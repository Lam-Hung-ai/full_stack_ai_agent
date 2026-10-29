from datetime import datetime, timezone
from functools import lru_cache

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter
from langgraph.checkpoint.memory import InMemorySaver

from app.config.settings import get_settings

SYSTEM_PROMPT = (
    "You are a helpful assistant exposed through a FastAPI + LangGraph backend. "
    "Use the available tools when they help answer the question."
)


@tool
def get_current_time() -> str:
    """Return the current UTC date and time.

    Use this when asked what time or date it is.
    """
    return datetime.now(timezone.utc).isoformat()


TOOLS = [get_current_time]


@lru_cache(maxsize=1)
def get_agent():
    settings = get_settings()
    effort = settings.openrouter_reasoning_effort
    model = ChatOpenRouter(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        openrouter_api_base=settings.openrouter_base_url,
        app_url=settings.openrouter_site_url,
        app_title=settings.openrouter_app_name,
        reasoning={"effort": effort} if effort else None,
        streaming=True,
    )
    # AG-UI (thread_id-based runs, interrupts/resume) requires a checkpointer.
    # InMemorySaver is dev-only; the conversation runner moves to the Postgres
    # saver (sprint S4).
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
