"""Chat API helpers shared by the conversation and tool tests."""

import json
from typing import Any

from uuid_utils.compat import uuid7


async def new_conversation(client, user, headers):
    response = await client.post(
        f"/api/v1/workspaces/{user.personal_workspace_id}/conversations",
        json={},
        headers=headers,
    )
    return response.json()["id"]


def body(text, parent=None, message_id=None):
    return {
        "parent_message_id": parent,
        "message": {"id": str(message_id or uuid7()), "text": text},
    }


async def send(client, conversation_id, headers, payload) -> tuple[int, Any]:
    """POST a new question and read the whole SSE stream; return (status, events)."""
    return await stream_turn(
        client, f"/api/v1/conversations/{conversation_id}/messages", headers, payload
    )


async def stream_turn(client, url, headers, payload=None) -> tuple[int, Any]:
    """POST to a turn route and read the whole SSE stream."""
    events = []
    async with client.stream(
        "POST",
        url,
        json=payload,
        headers={**headers, "Accept": "text/event-stream"},
    ) as response:
        if response.status_code != 200:
            await response.aread()
            return response.status_code, response.json()
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:]))
    return 200, events


async def history(client, conversation_id, headers, from_message_id=None):
    params = {"from_message_id": from_message_id} if from_message_id else None
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        params=params,
        headers=headers,
    )
    return response.json()
