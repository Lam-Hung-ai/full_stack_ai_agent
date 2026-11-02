from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langgraph.graph.state import CompiledStateGraph

#: A compiled agent graph, whatever its state and context schemas.
type AgentGraph = CompiledStateGraph[Any, Any, Any, Any]


@dataclass(frozen=True)
class AgentSpec:
    key: str
    #: Stored with every pause; a paused turn resumes only on the same graph
    #: (RR-07). Bump it when nodes, tools or state change incompatibly.
    version: str
    #: Compiles the graph offering these tools (already filtered to the
    #: member's grants); no checkpointer, each turn adds its own saver.
    build: Callable[[frozenset[str]], AgentGraph]
