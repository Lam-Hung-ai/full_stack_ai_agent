from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_llm_connections as connections
from app.database.generated_tables import t_llm_model_assignments as assignments
from app.database.generated_tables import t_llm_models as models


class LlmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def connections(self) -> list[RowMapping]:
        statement = select(connections).order_by(connections.c.key)
        return list((await self._session.execute(statement)).mappings().all())

    async def connection(self, connection_id: UUID) -> RowMapping | None:
        statement = select(connections).where(connections.c.id == connection_id)
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def add_connection(self, values: dict[str, Any]) -> RowMapping:
        statement = insert(connections).values(values).returning(connections)
        return (await self._session.execute(statement)).mappings().one()

    async def update_connection(
        self, connection_id: UUID, values: dict[str, Any]
    ) -> RowMapping:
        statement = (
            update(connections)
            .where(connections.c.id == connection_id)
            .values(values)
            .returning(connections)
        )
        return (await self._session.execute(statement)).mappings().one()

    async def delete_connection(self, connection_id: UUID) -> None:
        await self._session.execute(
            delete(connections).where(connections.c.id == connection_id)
        )

    async def models(self) -> list[RowMapping]:
        statement = select(models).order_by(models.c.key)
        return list((await self._session.execute(statement)).mappings().all())

    async def model(self, model_id: UUID) -> RowMapping | None:
        statement = select(models).where(models.c.id == model_id)
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def model_with_connection(self, model_id: UUID) -> RowMapping | None:
        """A model joined with its connection, as `catalog.spec_of` reads it."""
        statement = (
            select(
                models.c.key,
                models.c.model,
                models.c.params,
                connections.c.provider,
                connections.c.client_params,
                connections.c.api_key_ciphertext,
            )
            .join(connections, connections.c.id == models.c.connection_id)
            .where(models.c.id == model_id)
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def add_model(self, values: dict[str, Any]) -> RowMapping:
        statement = insert(models).values(values).returning(models)
        return (await self._session.execute(statement)).mappings().one()

    async def update_model(self, model_id: UUID, values: dict[str, Any]) -> RowMapping:
        statement = (
            update(models)
            .where(models.c.id == model_id)
            .values(values)
            .returning(models)
        )
        return (await self._session.execute(statement)).mappings().one()

    async def delete_model(self, model_id: UUID) -> None:
        await self._session.execute(delete(models).where(models.c.id == model_id))

    async def assignments(self) -> list[RowMapping]:
        statement = select(assignments).order_by(
            assignments.c.purpose, assignments.c.position
        )
        return list((await self._session.execute(statement)).mappings().all())

    async def existing_models(self, model_ids: list[UUID]) -> set[UUID]:
        statement = select(models.c.id).where(models.c.id.in_(model_ids))
        return set((await self._session.execute(statement)).scalars().all())

    async def replace_assignments(self, purpose: str, model_ids: list[UUID]) -> None:
        await self._session.execute(
            delete(assignments).where(assignments.c.purpose == purpose)
        )
        if model_ids:
            await self._session.execute(
                insert(assignments),
                [
                    {"purpose": purpose, "position": position, "model_id": model_id}
                    for position, model_id in enumerate(model_ids)
                ],
            )
