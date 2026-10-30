"""Shared request primitives used by several modules."""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints


def _printable(value: str) -> str:
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("Name must not contain control characters")
    return value


#: Names also go into letter subjects and bodies: no control characters.
Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    AfterValidator(_printable),
]


def _password_complexity(value: str) -> str:
    has_mixed_case = any(c.islower() for c in value) and any(c.isupper() for c in value)
    has_number = any(c.isdigit() for c in value)
    has_special = any(not c.isalnum() for c in value)
    if not (has_mixed_case and has_number and has_special):
        raise ValueError(
            "Password must include uppercase, lowercase, number and special character"
        )
    return value


Password = Annotated[
    str,
    StringConstraints(min_length=8, max_length=256),
    AfterValidator(_password_complexity),
]


class Input(BaseModel):
    """Request body base: unknown fields are rejected, not silently dropped."""

    model_config = ConfigDict(extra="forbid")
