"""Open AG-UI spans of a turn, so a cut-off stream can still end validly.

A stopped turn ends between a START and its END (a model step, a text or
reasoning message, a tool call). Clients verify the protocol and reject a
RUN_FINISHED while anything is still open, so the runner closes what is open,
innermost first, before announcing the end.
"""

from collections.abc import Callable

from ag_ui.core import (
    BaseEvent,
    EventType,
    ReasoningEndEvent,
    ReasoningMessageEndEvent,
    StepFinishedEvent,
    TextMessageEndEvent,
    ToolCallEndEvent,
)

#: Start type -> (field holding the span id, END event for that id).
_OPENS: dict[EventType, tuple[str, Callable[[str], BaseEvent]]] = {
    EventType.STEP_STARTED: ("step_name", lambda i: StepFinishedEvent(step_name=i)),
    EventType.REASONING_START: (
        "message_id",
        lambda i: ReasoningEndEvent(message_id=i),
    ),
    EventType.REASONING_MESSAGE_START: (
        "message_id",
        lambda i: ReasoningMessageEndEvent(message_id=i),
    ),
    EventType.TEXT_MESSAGE_START: (
        "message_id",
        lambda i: TextMessageEndEvent(message_id=i),
    ),
    EventType.TOOL_CALL_START: (
        "tool_call_id",
        lambda i: ToolCallEndEvent(tool_call_id=i),
    ),
}
_CLOSES = {
    EventType.STEP_FINISHED: EventType.STEP_STARTED,
    EventType.REASONING_END: EventType.REASONING_START,
    EventType.REASONING_MESSAGE_END: EventType.REASONING_MESSAGE_START,
    EventType.TEXT_MESSAGE_END: EventType.TEXT_MESSAGE_START,
    EventType.TOOL_CALL_END: EventType.TOOL_CALL_START,
}


class OpenSpans:
    def __init__(self) -> None:
        #: (start type, id) in the order they opened.
        self._open: list[tuple[EventType, str]] = []

    def apply(self, event: BaseEvent) -> None:
        if event.type in _OPENS:
            field, _ = _OPENS[event.type]
            self._open.append((event.type, getattr(event, field)))
        elif event.type in _CLOSES:
            field, _ = _OPENS[_CLOSES[event.type]]
            span = (_CLOSES[event.type], getattr(event, field))
            if span in self._open:
                self._open.remove(span)

    def closing_events(self) -> list[BaseEvent]:
        """END events for everything still open, innermost first."""
        events: list[BaseEvent] = []
        for start, span_id in reversed(self._open):
            _, end = _OPENS[start]
            events.append(end(span_id))
        self._open.clear()
        return events
