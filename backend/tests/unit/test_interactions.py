from typing import Literal
from uuid import UUID

import pytest
from ag_ui.core import ResumeEntry

from app.common.exceptions.handlers import DomainError
from app.modules.conversations import interactions

PENDING = {
    "action_id": "a1",
    "interrupts": [
        {"interrupt_id": "i1", "payload": {"kind": "user_question", "question": "?"}},
        {
            "interrupt_id": "i2",
            "payload": {"kind": "tool_approval", "tool_name": "clock"},
        },
    ],
}


def entry(
    interrupt_id: str,
    payload: dict,
    status: Literal["resolved", "cancelled"] = "resolved",
) -> ResumeEntry:
    return ResumeEntry(interrupt_id=interrupt_id, status=status, payload=payload)


def code(entries):
    with pytest.raises(DomainError) as caught:
        interactions.validate_answers(PENDING, entries)
    return caught.value.code


def test_every_waiting_interrupt_needs_a_valid_answer():
    values = interactions.validate_answers(
        PENDING, [entry("i1", {"answer": " CSV "}), entry("i2", {"approved": True})]
    )
    assert values == {"i1": "CSV", "i2": {"approved": True}}
    assert interactions.approved_tools(PENDING, values) == {"clock"}

    assert code([entry("i1", {"answer": "CSV"})]) == "resume_incomplete"
    assert code([entry("i1", {"answer": "x"}), entry("i9", {})]) == "stale_interrupt"
    assert code([entry("i1", {"answer": "x"}), entry("i2", {"approved": "yes"})]) == (
        "invalid_approval"
    )
    assert code([entry("i1", {}, "cancelled"), entry("i2", {"approved": True})]) == (
        "invalid_resume"
    )


def test_activities_follow_the_action():
    activities = interactions.waiting_activities(PENDING)
    assert [a["content"]["status"] for a in activities] == ["waiting", "waiting"]
    assert activities[1]["content"]["tool_name"] == "clock"
    answered = interactions.resolve_activities(
        activities,
        PENDING,
        status="answered",
        values={"i1": "CSV", "i2": {"approved": False}},
        actor_id=UUID(int=1),
    )
    assert answered[0]["content"]["actor_id"] == str(UUID(int=1))
    assert [a["content"]["response"] for a in answered] == [
        "CSV",
        {"approved": False},
    ]
    metadata = interactions.resolved_metadata(
        {"pending_action": PENDING}, PENDING, status="cancelled"
    )
    assert "pending_action" not in metadata
    assert metadata["actions"] == [{"action_id": "a1", "status": "cancelled"}]
