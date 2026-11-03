"""Letters the backend sends, caught instead of reaching an SMTP server."""

import re

import pytest

_TOKEN = re.compile(r"token=([A-Za-z0-9_-]+)")


class Mailbox(list):
    def token(self, purpose: str, to: str | None = None) -> str:
        """The link token of the latest letter for `purpose` (and address)."""
        for letter in reversed(self):
            if letter.purpose == purpose and (to is None or letter.to == to):
                match = _TOKEN.search(letter.body)
                assert match, letter.body
                return match.group(1)
        raise AssertionError(f"no {purpose} letter")


@pytest.fixture
def mailbox(client):
    from app.common.email import get_mailer
    from app.main import app

    letters = Mailbox()

    class CaughtMailer:
        async def send(self, letter):
            letters.append(letter)

    app.dependency_overrides[get_mailer] = CaughtMailer
    yield letters
    app.dependency_overrides.pop(get_mailer, None)
