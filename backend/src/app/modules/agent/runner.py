"""In-process runner for assistant turns (QD-15).

A turn runs in an asyncio task owned by the application, not by the HTTP
request: closing the browser detaches a subscriber and the turn still finishes
and is saved. Events are buffered per turn so a subscriber that arrives after
the start still sees them in order. Sprint S5 moves the live buffer to Redis
for reconnects across processes.

Database decisions §6: content is written once the turn ends. The terminal
RUN_FINISHED / RUN_ERROR is published only after that write commits, so a
client that saw the end can reload and find the same result. A turn that
stops on an interrupt ends as `requires_action`; its checkpoint is handed to
the finalizer to be stored in the same transaction (agent/checkpoints.py).

Every event is also mirrored to Redis (agent/live.py) so `connect` can show a
running turn from any process, and stop requests reach the owning process.
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID, uuid4

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
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langgraph.types import Interrupt

from app.modules.agent.bundle import AguiMessage, BundleBuilder
from app.modules.agent.checkpoints import TurnSaver, thread_config
from app.modules.agent.lifecycle import OpenSpans
from app.modules.agent.live import LiveStore, LiveView
from app.modules.agent.tools import ToolGuard, current_tool_guard

logger = logging.getLogger(__name__)

TurnStatus = Literal["completed", "failed", "cancelled", "requires_action"]
#: Name of the CUSTOM event that ties the protocol stream to SQL rows.
ASSISTANT_EVENT = "chat.assistant"


@dataclass(frozen=True)
class Pause:
    """A turn stopped on interrupts; `saver` holds the checkpoint to store."""

    saver: TurnSaver
    thread_id: str
    interrupts: list[Interrupt]


#: Saves the outcome; returns events to announce before the final status
#: (e.g. the activity asking the user).
type Finalizer = Callable[
    [TurnStatus, list[AguiMessage], Pause | None], Awaitable[list[BaseEvent]]
]
type InputPreparer = Callable[[RunAgentInput], Awaitable[RunAgentInput]]
#: (tools, saver, trace ids) -> the turn's agent.
type AgentFactory = Callable[
    [frozenset[str], BaseCheckpointSaver, dict[str, str]], LangGraphAgent
]


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


class _Channel:
    """Where one turn's events go: local subscribers first, then Redis. A
    Redis failure only degrades the live view; the turn goes on."""

    def __init__(
        self, stream: RunStream, live: LiveStore | None, assistant_id: UUID
    ) -> None:
        self.stream = stream
        self.live = live
        self.assistant_id = assistant_id
        self.seq = 0

    async def publish(
        self, event: BaseEvent, *, snapshot: list[AguiMessage] | None = None
    ) -> None:
        """`snapshot` is the bundle when this event leaves nothing open."""
        await self.stream.publish(event)
        if self.live is None:
            return
        try:
            self.seq += 1
            entry = await self.live.append(self.assistant_id, self.seq, event)
            if snapshot is not None:
                await self.live.save_view(
                    self.assistant_id, LiveView(snapshot, entry, self.seq)
                )
        except Exception:
            logger.warning("Live view of %s stopped", self.assistant_id, exc_info=True)
            self.live = None

    async def close(self) -> None:
        await self.stream.close()
        if self.live is not None:
            try:
                await self.live.end(self.assistant_id)
            except Exception:
                logger.warning("Could not expire live keys of %s", self.assistant_id)


def usage_fields(finished: BaseEvent | None) -> dict[str, Any]:
    """Token counts the provider reported for the turn (`RUN_FINISHED.usage`),
    summed over its model calls, with the models used."""
    usage = getattr(finished, "usage", None) or []
    if not usage:
        return {}
    return {
        "input_tokens": sum(item.input_tokens or 0 for item in usage),
        "output_tokens": sum(item.output_tokens or 0 for item in usage),
        "models": sorted({item.model for item in usage if item.model}),
    }


class Runner:
    def __init__(
        self,
        *,
        agent_factory: AgentFactory,
        max_concurrent: int,
        max_queued: int | None = None,
        live: LiveStore | None = None,
    ) -> None:
        self._agent_factory = agent_factory
        self._slots = asyncio.Semaphore(max_concurrent)
        #: Turns this process holds at most, running or waiting for a slot.
        self._capacity = max_concurrent + (
            max_queued if max_queued is not None else max_concurrent
        )
        self._live = live
        #: Names this process as a turn's owner in Redis.
        self.process_id = str(uuid4())
        self._streams: dict[UUID, RunStream] = {}
        self._tasks: dict[UUID, asyncio.Task[None]] = {}
        #: Turns saving their outcome; cancelling now would lose the end events.
        self._finishing: set[UUID] = set()

    @property
    def live(self) -> LiveStore | None:
        return self._live

    def has_room(self) -> bool:
        """Whether one more turn may start or queue here. Callers refuse a
        new turn otherwise instead of letting the queue grow without bound."""
        return len(self._tasks) < self._capacity

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
        known_ids: set[str] | None = None,
        resume_from: CheckpointTuple | None = None,
        prepare: InputPreparer | None = None,
        log_fields: dict[str, Any] | None = None,
    ) -> RunStream:
        """Run a turn in the background. `known_ids` are protocol messages the
        bundle must not repeat (default: the input); `resume_from` is the
        stored pause a resumed turn continues from; `prepare` completes the
        input inside the turn (attached files), where a failure fails the turn."""
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
                known_ids=known_ids,
                resume_from=resume_from,
                prepare=prepare,
                log_fields=log_fields or {},
            ),
            name=f"assistant-turn-{assistant_id}",
        )
        return stream

    def stream(self, assistant_id: UUID) -> RunStream | None:
        return self._streams.get(assistant_id)

    async def stop(
        self, assistant_id: UUID, *, timeout: float
    ) -> Literal["local", "remote", "orphan"]:
        """Stop a turn wherever it runs. Here: cancel it and wait up to
        `timeout` for it to be saved. Another process owns it: signal that
        process ("remote"; the caller watches the database). Nobody owns it:
        "orphan", for the caller to cancel in place."""
        task = self._tasks.get(assistant_id)
        if task is not None:
            self._cancel(assistant_id, task)
            await asyncio.wait({task}, timeout=timeout)
            return "local"
        if self._live is not None:
            try:
                if await self._live.owned(assistant_id):
                    await self._live.request_stop(assistant_id)
                    return "remote"
            except Exception:
                logger.warning("Could not reach Redis to stop %s", assistant_id)
        return "orphan"

    async def listen_for_stops(self) -> None:
        """Cancel turns of this process that another process was asked to
        stop. Runs for the life of the app; reconnects after Redis errors."""
        if self._live is None:
            return
        while True:
            try:
                async for assistant_id in self._live.stop_requests():
                    if task := self._tasks.get(assistant_id):
                        self._cancel(assistant_id, task)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning("Stop channel lost; retrying", exc_info=True)
                await asyncio.sleep(1)

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
        known_ids: set[str] | None,
        resume_from: CheckpointTuple | None,
        prepare: InputPreparer | None,
        log_fields: dict[str, Any],
    ) -> None:
        public_thread = run_input.thread_id
        began = time.monotonic()
        # ID decisions §1: the native thread is the assistant row; the
        # protocol stream keeps the conversation as its thread.
        native_thread = str(assistant_id)
        builder = BundleBuilder(
            known_ids
            if known_ids is not None
            else {message.id for message in run_input.messages}
        )
        spans = OpenSpans()
        channel = _Channel(stream, self._live, assistant_id)
        heartbeat = asyncio.create_task(self._own(assistant_id))
        saver = TurnSaver()
        # Tasks the graph spawns copy this context, so tool calls see the guard.
        current_tool_guard.set(tool_guard)
        finished: BaseEvent | None = None
        pause: Pause | None = None
        started = False
        status: TurnStatus = "failed"
        try:
            if resume_from is not None:
                saver.seed(resume_from)
            agent = self._agent_factory(
                tools,
                saver,
                {
                    **log_fields,
                    "assistant_id": str(assistant_id),
                    "conversation_id": public_thread,
                },
            )
            async with self._slots:
                await on_running()
                if prepare is not None:
                    run_input = await prepare(run_input)
                native = run_input.model_copy(update={"thread_id": native_thread})
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
                    await channel.publish(
                        event, snapshot=builder.bundle() if spans.idle else None
                    )
                    if event.type == EventType.RUN_STARTED:
                        started = True
                        await channel.publish(self._status_event(announce, "running"))
            state = await agent.graph.aget_state(thread_config(native_thread))
            interrupts = [item for task in state.tasks for item in task.interrupts]
            if interrupts and saver.has_pause(native_thread):
                pause = Pause(saver, native_thread, interrupts)
                status = "requires_action"
            else:
                status = "completed"
        except asyncio.CancelledError:
            status = "cancelled"
            raise
        except Exception:
            logger.exception("Assistant turn %s failed", assistant_id)
        finally:
            self._finishing.add(assistant_id)
            heartbeat.cancel()
            try:
                await self._finish(
                    channel=channel,
                    status=status,
                    content=builder.bundle(),
                    finalize=finalize,
                    announce=announce,
                    started=started,
                    finished=finished,
                    run_input=run_input,
                    spans=spans,
                    pause=pause,
                )
            finally:
                self._streams.pop(assistant_id, None)
                self._tasks.pop(assistant_id, None)
                self._finishing.discard(assistant_id)
                logger.info(
                    "Assistant turn ended",
                    extra={
                        "fields": {
                            **log_fields,
                            "assistant_id": str(assistant_id),
                            "conversation_id": public_thread,
                            "status": status,
                            "resumed": resume_from is not None,
                            "duration_ms": round((time.monotonic() - began) * 1000),
                            **usage_fields(finished),
                        }
                    },
                )

    async def _own(self, assistant_id: UUID) -> None:
        """Keep this process named as the turn's owner while it runs."""
        if self._live is None:
            return
        interval = self._live.settings.owner_ttl / 3
        while True:
            try:
                await self._live.claim(assistant_id, self.process_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning("Could not claim live ownership of %s", assistant_id)
            await asyncio.sleep(interval)

    async def _finish(
        self,
        *,
        channel: _Channel,
        status: TurnStatus,
        content: list[AguiMessage],
        finalize: Finalizer,
        announce: dict[str, Any],
        started: bool,
        finished: BaseEvent | None,
        run_input: RunAgentInput,
        spans: OpenSpans,
        pause: Pause | None,
    ) -> None:
        try:
            # Shielded: a shutdown cancellation must not abort the final write.
            announced = await asyncio.shield(finalize(status, content, pause))
        except Exception:
            logger.exception("Could not save assistant turn %s", announce)
            await channel.publish(
                RunErrorEvent(
                    message="The answer could not be saved.", code="persist_failed"
                )
            )
            await channel.close()
            return
        if not started:
            # Stopped while waiting for a slot: still give subscribers a
            # complete lifecycle so the client can show the outcome.
            await channel.publish(
                RunStartedEvent(thread_id=run_input.thread_id, run_id=run_input.run_id)
            )
        for event in [*spans.closing_events(), *announced]:
            await channel.publish(event)
        await channel.publish(self._status_event(announce, status))
        if status == "failed":
            await channel.publish(
                RunErrorEvent(
                    message="The agent could not finish.", code="agent_run_failed"
                )
            )
        else:
            await channel.publish(
                finished
                or RunFinishedEvent(
                    thread_id=run_input.thread_id,
                    run_id=run_input.run_id,
                    outcome=RunFinishedCancelledOutcome()
                    if status == "cancelled"
                    else None,
                )
            )
        await channel.close()

    @staticmethod
    def _status_event(announce: dict[str, Any], status: str) -> CustomEvent:
        return CustomEvent(name=ASSISTANT_EVENT, value={**announce, "status": status})
