import json
import logging
from typing import Literal

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool

from app.modules.ai.tools.context import TurnContext

logger = logging.getLogger(__name__)


@tool
async def create_file(
    name: str,
    format: Literal["csv", "md", "txt", "xlsx"],
    runtime: ToolRuntime[TurnContext],
    content: str | None = None,
    rows: list[list[str | int | float | None]] | None = None,
) -> str | ToolMessage:
    """Create a file the user can download, attached to your answer.

    Use it when the user asks for a document or spreadsheet to keep, e.g.
    "lập bảng Excel", "xuất CSV", "viết thành file Markdown".
    - name: what a person would call the file, in the user's language with
      its accents and spaces, saying what it holds, e.g. "Bảng chi phí tháng
      10-2026" (no underscores, no extension needed).
    - csv, xlsx: give `rows`, a list of rows; the first row holds the headers.
    - md, txt: give the whole text in `content`.
    In your answer name the file instead of repeating all of its content.
    """
    sink = runtime.context.file_sink if runtime.context else None
    if sink is None:
        return _failed(runtime, "Files cannot be created right now.")
    try:
        result = await sink(name, format, content, rows)
    except ValueError as error:
        return _failed(runtime, f"Could not create the file: {error}")
    except Exception:
        logger.warning("create_file failed", exc_info=True)
        return _failed(runtime, "Could not store the file right now. Try again later.")
    return json.dumps(result, ensure_ascii=False)


def _failed(runtime: ToolRuntime[TurnContext], text: str) -> ToolMessage:
    """A failed call: the error status reaches the model and, as AG-UI's
    `error`, the saved answer, so the UI can flag the step (a plain string
    would read as success)."""
    return ToolMessage(
        content=text,
        tool_call_id=runtime.tool_call_id or "",
        name="create_file",
        status="error",
    )
