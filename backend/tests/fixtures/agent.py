"""A scripted chat model in place of OpenRouter."""

import json
import re
import time
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGenerationChunk


class ScriptedModel(GenericFakeChatModel):
    """Streams the scripted replies word by word and records every prompt
    and every tool list the agent binds."""

    prompts: list[list[BaseMessage]] = []
    bound_tools: list[list[str]] = []
    fail_after_words: int | None = None
    #: Seconds per streamed token, to keep a turn running for a while.
    word_delay: float = 0
    streamed_words: int = 0
    #: Runs before each reply, e.g. to change grants in the middle of a turn.
    before_reply: Callable[[], None] | None = None

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedModel":
        self.bound_tools.append(sorted(getattr(item, "name", item) for item in tools))
        return self

    def _stream(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> Iterator[ChatGenerationChunk]:
        self.prompts.append(list(messages))
        if self.before_reply is not None:
            self.before_reply()
        reply = self._generate(messages).generations[0].message
        if isinstance(reply, AIMessage) and reply.tool_calls:
            yield ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    tool_call_chunks=[
                        {
                            "name": call["name"],
                            "args": json.dumps(call["args"]),
                            "id": call["id"],
                            "index": index,
                        }
                        for index, call in enumerate(reply.tool_calls)
                    ],
                )
            )
            return
        for index, token in enumerate(re.split(r"(\s)", str(reply.content))):
            if self.fail_after_words is not None and index >= self.fail_after_words:
                raise RuntimeError("provider exploded")
            if self.word_delay:
                time.sleep(self.word_delay)
            self.streamed_words += 1
            yield ChatGenerationChunk(message=AIMessageChunk(content=token))


@pytest.fixture
def scripted_model(monkeypatch):
    """Replace the model; call with the replies the agent should give."""
    from app.modules.agent import graph

    def install(
        *replies: str | AIMessage,
        fail_after_words: int | None = None,
        word_delay: float = 0,
        before_reply: Callable[[], None] | None = None,
    ) -> ScriptedModel:
        model = ScriptedModel(
            messages=iter(
                [
                    r if isinstance(r, AIMessage) else AIMessage(content=r)
                    for r in replies
                ]
            ),
            prompts=[],
            bound_tools=[],
            fail_after_words=fail_after_words,
            word_delay=word_delay,
            before_reply=before_reply,
        )
        monkeypatch.setattr(graph, "build_model", lambda: model)
        graph.get_agent.cache_clear()
        return model

    yield install
    graph.get_agent.cache_clear()
