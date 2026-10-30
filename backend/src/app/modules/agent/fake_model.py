"""A model that answers without a provider, for load tests (S9).

Streams a fixed answer word by word with a delay, like a provider would, so
a load test measures the API, stream, runner, PostgreSQL and Redis without
paying for or waiting on a real model. Enabled by `AGENT_FAKE_MODEL=true`;
never in production.
"""

import asyncio
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult


class LoadTestModel(BaseChatModel):
    words: int = 60
    #: Seconds between streamed words (about a provider's pace).
    word_delay: float = 0.02

    @property
    def _llm_type(self) -> str:
        return "load-test"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "LoadTestModel":
        # It never calls tools; accepting them keeps the agent graph unchanged.
        return self

    def _answer(self) -> list[str]:
        return [f"từ{i} " for i in range(self.words)]

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        text = "".join(self._answer()).strip()
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        for word in self._answer():
            yield ChatGenerationChunk(message=AIMessageChunk(content=word))

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        for word in self._answer():
            await asyncio.sleep(self.word_delay)
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=word))
            if run_manager:
                await run_manager.on_llm_new_token(word, chunk=chunk)
            yield chunk
