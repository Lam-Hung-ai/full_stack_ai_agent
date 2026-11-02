"""Langfuse traces of assistant turns (S9): model calls, tools, tokens and
cost per turn. Off unless `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`
are set; then each turn's run carries a LangChain callback handler.

Traces hold prompts and answers: point them only at a Langfuse instance
allowed to store chat content.
"""

import logging
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _client() -> Any | None:
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    from langfuse import Langfuse

    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key.get_secret_value(),
        host=settings.langfuse_host,
    )


def tracing_config(trace: Mapping[str, str]) -> RunnableConfig | None:
    """Run config tracing one turn, or None when tracing is off. The
    conversation is the Langfuse session and the user its user."""
    if _client() is None:
        return None
    from langfuse.langchain import CallbackHandler

    return {
        "callbacks": [CallbackHandler(public_key=get_settings().langfuse_public_key)],
        "run_name": "chat-turn",
        "metadata": {
            "langfuse_session_id": trace.get("conversation_id"),
            "langfuse_user_id": trace.get("user_id"),
            "langfuse_tags": ["chat"],
            "assistant_id": trace.get("assistant_id"),
            "workspace_id": trace.get("workspace_id"),
        },
    }


def flush_traces() -> None:
    """Send what is buffered; called when the app shuts down."""
    client = _client()
    if client is not None:
        try:
            client.shutdown()
        except Exception:
            logger.warning("Could not flush Langfuse traces", exc_info=True)
