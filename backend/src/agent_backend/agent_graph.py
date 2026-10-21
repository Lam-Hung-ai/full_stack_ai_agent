from datetime import datetime, timezone
from functools import lru_cache

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter
from langgraph.checkpoint.memory import InMemorySaver

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_APP_NAME,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    OPENROUTER_REASONING_EFFORT,
    OPENROUTER_SITE_URL,
)

SYSTEM_PROMPT = (
    "You are a helpful assistant exposed through a FastAPI + LangGraph backend. "
    "Use the available tools when they help answer the question."
)


@tool
def get_current_time() -> str:
    """Return the current UTC date and time. Use this when asked what time or date it is."""
    return datetime.now(timezone.utc).isoformat()


TOOLS = [get_current_time]


@lru_cache(maxsize=1)
def get_agent():
    model = ChatOpenRouter(
        model=OPENROUTER_MODEL,
        api_key=OPENROUTER_API_KEY,
        openrouter_api_base=OPENROUTER_BASE_URL,
        app_url=OPENROUTER_SITE_URL or None,
        app_title=OPENROUTER_APP_NAME or None,
        reasoning={"effort": OPENROUTER_REASONING_EFFORT} if OPENROUTER_REASONING_EFFORT else None,
        streaming=True,
    )
    # AG-UI (thread_id-based runs, interrupts/resume) requires a checkpointer.
    # InMemorySaver is dev-only — swap for a persistent saver (Postgres/Redis) in production.
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
