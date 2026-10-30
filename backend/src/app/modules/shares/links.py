"""Share link tokens (database phase 1 §7.2).

A link is a bearer secret; the database keeps only its SHA-256. The token is
an HMAC of the share id, so the owner can be shown the same link again
without the raw token ever being stored (QD-28). Rotating the key changes
every link.
"""

import base64
import hashlib
import hmac
from uuid import UUID

from app.config.security import digest
from app.config.settings import get_settings

_DOMAIN = b"share-link:"


def link_token(share_id: UUID) -> str:
    key = get_settings().jwt_secret.get_secret_value().encode()
    mac = hmac.new(key, _DOMAIN + share_id.bytes, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).rstrip(b"=").decode()


def link_token_hash(share_id: UUID) -> str:
    return digest(link_token(share_id))


def share_url(share_id: UUID) -> str:
    return f"{get_settings().frontend_url}/s/{link_token(share_id)}"
