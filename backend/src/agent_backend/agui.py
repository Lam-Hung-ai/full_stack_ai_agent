from functools import lru_cache

from ag_ui_langgraph import LangGraphAgent

from .agent_graph import get_agent


@lru_cache(maxsize=1)
def get_agui_agent() -> LangGraphAgent:
    """Wrap the compiled LangGraph agent for the AG-UI protocol.

    Call `.clone()` per request (see main.py) — LangGraphAgent keeps
    per-run state on the instance, so a shared instance would leak
    state across concurrent requests.
    """
    # emit_raw_events=False drops the verbose LangChain callback (RAW) events;
    # flip it on if you need them for debugging.
    return LangGraphAgent(name="agent", graph=get_agent(), emit_raw_events=False)
