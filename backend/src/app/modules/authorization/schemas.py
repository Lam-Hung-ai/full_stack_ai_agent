from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, StringConstraints, model_validator

from app.common.schemas.common import Input, Name

PermissionKey = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class PermissionResponse(BaseModel):
    #: `resource.action`, the form roles list their permissions in.
    key: str
    resource: str
    action: str
    description: str | None


class PermissionListResponse(BaseModel):
    data: list[PermissionResponse]


class RoleResponse(BaseModel):
    id: UUID
    name: str
    #: owner, admin or member for the roles every organization starts with.
    role_key: str | None
    description: str | None
    permissions: list[str]
    #: Active members holding the role.
    member_count: int
    #: The owner role always holds every permission and cannot be changed.
    locked: bool


class RoleListResponse(BaseModel):
    data: list[RoleResponse]


class RoleCreate(Input):
    name: Name
    description: Description | None = None
    permissions: list[PermissionKey] = []


class RoleUpdate(Input):
    """Built-in roles keep their name; only their permissions change."""

    name: Name | None = None
    description: Description | None = None
    permissions: list[PermissionKey] | None = None

    @model_validator(mode="after")
    def _something_to_change(self) -> "RoleUpdate":
        if not self.model_fields_set:
            raise ValueError("Nothing to update")
        return self
