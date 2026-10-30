"""Name a new chat from its first question (use case C01).

The chat gets the question's first line at once; a short model call then
suggests a better name in the background. It is stored only while the chat
still has that first-line name, so a rename by the user always wins (C07).
A failed call keeps the first-line name.
"""

import asyncio
import logging
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage

from app.database.session import SessionFactory
from app.modules.agent import graph
from app.modules.conversations.repository import ConversationRepository

logger = logging.getLogger(__name__)

TITLE_LENGTH = 60
#: Characters of the question the model sees; enough to tell the topic.
QUESTION_CHARS = 2_000
PROMPT = (
    "Bạn đặt tên cho cuộc trò chuyện. Không trả lời câu hỏi. Viết một tên "
    "ngắn (tối đa 8 từ) nói chủ đề của câu hỏi, cùng ngôn ngữ với câu hỏi. "
    "Chỉ trả về tên, không ngoặc kép, không dấu chấm cuối."
)

_pending: set[asyncio.Task[None]] = set()


def clip(text: str) -> str:
    """One line of at most TITLE_LENGTH characters."""
    line = " ".join(text.split())
    return line if len(line) <= TITLE_LENGTH else line[: TITLE_LENGTH - 1] + "…"


def clean(raw: str) -> str | None:
    """The model's answer as a title: first non-empty line, no quotes."""
    line = next((part for part in raw.splitlines() if part.strip()), "")
    line = line.strip().strip("\"'“”‘’`*#").strip().rstrip(".")
    return clip(line) or None


async def suggest(question: str) -> str | None:
    # Framed as data, so the model names the question instead of answering it.
    framed = (
        f"Câu hỏi của người dùng:\n<<<\n{question[:QUESTION_CHARS]}\n>>>\n\n"
        "Chỉ trả về tên cuộc trò chuyện."
    )
    reply = await graph.build_title_model().ainvoke(
        [SystemMessage(PROMPT), HumanMessage(framed)]
    )
    usage = getattr(reply, "usage_metadata", None) or {}
    logger.info(
        "Conversation title suggested",
        extra={
            "fields": {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
            }
        },
    )
    return clean(reply.text if hasattr(reply, "text") else str(reply.content))


def name_in_background(
    *,
    session_factory: SessionFactory,
    conversation_id: UUID,
    current: str,
    question: str,
) -> None:
    """Start naming the chat; `current` is the title it has now."""
    task = asyncio.create_task(
        _name(session_factory, conversation_id, current, question),
        name=f"conversation-title-{conversation_id}",
    )
    _pending.add(task)
    task.add_done_callback(_pending.discard)


async def drain() -> None:
    """Wait for naming in progress (tests, shutdown)."""
    await asyncio.gather(*_pending, return_exceptions=True)


async def _name(
    session_factory: SessionFactory, conversation_id: UUID, current: str, question: str
) -> None:
    try:
        title = await suggest(question)
    except Exception:
        logger.warning("Could not name conversation %s", conversation_id, exc_info=True)
        return
    if title is None or title == current:
        return
    async with session_factory() as session:
        await ConversationRepository(session).rename_if(
            conversation_id=conversation_id, expected=current, title=title
        )
        await session.commit()
