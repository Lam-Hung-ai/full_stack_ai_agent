from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    email_verified: bool
    avatar_url: str | None
    created_at: datetime
