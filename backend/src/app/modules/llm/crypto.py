"""API keys of LLM connections, encrypted with Fernet (QD-34).

The key comes from `LLM_ENCRYPTION_KEY`; the database keeps the token and the
last characters for display, never the key in clear.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import get_settings

HINT_LENGTH = 4


class EncryptionUnavailable(Exception):
    """`LLM_ENCRYPTION_KEY` is missing, malformed, or not the one that
    encrypted a stored key."""


def _fernet() -> Fernet:
    secret = get_settings().llm_encryption_key
    if secret is None:
        raise EncryptionUnavailable("LLM_ENCRYPTION_KEY is not set")
    try:
        return Fernet(secret.get_secret_value())
    except ValueError as error:
        raise EncryptionUnavailable("LLM_ENCRYPTION_KEY is not a Fernet key") from error


def encrypt(api_key: str) -> tuple[str, str]:
    """(ciphertext, hint) for a key; the hint is its last characters."""
    token = _fernet().encrypt(api_key.encode()).decode()
    return token, api_key[-HINT_LENGTH:]


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as error:
        raise EncryptionUnavailable(
            "a stored API key cannot be decrypted with LLM_ENCRYPTION_KEY"
        ) from error
