from functools import lru_cache

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_openrouter import ChatOpenRouter

from app.config.settings import get_settings
from app.modules.agent.tools import INTERACTION_TOOLS, TOOLS, ToolPermissionMiddleware

SYSTEM_PROMPT = (
    "You are a helpful assistant exposed through a FastAPI + LangGraph backend. "
    "Use the available tools when they help answer the question. When the "
    "request is ambiguous and a wrong guess would waste the user's time, ask "
    "with the ask_user tool instead of guessing."
)

#: Stored with every pause; a paused turn resumes only on the same graph
#: (RR-07). Bump it when nodes, tools or state change incompatibly.
GRAPH_VERSION = "chat-agent-v1"


def build_model() -> BaseChatModel:
    """The chat model; tests replace this function with a scripted fake."""
    settings = get_settings()
    if settings.agent_fake_model:
        from app.modules.agent.fake_model import LoadTestModel

        return LoadTestModel()
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
    grants share it. Unknown names are ignored. It has no checkpointer: each
    turn runs on a copy with its own saver (agui.turn_agent)."""
    tools = [TOOLS[name] for name in sorted(tool_names & TOOLS.keys())]
    return create_agent(
        model=build_model(),
        tools=[*tools, *INTERACTION_TOOLS.values()],
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            ToolPermissionMiddleware(frozenset(get_settings().tools_requiring_approval))
        ],
    )
