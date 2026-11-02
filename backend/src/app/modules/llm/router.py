from uuid import UUID

from fastapi import APIRouter, status

from app.common.dependencies.auth import SuperUser
from app.database.session import SessionDep
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
)
from app.modules.llm.service import LlmAdminService

#: System administration of the models agents run on (QD-34): superusers only.
router = APIRouter(prefix="/admin/llm", tags=["LLM administration"])


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers(user: SuperUser, session: SessionDep) -> ProviderListResponse:
    """Providers of LangChain's init_chat_model and whether each is installed."""
    return LlmAdminService(session).list_providers()


@router.get("/connections", response_model=ConnectionListResponse)
async def list_connections(
    user: SuperUser, session: SessionDep
) -> ConnectionListResponse:
    return await LlmAdminService(session).list_connections()


@router.post(
    "/connections",
    status_code=status.HTTP_201_CREATED,
    response_model=ConnectionResponse,
)
async def create_connection(
    data: ConnectionCreate, user: SuperUser, session: SessionDep
) -> ConnectionResponse:
    return await LlmAdminService(session).create_connection(user=user, data=data)


@router.patch("/connections/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: UUID, data: ConnectionUpdate, user: SuperUser, session: SessionDep
) -> ConnectionResponse:
    return await LlmAdminService(session).update_connection(
        user=user, connection_id=connection_id, data=data
    )


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID, user: SuperUser, session: SessionDep
) -> None:
    """409 `connection_in_use` while a model uses the connection."""
    await LlmAdminService(session).delete_connection(
        user=user, connection_id=connection_id
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models(user: SuperUser, session: SessionDep) -> ModelListResponse:
    return await LlmAdminService(session).list_models()


@router.post(
    "/models", status_code=status.HTTP_201_CREATED, response_model=ModelResponse
)
async def create_model(
    data: ModelCreate, user: SuperUser, session: SessionDep
) -> ModelResponse:
    return await LlmAdminService(session).create_model(user=user, data=data)


@router.patch("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: UUID, data: ModelUpdate, user: SuperUser, session: SessionDep
) -> ModelResponse:
    return await LlmAdminService(session).update_model(
        user=user, model_id=model_id, data=data
    )


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: UUID, user: SuperUser, session: SessionDep) -> None:
    """409 `model_in_use` while a purpose lists the model."""
    await LlmAdminService(session).delete_model(user=user, model_id=model_id)


@router.post("/models/{model_id}/test", response_model=ModelTestResponse)
async def test_model(
    model_id: UUID, user: SuperUser, session: SessionDep
) -> ModelTestResponse:
    """One short call with the stored settings and key; the provider's error
    is returned in `detail` when it fails."""
    return await LlmAdminService(session).test_model(model_id=model_id)


@router.get("/assignments", response_model=AssignmentListResponse)
async def list_assignments(
    user: SuperUser, session: SessionDep
) -> AssignmentListResponse:
    return await LlmAdminService(session).list_assignments()


@router.put("/assignments/{purpose}", response_model=AssignmentResponse)
async def set_assignment(
    purpose: str, data: AssignmentUpdate, user: SuperUser, session: SessionDep
) -> AssignmentResponse:
    """The models of a purpose in order (first answers, the rest are
    fallbacks); an empty list goes back to the environment configuration."""
    return await LlmAdminService(session).set_assignment(
        user=user, purpose=purpose, data=data
    )
