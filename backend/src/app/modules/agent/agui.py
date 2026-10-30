from typing import Any, Literal

from ag_ui_langgraph import LangGraphAgent
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from app.modules.agent.graph import get_agent


class TurnAgent(LangGraphAgent):
    """AG-UI wrapper for one turn. LangGraph's "exit" durability writes a
    checkpoint only where the graph stops, which is the contract the
    pause-only saver was proven with (agent/checkpoints.py)."""

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
        return {**kwargs, "durability": "exit"}

    def _build_command_from_agui_resume(self, entries: list, **_: Any) -> Command:
        # LangGraph maps resume values by interrupt id, for one interrupt or
        # several; the adapter's default wraps several in its own sentinel.
        # Entries are validated server side and always "resolved".
        return Command(resume={entry.interrupt_id: entry.payload for entry in entries})


def turn_agent(tool_names: frozenset[str], saver: BaseCheckpointSaver) -> TurnAgent:
    """A fresh wrapper per turn: LangGraphAgent keeps per-run state on the
    instance, and the shared compiled graph must not have its saver swapped
    under a turn that is using it, so the turn gets a copy."""
    return TurnAgent(
        name="agent",
        graph=get_agent(tool_names).copy(update={"checkpointer": saver}),
        # RAW callback events are verbose; flip on for debugging.
        emit_raw_events=False,
        # Interrupts end the run as RUN_FINISHED with an interrupt outcome.
        enable_legacy_on_interrupt_event=False,
        emit_interrupt_outcome=True,
    )
