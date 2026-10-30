"""Collect the AG-UI messages of one assistant turn from its event stream.

The stored bundle is what the user saw: messages in stream order, with the
final MESSAGES_SNAPSHOT version (minus the input history) where the agent sent
one, so a failed or stopped turn still keeps its partial text (database
decisions §6: content is the AG-UI Message[] of one logical row).
"""

from typing import Any

from ag_ui.core import (
    BaseEvent,
    MessagesSnapshotEvent,
    ReasoningMessageContentEvent,
    ReasoningMessageStartEvent,
    TextMessageContentEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)

#: Roles allowed inside an assistant row (chat_app.valid_agui_bundle).
ASSISTANT_BUNDLE_ROLES = frozenset({"assistant", "tool", "reasoning", "activity"})

type AguiMessage = dict[str, Any]


def dump_message(message: Any) -> AguiMessage:
    """Protocol JSON (camelCase), the shape the frontend SDK uses."""
    return message.model_dump(by_alias=True, exclude_none=True, mode="json")


class BundleBuilder:
    def __init__(self, input_ids: set[str]) -> None:
        self._input_ids = input_ids
        self._snapshot: list[AguiMessage] | None = None
        self._streamed: dict[str, AguiMessage] = {}
        self._tool_calls: dict[str, dict[str, Any]] = {}

    def apply(self, event: BaseEvent) -> None:
        if isinstance(event, MessagesSnapshotEvent):
            self._snapshot = [
                dump_message(message)
                for message in event.messages
                if message.id not in self._input_ids
            ]
        elif isinstance(event, TextMessageStartEvent):
            self._message(event.message_id, "assistant")
        elif isinstance(event, ReasoningMessageStartEvent):
            self._message(event.message_id, "reasoning")
        elif isinstance(event, TextMessageContentEvent):
            self._append(event.message_id, "assistant", event.delta)
        elif isinstance(event, ReasoningMessageContentEvent):
            self._append(event.message_id, "reasoning", event.delta)
        elif isinstance(event, ToolCallStartEvent):
            call = {
                "id": event.tool_call_id,
                "type": "function",
                "function": {"name": event.tool_call_name, "arguments": ""},
            }
            parent = self._message(
                event.parent_message_id or event.tool_call_id, "assistant"
            )
            parent.setdefault("toolCalls", []).append(call)
            self._tool_calls[event.tool_call_id] = call
        elif isinstance(event, ToolCallArgsEvent):
            if call := self._tool_calls.get(event.tool_call_id):
                call["function"]["arguments"] += event.delta
        elif isinstance(event, ToolCallResultEvent):
            self._streamed[event.message_id] = {
                "id": event.message_id,
                "role": "tool",
                "toolCallId": event.tool_call_id,
                "content": event.content,
            }

    def bundle(self) -> list[AguiMessage]:
        seen: set[str] = set()
        result = []
        for message in self._merged():
            # The database rejects foreign roles and duplicate ids in a row.
            if (
                message.get("role") in ASSISTANT_BUNDLE_ROLES
                and message["id"] not in seen
            ):
                seen.add(message["id"])
                result.append(message)
        return result

    def _merged(self) -> list[AguiMessage]:
        """Stream order, snapshot content. LangGraph's snapshot omits reasoning
        the provider returned outside content blocks (OpenRouter does), yet the
        user saw it stream; streamed reasoning without a snapshot twin stays."""
        if self._snapshot is None:
            return list(self._streamed.values())
        snapshot = {message["id"]: message for message in self._snapshot}
        # Tool results get a fresh id in the snapshot; their call id is shared.
        by_call = {
            message["toolCallId"]: message["id"]
            for message in self._snapshot
            if message.get("role") == "tool" and message.get("toolCallId")
        }
        merged: list[AguiMessage] = []
        for message in self._streamed.values():
            twin = message["id"]
            if twin not in snapshot and message["role"] == "tool":
                twin = by_call.get(message.get("toolCallId"), twin)
            if twin in snapshot:
                merged.append(snapshot.pop(twin))
            elif message["role"] == "reasoning":
                merged.append(message)
        merged.extend(snapshot.values())
        return merged

    def _message(self, message_id: str, role: str) -> AguiMessage:
        return self._streamed.setdefault(message_id, {"id": message_id, "role": role})

    def _append(self, message_id: str, role: str, delta: str) -> None:
        message = self._message(message_id, role)
        message["content"] = (message.get("content") or "") + delta
