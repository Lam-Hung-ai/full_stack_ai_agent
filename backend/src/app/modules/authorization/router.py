from uuid import UUID

from fastapi import APIRouter, status

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.organization import CurrentOrganization
from app.database.session import SessionDep
from app.modules.authorization.schemas import (
    PermissionListResponse,
    RoleCreate,
    RoleListResponse,
    RoleResponse,
    RoleUpdate,
)
from app.modules.authorization.service import AuthorizationService

router = APIRouter(tags=["Roles"])


@router.get("/permissions", response_model=PermissionListResponse)
async def list_permissions(
    user: CurrentUser, session: SessionDep
) -> PermissionListResponse:
    """The permission catalog; the same for every organization."""
    return await AuthorizationService(session).catalog()


@router.get("/organizations/{organization_id}/roles", response_model=RoleListResponse)
async def list_roles(
    organization: CurrentOrganization, session: SessionDep
) -> RoleListResponse:
    return await AuthorizationService(session).list_roles(organization)


@router.post(
    "/organizations/{organization_id}/roles",
    status_code=status.HTTP_201_CREATED,
    response_model=RoleResponse,
)
async def create_role(
    data: RoleCreate, organization: CurrentOrganization, session: SessionDep
) -> RoleResponse:
    return await AuthorizationService(session).create_role(organization, data)


@router.patch(
    "/organizations/{organization_id}/roles/{role_id}", response_model=RoleResponse
)
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    organization: CurrentOrganization,
    session: SessionDep,
) -> RoleResponse:
    return await AuthorizationService(session).update_role(organization, role_id, data)


@router.delete(
    "/organizations/{organization_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
    role_id: UUID, organization: CurrentOrganization, session: SessionDep
) -> None:
    await AuthorizationService(session).delete_role(organization, role_id)
