from uuid import uuid4

import fakeredis
from ag_ui.core import TextMessageContentEvent

from app.modules.agent.live import LiveStore, LiveView


async def test_a_trimmed_stream_is_not_continued_after_the_view():
    live = LiveStore(fakeredis.FakeAsyncRedis())
    assistant_id = uuid4()
    ids = [
        await live.append(
            assistant_id, n, TextMessageContentEvent(message_id="m", delta=str(n))
        )
        for n in range(1, 6)
    ]
    await live.save_view(assistant_id, LiveView([], ids[1], 2))
    view = await live.view(assistant_id)
    assert view is not None and view == LiveView([], ids[1], 2)
    assert await live.continues(assistant_id, view)

    # Capping dropped events 1-3; a view covering only 2 would miss event 3.
    await live.redis.xtrim(
        f"chat:{{{assistant_id}}}:events", maxlen=2, approximate=False
    )
    assert not await live.continues(assistant_id, LiveView([], ids[1], 2))
    assert await live.continues(assistant_id, LiveView([], ids[2], 3))

    after = await live.read(assistant_id, ids[2], block_ms=10)
    assert [event for _, event in after] == [
        TextMessageContentEvent(message_id="m", delta="4"),
        TextMessageContentEvent(message_id="m", delta="5"),
    ]
