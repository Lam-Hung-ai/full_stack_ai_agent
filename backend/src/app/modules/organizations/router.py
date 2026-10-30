from fastapi import APIRouter, status

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.organization import CurrentOrganization
from app.database.session import SessionDep
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.modules.organizations.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=OrganizationResponse
)
async def create_organization(
    data: OrganizationCreate, user: CurrentUser, session: SessionDep
) -> OrganizationResponse:
    """The creator becomes its owner; the organization gets its workspace."""
    return await OrganizationService(session).create(user=user, data=data)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization: CurrentOrganization, session: SessionDep
) -> OrganizationResponse:
    return await OrganizationService(session).get(organization)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    data: OrganizationUpdate, organization: CurrentOrganization, session: SessionDep
) -> OrganizationResponse:
    return await OrganizationService(session).update(organization, data)
