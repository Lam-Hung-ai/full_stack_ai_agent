from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from app.common.schemas.common import Input, Name

Key = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[a-z][a-z0-9_-]{0,62}$"),
]
Provider = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z][a-z0-9_]*$")
]
ModelName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
ApiKey = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Settings = Annotated[dict[str, Any], Field(max_length=50)]


class ProviderResponse(BaseModel):
    provider: str
    #: Python package of the LangChain integration.
    package: str
    #: Whether that package is installed, i.e. the provider can be used.
    installed: bool


class ProviderListResponse(BaseModel):
    data: list[ProviderResponse]


class ConnectionCreate(Input):
    key: Key
    name: Name
    provider: Provider
    #: Client settings passed to init_chat_model as is (base URL, headers…).
    client_params: Settings = {}
    api_key: ApiKey | None = None
    is_active: bool = True


class ConnectionUpdate(Input):
    """Omitted fields stay. `api_key`: a value replaces the key, null clears
    it, omitted keeps it."""

    name: Name | None = None
    provider: Provider | None = None
    client_params: Settings | None = None
    api_key: ApiKey | None = None
    is_active: bool | None = None


class ConnectionResponse(BaseModel):
    id: UUID
    key: str
    name: str
    provider: str
    client_params: dict[str, Any]
    has_api_key: bool
    #: Last characters of the key; the key itself is never returned.
    api_key_hint: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ConnectionListResponse(BaseModel):
    data: list[ConnectionResponse]


class ModelCreate(Input):
    key: Key
    connection_id: UUID
    #: The provider's model name, e.g. "anthropic/claude-sonnet-4.5".
    model: ModelName
    name: Name
    #: Model settings passed to init_chat_model (temperature, max_tokens…).
    params: Settings = {}
    is_active: bool = True


class ModelUpdate(Input):
    connection_id: UUID | None = None
    model: ModelName | None = None
    name: Name | None = None
    params: Settings | None = None
    is_active: bool | None = None


class ModelResponse(BaseModel):
    id: UUID
    key: str
    connection_id: UUID
    model: str
    name: str
    params: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ModelListResponse(BaseModel):
    data: list[ModelResponse]


class AssignmentResponse(BaseModel):
    purpose: str
    description: str
    #: Tried in order: the first answers, the rest are fallbacks.
    model_ids: list[UUID]


class AssignmentListResponse(BaseModel):
    data: list[AssignmentResponse]


class AssignmentUpdate(Input):
    #: Empty means the purpose uses the environment configuration again.
    model_ids: list[UUID] = Field(max_length=10)


class ModelTestResponse(BaseModel):
    ok: bool
    #: The model's reply, or the error when the call failed.
    detail: str
