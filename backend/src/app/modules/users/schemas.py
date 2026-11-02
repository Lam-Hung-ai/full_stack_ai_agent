from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    email_verified: bool
    #: Shows the system administration pages (QD-34).
    is_superuser: bool
    avatar_url: str | None
    created_at: datetime
