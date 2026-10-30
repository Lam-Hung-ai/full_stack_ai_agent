"""Tool registry and its permission gate (database decisions §4, use case T07).

Each tool is permission `tool.<name>`. A turn's agent is built with the tools
the member may use when the turn starts, so the model never sees the others;
every call is checked again right before it runs, because a grant can be
revoked while a turn is still going (or while it waits for approval).

Two things pause a turn (database phase 4): `ask_user`, always offered, and a
tool configured to need approval. Both call `interrupt()` before anything with
an effect, because LangGraph reruns the interrupted node from its start.
"""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import ToolCall, ToolMessage
from langchain_core.tools import BaseTool, tool
from langgraph.types import Command, interrupt

#: Permission resource of every tool; the action is the tool name.
TOOL_RESOURCE = "tool"

type ToolGuard = Callable[[str], Awaitable[bool]]

#: Set by the runner inside a turn's task; tool calls inherit it.
current_tool_guard: ContextVar[ToolGuard | None] = ContextVar(
    "current_tool_guard", default=None
)


@tool
def get_current_time() -> str:
    """Return the current UTC date and time.

    Use this when asked what time or date it is.
    """
    return datetime.now(timezone.utc).isoformat()


TOOLS: dict[str, BaseTool] = {item.name: item for item in (get_current_time,)}


@tool
def ask_user(question: str) -> str:
    """Ask the user a question and wait for the answer.

    Use only when you cannot continue without information that only the user
    has, such as a choice between options. Ask one short, clear question.
    """
    return interrupt({"kind": "user_question", "question": question})


#: Offered to every turn, outside the permission catalog: they act on nothing.
INTERACTION_TOOLS: dict[str, BaseTool] = {ask_user.name: ask_user}

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
        guard = current_tool_guard.get()
        # On resume this node runs again from here, so the grant is checked
        # once more after the approval too.
        if guard is None or not await guard(call["name"]):
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
