"""Typed values exchanged with the object storage adapter."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PresignedRequest:
    url: str
    method: str
    expires_in: int
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ObjectHead:
    size_bytes: int
    content_type: str | None
    etag: str | None
    checksum_sha256: str | None
