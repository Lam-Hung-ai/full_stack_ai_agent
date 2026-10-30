"""What an assistant row stores: what the user saw, in order (decisions §6)."""

from ag_ui.core import (
    AssistantMessage,
    FunctionCall,
    MessagesSnapshotEvent,
    ReasoningMessageContentEvent,
    ReasoningMessageStartEvent,
    TextMessageContentEvent,
    TextMessageStartEvent,
    ToolCall,
    ToolCallArgsEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
    ToolMessage,
    UserMessage,
)

from app.modules.agent.bundle import BundleBuilder


def stream_tool_turn(builder: BundleBuilder) -> None:
    for event in [
        ReasoningMessageStartEvent(message_id="r1", role="reasoning"),
        ReasoningMessageContentEvent(message_id="r1", delta="cần giờ"),
        ToolCallStartEvent(
            tool_call_id="c1", tool_call_name="clock", parent_message_id="a1"
        ),
        ToolCallArgsEvent(tool_call_id="c1", delta="{}"),
        ToolCallResultEvent(message_id="t-stream", tool_call_id="c1", content="10:00"),
        TextMessageStartEvent(message_id="a2", role="assistant"),
        TextMessageContentEvent(message_id="a2", delta="10 giờ"),
    ]:
        builder.apply(event)


def test_streamed_messages_without_snapshot():
    builder = BundleBuilder(set())
    stream_tool_turn(builder)
    assert builder.bundle() == [
        {"id": "r1", "role": "reasoning", "content": "cần giờ"},
        {
            "id": "a1",
            "role": "assistant",
            "toolCalls": [
                {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "clock", "arguments": "{}"},
                }
            ],
        },
        {"id": "t-stream", "role": "tool", "toolCallId": "c1", "content": "10:00"},
        {"id": "a2", "role": "assistant", "content": "10 giờ"},
    ]


def test_snapshot_content_in_stream_order_keeps_reasoning():
    builder = BundleBuilder({"u1"})
    stream_tool_turn(builder)
    builder.apply(
        MessagesSnapshotEvent(
            messages=[
                UserMessage(id="u1", role="user", content="mấy giờ"),
                AssistantMessage(
                    id="a1",
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            id="c1", function=FunctionCall(name="clock", arguments="{}")
                        )
                    ],
                ),
                ToolMessage(
                    id="t-snap", role="tool", tool_call_id="c1", content="10:00"
                ),
                AssistantMessage(id="a2", role="assistant", content="10 giờ."),
            ]
        )
    )
    bundle = builder.bundle()
    assert [(m["role"], m["id"]) for m in bundle] == [
        ("reasoning", "r1"),
        ("assistant", "a1"),
        ("tool", "t-snap"),
        ("assistant", "a2"),
    ]
    assert bundle[-1]["content"] == "10 giờ."


def test_bundle_drops_input_history_and_foreign_roles():
    builder = BundleBuilder({"old"})
    builder.apply(
        MessagesSnapshotEvent(
            messages=[
                UserMessage(id="old", role="user", content="cũ"),
                UserMessage(id="echo", role="user", content="lạ"),
                AssistantMessage(id="a", role="assistant", content="ok"),
            ]
        )
    )
    assert [m["id"] for m in builder.bundle()] == ["a"]
