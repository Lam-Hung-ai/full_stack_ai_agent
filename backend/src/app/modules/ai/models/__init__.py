"""Chat models the agents run on.

A purpose with models assigned in the database (`/admin/llm`, QD-34) runs on
those, built by `init_chat_model` (`llm.catalog`); otherwise on the
environment configuration below (OPENROUTER_*). Agents call these through the
module (`models.build_chain(...)`), so tests replace them with scripted fakes.
"""

from typing import Any

from langchain_core.language_models import BaseChatModel

from app.config.settings import get_settings
from app.modules.ai.models.openrouter import openrouter_model
from app.modules.llm import catalog
from app.modules.llm.catalog import ModelChain, ModelSpec


def from_spec(spec: ModelSpec, **overrides: Any) -> BaseChatModel:
    """A model configured in the database."""
    return catalog.build(spec, **overrides)


def build_chain(chain: ModelChain | None) -> tuple[BaseChatModel, list[BaseChatModel]]:
    """The model answering a turn and its fallbacks, in order."""
    if chain is None or get_settings().agent_fake_model:
        return build_chat_model(), build_fallback_models()
    built = [from_spec(spec, streaming=True) for spec in chain.specs]
    return built[0], built[1:]


def _chat_params() -> dict:
    effort = get_settings().openrouter_reasoning_effort
    return {"reasoning": {"effort": effort} if effort else None, "streaming": True}


def build_chat_model() -> BaseChatModel:
    """The model answering a turn."""
    settings = get_settings()
    if settings.agent_fake_model:
        from app.modules.ai.models.fake import LoadTestModel

        return LoadTestModel()
    return openrouter_model(settings.openrouter_model, **_chat_params())


def build_fallback_models() -> list[BaseChatModel]:
    """Tried in order when the primary model call fails (provider error,
    rate limit, outage); empty means no fallback."""
    settings = get_settings()
    if settings.agent_fake_model:
        return []
    return [
        openrouter_model(name, **_chat_params())
        for name in settings.openrouter_fallback_models
    ]


def build_title_model(chain: ModelChain | None = None) -> BaseChatModel:
    """A short, non-streaming call that names a new chat (C01): the first
    model of the `title` purpose, or the environment's model."""
    settings = get_settings()
    if chain is not None and not settings.agent_fake_model:
        return from_spec(chain.specs[0], streaming=False, max_tokens=40)
    if settings.agent_fake_model:
        from app.modules.ai.models.fake import LoadTestModel

        return LoadTestModel(words=4, word_delay=0)
    return openrouter_model(
        settings.openrouter_model,
        # A name needs no chain of thought; reasoning made it cost ~2k tokens.
        reasoning={"effort": "none"},
        max_tokens=40,
        streaming=False,
    )
