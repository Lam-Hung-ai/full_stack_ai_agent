from functools import lru_cache

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_openrouter import ChatOpenRouter
from langgraph.checkpoint.memory import InMemorySaver

from app.config.settings import get_settings
from app.modules.agent.tools import TOOLS, ToolPermissionMiddleware

SYSTEM_PROMPT = (
    "You are a helpful assistant exposed through a FastAPI + LangGraph backend. "
    "Use the available tools when they help answer the question."
)


def build_model() -> BaseChatModel:
    """The chat model; tests replace this function with a scripted fake."""
    settings = get_settings()
    effort = settings.openrouter_reasoning_effort
    return ChatOpenRouter(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        openrouter_api_base=settings.openrouter_base_url,
        app_url=settings.openrouter_site_url,
        app_title=settings.openrouter_app_name,
        reasoning={"effort": effort} if effort else None,
        streaming=True,
    )


@lru_cache(maxsize=16)
def get_agent(tool_names: frozenset[str]):
    """One compiled graph per set of allowed tools; members with the same
    grants share it. Unknown names are ignored."""
    # AG-UI requires a checkpointer for thread-based runs. Each assistant turn
    # gets its own native thread, deleted when the turn ends; the Postgres
    # saver that keeps paused turns arrives in sprint S4.
    return create_agent(
        model=build_model(),
        tools=[TOOLS[name] for name in sorted(tool_names & TOOLS.keys())],
        system_prompt=SYSTEM_PROMPT,
        middleware=[ToolPermissionMiddleware()],
        checkpointer=InMemorySaver(),
    )
