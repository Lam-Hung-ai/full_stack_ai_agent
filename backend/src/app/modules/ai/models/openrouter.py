from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.config.settings import get_settings


def openrouter_model(model: str, **params: Any) -> BaseChatModel:
    """A chat model served through OpenRouter, with the app's credentials and
    attribution; `params` are the model's own settings (reasoning, streaming…)."""
    settings = get_settings()
    return init_chat_model(
        model,
        model_provider="openrouter",
        api_key=settings.openrouter_api_key,
        openrouter_api_base=settings.openrouter_base_url,
        app_url=settings.openrouter_site_url,
        app_title=settings.openrouter_app_name,
        **params,
    )
