"""Chat models the agents run on.

Agents call these through the module (`models.build_chat_model()`), so tests
replace them with scripted fakes. Each model comes from `init_chat_model`; a
new provider is a module beside `openrouter.py` and a `langchain-<provider>`
dependency.
"""

from langchain_core.language_models import BaseChatModel

from app.config.settings import get_settings
from app.modules.ai.models.openrouter import openrouter_model


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


def build_title_model() -> BaseChatModel:
    """A short, non-streaming call that names a new chat (C01)."""
    settings = get_settings()
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
