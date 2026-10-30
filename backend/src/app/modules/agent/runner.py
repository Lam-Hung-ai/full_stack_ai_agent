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
    RunFinishedEvent,
)
from ag_ui_langgraph import LangGraphAgent

from app.modules.agent.bundle import AguiMessage, BundleBuilder

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
        agent_factory: Callable[[], LangGraphAgent],
        max_concurrent: int,
    ) -> None:
        self._agent_factory = agent_factory
        self._slots = asyncio.Semaphore(max_concurrent)
        self._streams: dict[UUID, RunStream] = {}
        self._tasks: dict[UUID, asyncio.Task[None]] = {}

    def start(
        self,
        *,
        assistant_id: UUID,
        run_input: RunAgentInput,
        announce: dict[str, Any],
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
                on_running=on_running,
                finalize=finalize,
            ),
            name=f"assistant-turn-{assistant_id}",
        )
        return stream

    def stream(self, assistant_id: UUID) -> RunStream | None:
        return self._streams.get(assistant_id)

    async def shutdown(self, timeout: float) -> None:
        """Let running turns finish within `timeout`, then cancel the rest
        (they are saved as cancelled with their partial content)."""
        tasks = list(self._tasks.values())
        if not tasks:
            return
        _, pending = await asyncio.wait(tasks, timeout=timeout)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    async def _execute(
        self,
        *,
        assistant_id: UUID,
        stream: RunStream,
        run_input: RunAgentInput,
        announce: dict[str, Any],
        on_running: Callable[[], Awaitable[None]],
        finalize: Finalizer,
    ) -> None:
        public_thread = run_input.thread_id
        builder = BundleBuilder({message.id for message in run_input.messages})
        agent = self._agent_factory().clone()
        finished: BaseEvent | None = None
        started = False
        status: TurnStatus = "failed"
        try:
            async with self._slots:
                await on_running()
                # ID decisions §1: the native thread is the assistant row; the
                # protocol stream keeps the conversation as its thread.
                native = run_input.model_copy(update={"thread_id": str(assistant_id)})
                async for event in agent.run(native):
                    if getattr(event, "thread_id", None) is not None:
                        event = event.model_copy(update={"thread_id": public_thread})
                    builder.apply(event)
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
                )
            finally:
                await self._forget_native_thread(agent, assistant_id)
                self._streams.pop(assistant_id, None)
                self._tasks.pop(assistant_id, None)

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
        if started:
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
                    thread_id=run_input.thread_id, run_id=run_input.run_id
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
