"""Model context rebuilt from the stored branch."""

from app.modules.conversations.context import branch_messages


def row(role, status, content):
    return {"role": role, "status": status, "content": content}


def test_flattens_rows_and_hides_activities():
    rows = [
        row("user", "completed", [{"id": "u", "role": "user", "content": "hỏi"}]),
        row(
            "assistant",
            "completed",
            [
                {"id": "r", "role": "reasoning", "content": "nghĩ"},
                {"id": "x", "role": "activity", "activityType": "progress"},
                {"id": "a", "role": "assistant", "content": "đáp"},
            ],
        ),
    ]
    assert [m["id"] for m in branch_messages(rows)] == ["u", "r", "a"]


def test_unfinished_turn_drops_calls_without_results():
    call = {"id": "c1", "type": "function", "function": {"name": "f", "arguments": ""}}
    done = {"id": "c2", "type": "function", "function": {"name": "g", "arguments": ""}}
    rows = [
        row(
            "assistant",
            "failed",
            [
                {"id": "a1", "role": "assistant", "toolCalls": [call]},
                {
                    "id": "a2",
                    "role": "assistant",
                    "content": "dở",
                    "toolCalls": [call, done],
                },
                {"id": "t2", "role": "tool", "toolCallId": "c2", "content": "kết quả"},
            ],
        )
    ]
    messages = branch_messages(rows)
    assert [m["id"] for m in messages] == ["a2", "t2"]
    assert messages[0]["toolCalls"] == [done]
