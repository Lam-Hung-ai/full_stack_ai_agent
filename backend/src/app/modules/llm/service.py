"""System administration of LLM connections, models and assignments (QD-34).

Superusers only (router). Keys are encrypted before they reach the database
and never returned. Settings are passed to init_chat_model as given, so they
may not carry secrets: the API key has its own encrypted field.
"""

import asyncio
import importlib.util
import logging
import re
from typing import Any
from uuid import UUID

from langchain.chat_models import base as chat_models
from sqlalchemy import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies.auth import Principal
from app.common.exceptions.handlers import fail
from app.modules.llm import catalog, crypto
from app.modules.llm.repository import LlmRepository
from app.modules.llm.schemas import (
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentUpdate,
    ConnectionCreate,
    ConnectionListResponse,
    ConnectionResponse,
    ConnectionUpdate,
    ModelCreate,
    ModelListResponse,
    ModelResponse,
    ModelTestResponse,
    ModelUpdate,
    ProviderListResponse,
    ProviderResponse,
)

logger = logging.getLogger(__name__)

#: A setting whose name looks like a credential belongs in `api_key`.
SECRET_NAME = re.compile(r"key|secret|token|password|credential", re.IGNORECASE)
TEST_PROMPT = "Trả lời đúng một chữ: OK"
TEST_TIMEOUT_SECONDS = 30
DETAIL_LENGTH = 300


def providers() -> dict[str, str]:
    """init_chat_model's providers and the package each needs. LangChain keeps
    this table private; tests pin that it still exists."""
    return {
        name: module.split(".")[0]
        for name, (module, *_rest) in chat_models._BUILTIN_PROVIDERS.items()
    }


def _installed(package: str) -> bool:
    return importlib.util.find_spec(package) is not None


def _secret_names(value: Any, path: str = "") -> list[str]:
    if not isinstance(value, dict):
        return []
    found = []
    for name, item in value.items():
        where = f"{path}.{name}" if path else str(name)
        if SECRET_NAME.search(str(name)):
            found.append(where)
        found.extend(_secret_names(item, where))
    return found


def _check_settings(field: str, value: dict[str, Any] | None) -> None:
    if value is not None and (names := _secret_names(value)):
        fail(
            422,
            "secret_in_settings",
            f"Put credentials in api_key, not in {field}",
            details={"field": field, "names": names},
        )


def _check_provider(provider: str) -> None:
    package = providers().get(provider)
    if package is None:
        fail(422, "unknown_provider", details={"provider": provider})
    if not _installed(package):
        fail(
            422,
            "provider_not_installed",
            details={"provider": provider, "package": package},
        )


def _encrypt(api_key: str) -> tuple[str, str]:
    try:
        return crypto.encrypt(api_key)
    except crypto.EncryptionUnavailable as error:
        logger.error("Cannot encrypt an LLM API key: %s", error)
        fail(503, "llm_encryption_unavailable")


def _connection(row: RowMapping) -> ConnectionResponse:
    return ConnectionResponse(
        id=row["id"],
        key=row["key"],
        name=row["name"],
        provider=row["provider"],
        client_params=row["client_params"],
        has_api_key=row["api_key_ciphertext"] is not None,
        api_key_hint=row["api_key_hint"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class LlmAdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._llm = LlmRepository(session)

    def list_providers(self) -> ProviderListResponse:
        return ProviderListResponse(
            data=[
                ProviderResponse(
                    provider=name, package=package, installed=_installed(package)
                )
                for name, package in sorted(providers().items())
            ]
        )

    async def list_connections(self) -> ConnectionListResponse:
        rows = await self._llm.connections()
        return ConnectionListResponse(data=[_connection(row) for row in rows])

    async def create_connection(
        self, *, user: Principal, data: ConnectionCreate
    ) -> ConnectionResponse:
        _check_provider(data.provider)
        _check_settings("client_params", data.client_params)
        values: dict[str, Any] = data.model_dump(exclude={"api_key"})
        if data.api_key is not None:
            values["api_key_ciphertext"], values["api_key_hint"] = _encrypt(
                data.api_key
            )
        row = await self._write(lambda: self._llm.add_connection(values))
        self._log(user, "created connection", row["key"])
        return _connection(row)

    async def update_connection(
        self, *, user: Principal, connection_id: UUID, data: ConnectionUpdate
    ) -> ConnectionResponse:
        await self._require_connection(connection_id)
        changes = data.model_dump(exclude_unset=True, exclude={"api_key"})
        self._reject_nulls(changes, ("name", "provider", "client_params", "is_active"))
        if "provider" in changes:
            _check_provider(changes["provider"])
        _check_settings("client_params", changes.get("client_params"))
        if "api_key" in data.model_fields_set:
            if data.api_key is None:
                changes["api_key_ciphertext"] = changes["api_key_hint"] = None
            else:
                changes["api_key_ciphertext"], changes["api_key_hint"] = _encrypt(
                    data.api_key
                )
        if not changes:
            fail(422, "nothing_to_update")
        row = await self._write(
            lambda: self._llm.update_connection(connection_id, changes)
        )
        self._log(user, "updated connection", row["key"], sorted(changes))
        return _connection(row)

    async def delete_connection(self, *, user: Principal, connection_id: UUID) -> None:
        row = await self._require_connection(connection_id)
        await self._write(
            lambda: self._llm.delete_connection(connection_id),
            conflict="connection_in_use",
        )
        self._log(user, "deleted connection", row["key"])

    async def list_models(self) -> ModelListResponse:
        rows = await self._llm.models()
        return ModelListResponse(
            data=[ModelResponse.model_validate(dict(row)) for row in rows]
        )

    async def create_model(
        self, *, user: Principal, data: ModelCreate
    ) -> ModelResponse:
        await self._require_connection(data.connection_id)
        _check_settings("params", data.params)
        row = await self._write(lambda: self._llm.add_model(data.model_dump()))
        self._log(user, "created model", row["key"])
        return ModelResponse.model_validate(dict(row))

    async def update_model(
        self, *, user: Principal, model_id: UUID, data: ModelUpdate
    ) -> ModelResponse:
        await self._require_model(model_id)
        changes = data.model_dump(exclude_unset=True)
        self._reject_nulls(changes, tuple(changes))
        if "connection_id" in changes:
            await self._require_connection(changes["connection_id"])
        _check_settings("params", changes.get("params"))
        if not changes:
            fail(422, "nothing_to_update")
        row = await self._write(lambda: self._llm.update_model(model_id, changes))
        self._log(user, "updated model", row["key"], sorted(changes))
        return ModelResponse.model_validate(dict(row))

    async def delete_model(self, *, user: Principal, model_id: UUID) -> None:
        row = await self._require_model(model_id)
        await self._write(
            lambda: self._llm.delete_model(model_id), conflict="model_in_use"
        )
        self._log(user, "deleted model", row["key"])

    async def list_assignments(self) -> AssignmentListResponse:
        by_purpose: dict[str, list[UUID]] = {
            purpose: [] for purpose in catalog.PURPOSES
        }
        for row in await self._llm.assignments():
            by_purpose.setdefault(row["purpose"], []).append(row["model_id"])
        return AssignmentListResponse(
            data=[
                AssignmentResponse(
                    purpose=purpose,
                    description=catalog.PURPOSES.get(purpose, purpose),
                    model_ids=ids,
                )
                for purpose, ids in by_purpose.items()
            ]
        )

    async def set_assignment(
        self, *, user: Principal, purpose: str, data: AssignmentUpdate
    ) -> AssignmentResponse:
        if purpose not in catalog.PURPOSES:
            fail(404, "purpose_not_found")
        ids = list(data.model_ids)
        if len(set(ids)) != len(ids):
            fail(422, "duplicate_model")
        missing = set(ids) - await self._llm.existing_models(ids)
        if missing:
            fail(422, "model_not_found", details={"ids": sorted(map(str, missing))})
        await self._llm.replace_assignments(purpose, ids)
        await self._session.commit()
        self._log(user, "assigned models", purpose, [str(i) for i in ids])
        return AssignmentResponse(
            purpose=purpose, description=catalog.PURPOSES[purpose], model_ids=ids
        )

    async def test_model(self, *, model_id: UUID) -> ModelTestResponse:
        """One short call with the stored settings and key."""
        row = await self._llm.model_with_connection(model_id)
        if row is None:
            fail(404, "model_not_found")
        try:
            spec = catalog.spec_of(row)
        except crypto.EncryptionUnavailable:
            fail(503, "llm_encryption_unavailable")
        try:
            model = catalog.build(spec, streaming=False)
            reply = await asyncio.wait_for(
                model.ainvoke(TEST_PROMPT), timeout=TEST_TIMEOUT_SECONDS
            )
        except Exception as error:  # the provider's error is the answer here
            detail = f"{type(error).__name__}: {error}"
            return ModelTestResponse(ok=False, detail=detail[:DETAIL_LENGTH])
        return ModelTestResponse(ok=True, detail=str(reply.text)[:DETAIL_LENGTH])

    async def _require_connection(self, connection_id: UUID) -> RowMapping:
        row = await self._llm.connection(connection_id)
        if row is None:
            fail(404, "connection_not_found")
        return row

    async def _require_model(self, model_id: UUID) -> RowMapping:
        row = await self._llm.model(model_id)
        if row is None:
            fail(404, "model_not_found")
        return row

    async def _write(self, action, *, conflict: str = "llm_key_taken"):
        """Run a write and commit; a unique or foreign-key conflict is 409."""
        try:
            result = await action()
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            fail(409, conflict)
        return result

    @staticmethod
    def _reject_nulls(changes: dict[str, Any], fields: tuple[str, ...]) -> None:
        for name in fields:
            if name in changes and changes[name] is None:
                fail(422, "null_not_allowed", details={"field": name})

    @staticmethod
    def _log(user: Principal, action: str, target: str, extra: Any = None) -> None:
        logger.info(
            "LLM config %s",
            action,
            extra={
                "fields": {
                    "user_id": str(user.id),
                    "target": target,
                    **({"changes": extra} if extra is not None else {}),
                }
            },
        )
