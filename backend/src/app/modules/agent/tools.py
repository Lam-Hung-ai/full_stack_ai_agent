"""Tool registry and its permission gate (database decisions §4, use case T07).

Each tool is permission `tool.<name>`. A turn's agent is built with the tools
the member may use when the turn starts, so the model never sees the others;
every call is checked again right before it runs, because a grant can be
revoked while a turn is still going.
"""

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, tool
from langgraph.types import Command

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


class ToolPermissionMiddleware(AgentMiddleware):
    """Refuses a tool call unless the turn's guard allows it now. Without a
    guard nothing runs: a turn always sets one, so its absence is a bug."""

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        call = request.tool_call
        guard = current_tool_guard.get()
        if guard is None or not await guard(call["name"]):
            return ToolMessage(
                content="This tool is not available to you.",
                tool_call_id=call["id"],
                name=call["name"],
                status="error",
            )
        return await handler(request)
