"""In-process runner for assistant turns (QD-15).

A turn runs in an asyncio task owned by the application, not by the HTTP
request: closing the browser detaches a subscriber and the turn still finishes
and is saved. Events are buffered per turn so a subscriber that arrives after
the start still sees them in order. Sprint S5 moves the live buffer to Redis
for reconnects across processes.

Database decisions §6: content is written once the turn ends. The terminal
RUN_FINISHED / RUN_ERROR is published only after that write commits, so a
client that saw the end can reload and find the same result.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Literal
from uuid import UUID

from ag_ui.core import (
    BaseEvent,
    CustomEvent,
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedCancelledOutcome,
    RunFinishedEvent,
    RunStartedEvent,
)
from ag_ui_langgraph import LangGraphAgent

from app.modules.agent.bundle import AguiMessage, BundleBuilder
from app.modules.agent.lifecycle import OpenSpans
from app.modules.agent.tools import ToolGuard, current_tool_guard

logger = logging.getLogger(__name__)

TurnStatus = Literal["completed", "failed", "cancelled"]
#: Name of the CUSTOM event that ties the protocol stream to SQL rows.
ASSISTANT_EVENT = "chat.assistant"

type Finalizer = Callable[[TurnStatus, list[AguiMessage]], Awaitable[None]]


class RunStream:
    """Ordered events of one turn, readable by any number of subscribers."""

    def __init__(self) -> None:
        self._events: list[BaseEvent] = []
        self._closed = False
        self._changed = asyncio.Condition()

    async def publish(self, event: BaseEvent) -> None:
        async with self._changed:
            self._events.append(event)
            self._changed.notify_all()

    async def close(self) -> None:
        async with self._changed:
            self._closed = True
            self._changed.notify_all()

    async def subscribe(self) -> AsyncIterator[BaseEvent]:
        position = 0
        while True:
            async with self._changed:
                await self._changed.wait_for(
                    lambda: position < len(self._events) or self._closed
                )
                batch = self._events[position:]
                position = len(self._events)
                closed = self._closed
            for event in batch:
                yield event
            if closed and position == len(self._events):
                return


class Runner:
    def __init__(
        self,
        *,
        agent_factory: Callable[[frozenset[str]], LangGraphAgent],
        max_concurrent: int,
    ) -> None:
        self._agent_factory = agent_factory
        self._slots = asyncio.Semaphore(max_concurrent)
        self._streams: dict[UUID, RunStream] = {}
        self._tasks: dict[UUID, asyncio.Task[None]] = {}
        #: Turns saving their outcome; cancelling now would lose the end events.
        self._finishing: set[UUID] = set()

    def start(
        self,
        *,
        assistant_id: UUID,
        run_input: RunAgentInput,
        announce: dict[str, Any],
        tools: frozenset[str],
        tool_guard: ToolGuard,
        on_running: Callable[[], Awaitable[None]],
        finalize: Finalizer,
    ) -> RunStream:
        stream = RunStream()
        self._streams[assistant_id] = stream
        self._tasks[assistant_id] = asyncio.create_task(
            self._execute(
                assistant_id=assistant_id,
                stream=stream,
                run_input=run_input,
                announce=announce,
                tools=tools,
                tool_guard=tool_guard,
                on_running=on_running,
                finalize=finalize,
            ),
            name=f"assistant-turn-{assistant_id}",
        )
        return stream

    def stream(self, assistant_id: UUID) -> RunStream | None:
        return self._streams.get(assistant_id)

    async def stop(self, assistant_id: UUID, *, timeout: float) -> bool:
        """Cancel a turn of this process and wait up to `timeout` for it to be
        saved as cancelled. False when no such turn runs here."""
        task = self._tasks.get(assistant_id)
        if task is None:
            return False
        self._cancel(assistant_id, task)
        await asyncio.wait({task}, timeout=timeout)
        return True

    async def shutdown(self, timeout: float) -> None:
        """Let running turns finish within `timeout`, then cancel the rest
        (they are saved as cancelled with their partial content)."""
        tasks = dict(self._tasks)
        if not tasks:
            return
        await asyncio.wait(tasks.values(), timeout=timeout)
        for assistant_id, task in tasks.items():
            self._cancel(assistant_id, task)
        await asyncio.gather(*tasks.values(), return_exceptions=True)

    def _cancel(self, assistant_id: UUID, task: asyncio.Task[None]) -> None:
        if assistant_id not in self._finishing and not task.done():
            task.cancel()

    async def _execute(
        self,
        *,
        assistant_id: UUID,
        stream: RunStream,
        run_input: RunAgentInput,
        announce: dict[str, Any],
        tools: frozenset[str],
        tool_guard: ToolGuard,
        on_running: Callable[[], Awaitable[None]],
        finalize: Finalizer,
    ) -> None:
        public_thread = run_input.thread_id
        builder = BundleBuilder({message.id for message in run_input.messages})
        spans = OpenSpans()
        # Tasks the graph spawns copy this context, so tool calls see the guard.
        current_tool_guard.set(tool_guard)
        agent: LangGraphAgent | None = None
        finished: BaseEvent | None = None
        started = False
        status: TurnStatus = "failed"
        try:
            agent = self._agent_factory(tools).clone()
            async with self._slots:
                await on_running()
                # ID decisions §1: the native thread is the assistant row; the
                # protocol stream keeps the conversation as its thread.
                native = run_input.model_copy(update={"thread_id": str(assistant_id)})
                async for event in agent.run(native):
                    if getattr(event, "thread_id", None) is not None:
                        event = event.model_copy(update={"thread_id": public_thread})
                    builder.apply(event)
                    spans.apply(event)
                    if event.type == EventType.RUN_FINISHED:
                        finished = event
                        continue
                    if event.type == EventType.RUN_ERROR:
                        raise RuntimeError(getattr(event, "message", "run error"))
                    await stream.publish(event)
                    if event.type == EventType.RUN_STARTED:
                        started = True
                        await stream.publish(self._status_event(announce, "running"))
            status = "completed"
        except asyncio.CancelledError:
            status = "cancelled"
            raise
        except Exception:
            logger.exception("Assistant turn %s failed", assistant_id)
        finally:
            self._finishing.add(assistant_id)
            try:
                await self._finish(
                    stream=stream,
                    status=status,
                    content=builder.bundle(),
                    finalize=finalize,
                    announce=announce,
                    started=started,
                    finished=finished,
                    run_input=run_input,
                    spans=spans,
                )
            finally:
                if agent is not None:
                    await self._forget_native_thread(agent, assistant_id)
                self._streams.pop(assistant_id, None)
                self._tasks.pop(assistant_id, None)
                self._finishing.discard(assistant_id)

    async def _finish(
        self,
        *,
        stream: RunStream,
        status: TurnStatus,
        content: list[AguiMessage],
        finalize: Finalizer,
        announce: dict[str, Any],
        started: bool,
        finished: BaseEvent | None,
        run_input: RunAgentInput,
        spans: OpenSpans,
    ) -> None:
        try:
            # Shielded: a shutdown cancellation must not abort the final write.
            await asyncio.shield(finalize(status, content))
        except Exception:
            logger.exception("Could not save assistant turn %s", announce)
            await stream.publish(
                RunErrorEvent(
                    message="The answer could not be saved.", code="persist_failed"
                )
            )
            await stream.close()
            return
        if not started:
            # Stopped while waiting for a slot: still give subscribers a
            # complete lifecycle so the client can show the outcome.
            await stream.publish(
                RunStartedEvent(thread_id=run_input.thread_id, run_id=run_input.run_id)
            )
        for event in spans.closing_events():
            await stream.publish(event)
        await stream.publish(self._status_event(announce, status))
        if status == "failed":
            await stream.publish(
                RunErrorEvent(
                    message="The agent could not finish.", code="agent_run_failed"
                )
            )
        else:
            await stream.publish(
                finished
                or RunFinishedEvent(
                    thread_id=run_input.thread_id,
                    run_id=run_input.run_id,
                    outcome=RunFinishedCancelledOutcome()
                    if status == "cancelled"
                    else None,
                )
            )
        await stream.close()

    @staticmethod
    def _status_event(announce: dict[str, Any], status: str) -> CustomEvent:
        return CustomEvent(name=ASSISTANT_EVENT, value={**announce, "status": status})

    @staticmethod
    async def _forget_native_thread(agent: LangGraphAgent, assistant_id: UUID) -> None:
        """The in-memory saver keeps every thread; nothing resumes a finished
        turn before sprint S4, so drop it."""
        checkpointer = getattr(agent.graph, "checkpointer", None)
        try:
            if checkpointer is not None:
                await checkpointer.adelete_thread(str(assistant_id))
        except Exception:
            logger.warning("Could not delete native thread %s", assistant_id)
