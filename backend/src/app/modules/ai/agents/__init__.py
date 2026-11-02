"""Agent registry.

Each agent is an `AgentSpec` in its own module. Turns run `DEFAULT_AGENT`
until conversations choose an agent; a pause records the agent's version so
it resumes on the same graph.
"""

from functools import lru_cache

from app.modules.ai.agents.chat import CHAT
from app.modules.ai.agents.spec import AgentGraph, AgentSpec

AGENTS: dict[str, AgentSpec] = {spec.key: spec for spec in (CHAT,)}
DEFAULT_AGENT = CHAT


@lru_cache(maxsize=32)
def get_agent(tool_names: frozenset[str], key: str = DEFAULT_AGENT.key) -> AgentGraph:
    """One compiled graph per agent and set of allowed tools; members with the
    same grants share it. Unknown tool names are ignored. It has no
    checkpointer: each turn runs on a copy with its own saver
    (runtime.agui.turn_agent)."""
    return AGENTS[key].build(tool_names)
