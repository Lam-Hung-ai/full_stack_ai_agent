from ag_ui.core import (
    EventType,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)

from app.modules.agent.lifecycle import OpenSpans


def test_closes_what_is_still_open_innermost_first():
    spans = OpenSpans()
    for event in (
        StepStartedEvent(step_name="model"),
        TextMessageStartEvent(message_id="m1", role="assistant"),
        TextMessageEndEvent(message_id="m1"),
        ToolCallStartEvent(tool_call_id="c1", tool_call_name="clock"),
        ToolCallEndEvent(tool_call_id="c1"),
        StepFinishedEvent(step_name="model"),
        StepStartedEvent(step_name="model"),
        TextMessageStartEvent(message_id="m2", role="assistant"),
    ):
        spans.apply(event)

    closing = spans.closing_events()
    assert [e.type for e in closing] == [
        EventType.TEXT_MESSAGE_END,
        EventType.STEP_FINISHED,
    ]
    assert closing[0] == TextMessageEndEvent(message_id="m2")
    assert spans.closing_events() == []
