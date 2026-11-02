"""Models the agents run on, read from the database (QD-34).

A purpose (`chat`, `title`) lists models in order: the first answers, the
rest are fallbacks. Each becomes `init_chat_model(model, model_provider=…,
api_key=…, **client_params, **params)`. A purpose with no active model uses
the environment configuration instead (`ai.models`).
"""

import json
from dataclasses import dataclass, field
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_llm_connections as connections
from app.database.generated_tables import t_llm_model_assignments as assignments
from app.database.generated_tables import t_llm_models as models
from app.modules.llm import crypto

#: What a purpose is used for; the admin page assigns models to these.
PURPOSES: dict[str, str] = {
    "chat": "Trả lời trong chat",
    "title": "Đặt tên chat mới",
}


@dataclass(frozen=True)
class ModelSpec:
    """Everything `init_chat_model` needs for one model. Hashable, so a
    compiled agent can be cached per configuration."""

    key: str
    provider: str
    model: str
    #: JSON of the merged client and model settings (sorted keys).
    settings: str
    api_key: str | None = field(default=None, repr=False)

    @property
    def kwargs(self) -> dict[str, Any]:
        return json.loads(self.settings)


@dataclass(frozen=True)
class ModelChain:
    purpose: str
    specs: tuple[ModelSpec, ...]


def build(spec: ModelSpec, **overrides: Any) -> BaseChatModel:
    """The chat model of a spec; `overrides` win over stored settings."""
    kwargs = {**spec.kwargs, **overrides}
    if spec.api_key is not None:
        kwargs["api_key"] = spec.api_key
    return init_chat_model(spec.model, model_provider=spec.provider, **kwargs)


def spec_of(row: Any) -> ModelSpec:
    """A spec from a joined model + connection row, decrypting the key."""
    settings = {**row["client_params"], **row["params"]}
    ciphertext = row["api_key_ciphertext"]
    return ModelSpec(
        key=row["key"],
        provider=row["provider"],
        model=row["model"],
        settings=json.dumps(settings, sort_keys=True),
        api_key=crypto.decrypt(ciphertext) if ciphertext else None,
    )


class ModelCatalog:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def chain(self, purpose: str) -> ModelChain | None:
        """The active models of `purpose` in order, or None when it has none.
        Raises `crypto.EncryptionUnavailable` if a key cannot be decrypted."""
        statement = (
            select(
                models.c.key,
                models.c.model,
                models.c.params,
                connections.c.provider,
                connections.c.client_params,
                connections.c.api_key_ciphertext,
            )
            .select_from(assignments)
            .join(models, models.c.id == assignments.c.model_id)
            .join(connections, connections.c.id == models.c.connection_id)
            .where(
                assignments.c.purpose == purpose,
                models.c.is_active.is_(True),
                connections.c.is_active.is_(True),
            )
            .order_by(assignments.c.position)
        )
        rows = (await self._session.execute(statement)).mappings().all()
        if not rows:
            return None
        return ModelChain(purpose, tuple(spec_of(row) for row in rows))
