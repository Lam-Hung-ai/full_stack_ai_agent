"""What a turn hands its tools (LangGraph runtime context).

The runner builds one `TurnContext` per turn and the agent receives it as
`context` (agent `context_schema`); tools read it through `ToolRuntime` and
middleware through `request.runtime`, so nothing is passed through globals.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

type ToolGuard = Callable[[str], Awaitable[bool]]
#: Stores a file for the turn's assistant: (name, format, content, rows) ->
#: what the tool returns. Raises ValueError for a request it refuses.
type FileSink = Callable[
    [str, str, str | None, list[list[Any]] | None], Awaitable[dict[str, Any]]
]


@dataclass(frozen=True)
class TurnContext:
    #: Whether the member may still use a tool, checked before every call.
    tool_guard: ToolGuard
    #: Absent when object storage is not configured.
    file_sink: FileSink | None = None
