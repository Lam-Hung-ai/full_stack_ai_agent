from collections.abc import Mapping
from typing import Any, Literal

from ag_ui_langgraph import LangGraphAgent
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from app.modules.ai.agents import DEFAULT_AGENT, get_agent
from app.modules.ai.observability.tracing import tracing_config
from app.modules.ai.tools.context import TurnContext


class TurnAgent(LangGraphAgent):
    """AG-UI wrapper for one turn. LangGraph's "exit" durability writes a
    checkpoint only where the graph stops, which is the contract the
    pause-only saver was proven with (ai/memory/checkpoints.py)."""

    #: Handed to the graph as its runtime context (tools, middleware).
    turn_context: TurnContext | None = None

    def get_stream_kwargs(
        self,
        input: Any,
        subgraphs: bool = False,
        version: Literal["v1", "v2"] = "v2",
        config: RunnableConfig | None = None,
        context: dict[str, Any] | None = None,
        fork: Any | None = None,
    ) -> dict[str, Any]:
        kwargs = super().get_stream_kwargs(
            input, subgraphs, version, config, context, fork
        )
        # The adapter would pass the config's `configurable` as the context;
        # the agent's context schema is the turn's own.
        return {**kwargs, "durability": "exit", "context": self.turn_context}

    def _build_command_from_agui_resume(self, entries: list, **_: Any) -> Command:
        # LangGraph maps resume values by interrupt id, for one interrupt or
        # several; the adapter's default wraps several in its own sentinel.
        # Entries are validated server side and always "resolved".
        return Command(resume={entry.interrupt_id: entry.payload for entry in entries})


def turn_agent(
    tool_names: frozenset[str],
    saver: BaseCheckpointSaver,
    context: TurnContext,
    trace: Mapping[str, str] | None = None,
) -> TurnAgent:
    """A fresh wrapper per turn: LangGraphAgent keeps per-run state on the
    instance, and the shared compiled graph must not have its saver swapped
    under a turn that is using it, so the turn gets a copy. `trace` names
    the turn for Langfuse when tracing is on."""
    agent = TurnAgent(
        name=DEFAULT_AGENT.key,
        graph=get_agent(tool_names).copy(update={"checkpointer": saver}),
        config=tracing_config(trace or {}),
        # RAW callback events are verbose; flip on for debugging.
        emit_raw_events=False,
        # Interrupts end the run as RUN_FINISHED with an interrupt outcome.
        enable_legacy_on_interrupt_event=False,
        emit_interrupt_outcome=True,
    )
    agent.turn_context = context
    return agent
