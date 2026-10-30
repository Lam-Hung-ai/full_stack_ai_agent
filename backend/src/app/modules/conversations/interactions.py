"""What a paused turn waits for, and how answers are recorded (phase 4 §4, §5).

`messages.metadata.pending_action` holds the server-side state: action id,
graph version, the stored checkpoint pointer and the interrupts. The content
holds one AG-UI activity `user_interaction` per interrupt, which is what the
user sees: the question or the tool to approve, then the answer and who gave
it. Activities are display only; the model gets the answer as the result of
the `ask_user` or tool call it made, never from the activity.
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from ag_ui.core import ActivitySnapshotEvent, BaseEvent, ResumeEntry
from langgraph.types import Interrupt
from uuid_utils.compat import uuid7

from app.common.exceptions.handlers import fail
from app.modules.agent.bundle import AguiMessage

ACTIVITY_TYPE = "user_interaction"
KINDS = frozenset({"user_question", "tool_approval"})
MAX_ANSWER_LENGTH = 4_000


def new_pending_action(
    *, checkpoint: dict[str, Any], interrupts: Sequence[Interrupt], graph_version: str
) -> dict[str, Any]:
    return {
        "action_id": str(uuid7()),
        "state": "waiting",
        "graph_version": graph_version,
        "expires_at": None,
        "checkpoint": checkpoint,
        "interrupts": [
            {"interrupt_id": item.id, "payload": item.value} for item in interrupts
        ],
    }


def activity_id(action_id: str, index: int) -> str:
    return f"interaction:{action_id}:{index}"


def waiting_activities(pending: dict[str, Any]) -> list[AguiMessage]:
    activities = []
    for index, item in enumerate(pending["interrupts"]):
        payload = item["payload"] if isinstance(item["payload"], dict) else {}
        content = {
            "action_id": pending["action_id"],
            "interrupt_id": item["interrupt_id"],
            "kind": payload.get("kind", "unknown"),
            "status": "waiting",
        }
        for field in ("question", "tool_name", "tool_call_id", "arguments"):
            if field in payload:
                content[field] = payload[field]
        activities.append(
            {
                "id": activity_id(pending["action_id"], index),
                "role": "activity",
                "activityType": ACTIVITY_TYPE,
                "content": content,
            }
        )
    return activities


def activity_events(activities: Sequence[AguiMessage]) -> list[BaseEvent]:
    return [
        ActivitySnapshotEvent(
            message_id=activity["id"],
            activity_type=ACTIVITY_TYPE,
            content=activity["content"],
            replace=True,
        )
        for activity in activities
    ]


def validate_answers(
    pending: dict[str, Any], entries: Sequence[ResumeEntry]
) -> dict[str, Any]:
    """Map each waiting interrupt to the value the graph resumes with, or fail
    before anything is claimed (the turn keeps waiting)."""
    waiting = {item["interrupt_id"]: item["payload"] for item in pending["interrupts"]}
    given = {entry.interrupt_id: entry for entry in entries}
    if len(given) != len(entries) or not given.keys() <= waiting.keys():
        fail(409, "stale_interrupt")
    if given.keys() != waiting.keys():
        fail(422, "resume_incomplete")
    values: dict[str, Any] = {}
    for interrupt_id, entry in given.items():
        kind = (waiting[interrupt_id] or {}).get("kind")
        payload = entry.payload if isinstance(entry.payload, dict) else {}
        # Stopping the whole turn is POST …/stop (API §5); a declined tool is
        # a resolved approval with approved=false.
        if entry.status != "resolved":
            fail(422, "invalid_resume", details={"interrupt_id": interrupt_id})
        if kind == "user_question":
            answer = payload.get("answer")
            if not isinstance(answer, str) or not answer.strip():
                fail(422, "empty_answer", details={"interrupt_id": interrupt_id})
            if len(answer) > MAX_ANSWER_LENGTH:
                fail(422, "answer_too_long", details={"interrupt_id": interrupt_id})
            values[interrupt_id] = answer.strip()
        elif kind == "tool_approval":
            if not isinstance(payload.get("approved"), bool):
                fail(422, "invalid_approval", details={"interrupt_id": interrupt_id})
            values[interrupt_id] = {"approved": payload["approved"]}
        else:
            fail(409, "unsupported_interrupt", details={"interrupt_id": interrupt_id})
    return values


def approved_tools(pending: dict[str, Any], values: dict[str, Any]) -> set[str]:
    """Tools the answers approve: their grant is checked before claiming (T07)."""
    return {
        item["payload"]["tool_name"]
        for item in pending["interrupts"]
        if item["payload"].get("kind") == "tool_approval"
        and values[item["interrupt_id"]] == {"approved": True}
    }


def resolve_activities(
    content: Sequence[AguiMessage],
    pending: dict[str, Any],
    *,
    status: str,
    values: dict[str, Any] | None = None,
    actor_id: UUID | None = None,
) -> list[AguiMessage]:
    """The content with this action's activities marked answered/cancelled."""
    ids = {
        activity_id(pending["action_id"], index): item["interrupt_id"]
        for index, item in enumerate(pending["interrupts"])
    }
    result = []
    for message in content:
        if message.get("id") in ids:
            update: dict[str, Any] = {"status": status}
            if values is not None:
                update["response"] = values[ids[message["id"]]]
                update["actor_id"] = str(actor_id)
            message = {**message, "content": {**message["content"], **update}}
        result.append(message)
    return result


def resolved_metadata(
    metadata: dict[str, Any],
    pending: dict[str, Any],
    *,
    status: str,
    values: dict[str, Any] | None = None,
    actor_id: UUID | None = None,
) -> dict[str, Any]:
    """Record the decision in `actions`; `pending_action` stays while resuming
    (a crash then leaves the pointer to inspect) and goes when the turn ends."""
    entry: dict[str, Any] = {"action_id": pending["action_id"], "status": status}
    if values is not None:
        entry.update(responses=values, actor_id=str(actor_id))
    result = {**metadata, "actions": [*metadata.get("actions", []), entry]}
    if status == "answered":
        result["pending_action"] = {**pending, "state": "resuming"}
    else:
        result.pop("pending_action", None)
    return result


def resume_entries(values: dict[str, Any]) -> list[ResumeEntry]:
    return [
        ResumeEntry(interrupt_id=interrupt_id, status="resolved", payload=value)
        for interrupt_id, value in values.items()
    ]
