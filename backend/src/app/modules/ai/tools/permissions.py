"""The permission gate in front of every tool call (use case T07)."""

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import ToolCall, ToolMessage
from langgraph.types import Command, interrupt

from app.modules.ai.tools import INTERACTION_TOOLS
from app.modules.ai.tools.context import TurnContext

DENIED = "This tool is not available to you."
DECLINED = "The user declined to run this tool."


def _refuse(call: ToolCall, text: str) -> ToolMessage:
    return ToolMessage(
        content=text, tool_call_id=call["id"], name=call["name"], status="error"
    )


class ToolPermissionMiddleware(AgentMiddleware):
    """Refuses a tool call unless the turn's guard allows it now, and asks the
    user first for tools in `needs_approval`. Without a guard nothing runs: a
    turn always sets one, so its absence is a bug."""

    def __init__(self, needs_approval: frozenset[str] = frozenset()) -> None:
        super().__init__()
        self.needs_approval = needs_approval

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        call = request.tool_call
        if call["name"] in INTERACTION_TOOLS:
            return await handler(request)
        context = request.runtime.context
        # On resume this node runs again from here, so the grant is checked
        # once more after the approval too.
        if not isinstance(context, TurnContext) or not await context.tool_guard(
            call["name"]
        ):
            return _refuse(call, DENIED)
        if call["name"] in self.needs_approval:
            decision = interrupt(
                {
                    "kind": "tool_approval",
                    "tool_name": call["name"],
                    "tool_call_id": call["id"],
                    "arguments": call["args"],
                }
            )
            if not (isinstance(decision, dict) and decision.get("approved") is True):
                return _refuse(call, DECLINED)
        return await handler(request)
