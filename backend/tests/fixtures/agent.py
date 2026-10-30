"""A scripted chat model in place of OpenRouter."""

from collections.abc import Iterator
from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGenerationChunk


class ScriptedModel(GenericFakeChatModel):
    """Streams the scripted replies word by word and records every prompt."""

    prompts: list[list[BaseMessage]] = []
    fail_after_words: int | None = None

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedModel":
        return self

    def _stream(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> Iterator[ChatGenerationChunk]:
        self.prompts.append(list(messages))
        for index, chunk in enumerate(super()._stream(messages, *args, **kwargs)):
            if self.fail_after_words is not None and index >= self.fail_after_words:
                raise RuntimeError("provider exploded")
            yield chunk


@pytest.fixture
def scripted_model(monkeypatch):
    """Replace the model; call with the replies the agent should give."""
    from app.modules.agent import agui, graph

    def install(*replies: str, fail_after_words: int | None = None) -> ScriptedModel:
        model = ScriptedModel(
            messages=iter([AIMessage(content=reply) for reply in replies]),
            prompts=[],
            fail_after_words=fail_after_words,
        )
        monkeypatch.setattr(graph, "build_model", lambda: model)
        graph.get_agent.cache_clear()
        agui.get_agui_agent.cache_clear()
        return model

    yield install
    graph.get_agent.cache_clear()
    agui.get_agui_agent.cache_clear()
