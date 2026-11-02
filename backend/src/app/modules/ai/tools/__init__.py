"""Tool registry (database decisions §4, use case T07).

Each tool in `TOOLS` is permission `tool.<name>` (authorization catalog). A
turn's agent is built with the tools the member may use when the turn starts,
so the model never sees the others; `permissions.ToolPermissionMiddleware`
checks every call again right before it runs.

Two things pause a turn (database phase 4): `ask_user`, always offered, and a
tool configured to need approval. Both call `interrupt()` before anything with
an effect, because LangGraph reruns the interrupted node from its start.

To add a tool: write it in its own module, list it here and give it a
permission in `authorization/catalog.py`.
"""

from langchain_core.tools import BaseTool

from app.modules.ai.tools.clock import get_current_time
from app.modules.ai.tools.files import create_file
from app.modules.ai.tools.interaction import ask_user

#: Permission resource of every tool; the action is the tool name.
TOOL_RESOURCE = "tool"

TOOLS: dict[str, BaseTool] = {
    item.name: item for item in (get_current_time, create_file)
}

#: Offered to every turn, outside the permission catalog: they act on nothing.
INTERACTION_TOOLS: dict[str, BaseTool] = {ask_user.name: ask_user}
