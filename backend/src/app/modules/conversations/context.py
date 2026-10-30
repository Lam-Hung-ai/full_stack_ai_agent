"""Model context for a new turn, rebuilt from the stored branch (API §1).

The browser never sends history: the backend reads the branch it authorized
and flattens each row's AG-UI bundle into one message list.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import RowMapping

#: Shown to the user but not model input: activities become context in S4
#: (an answered question maps to one HumanMessage).
_HIDDEN_FROM_MODEL = frozenset({"activity"})


def branch_messages(
    rows: Sequence[RowMapping | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for row in rows:
        bundle = [m for m in row["content"] if m.get("role") not in _HIDDEN_FROM_MODEL]
        if row["role"] == "assistant" and row["status"] != "completed":
            bundle = _without_unanswered_tool_calls(bundle)
        messages.extend(bundle)
    return messages


def _without_unanswered_tool_calls(
    bundle: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """A failed or stopped turn may end between a tool call and its result;
    providers reject a call with no result, so such calls are dropped."""
    answered = {m.get("toolCallId") for m in bundle if m.get("role") == "tool"}
    cleaned = []
    for message in bundle:
        calls = message.get("toolCalls")
        if calls:
            kept = [call for call in calls if call.get("id") in answered]
            message = {**message, "toolCalls": kept} if kept else _drop_calls(message)
            if message.get("role") == "assistant" and not (
                message.get("content") or message.get("toolCalls")
            ):
                continue
        cleaned.append(message)
    return cleaned


def _drop_calls(message: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in message.items() if key != "toolCalls"}
