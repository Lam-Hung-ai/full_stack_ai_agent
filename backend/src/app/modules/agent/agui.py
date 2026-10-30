from functools import lru_cache

from ag_ui_langgraph import LangGraphAgent

from app.modules.agent.graph import get_agent


@lru_cache(maxsize=16)
def get_agui_agent(tool_names: frozenset[str]) -> LangGraphAgent:
    """Wrap the compiled LangGraph agent for the AG-UI protocol.

    Call `.clone()` per turn (see runner.py) — LangGraphAgent keeps
    per-run state on the instance, so a shared instance would leak
    state across concurrent requests.
    """
    # emit_raw_events=False drops the verbose LangChain callback (RAW) events;
    # flip it on if you need them for debugging.
    return LangGraphAgent(
        name="agent", graph=get_agent(tool_names), emit_raw_events=False
    )
