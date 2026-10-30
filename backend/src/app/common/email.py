"""Outgoing email (backend AGENTS §19), after the pattern of hr-ai.

Modules write the letter; only `SMTPMailer` knows host, port and login.
Letters go out after the transaction commits, from a background task
(`deliver`), so a slow or failing mail server never holds a database
connection and never changes an answer: a request endpoint answers the same
whether an account exists or the letter could be sent.
"""

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Annotated, Protocol

from fastapi import Depends
from starlette.concurrency import run_in_threadpool

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class Letter:
    to: str
    subject: str
    body: str
    #: What the letter is for, for logs: never the address or the link.
    purpose: str


class EmailNotConfigured(RuntimeError):
    pass


class Mailer(Protocol):
    async def send(self, letter: Letter) -> None: ...


class SMTPMailer:
    async def send(self, letter: Letter) -> None:
        settings = get_settings()
        host = settings.smtp_host
        if not host:
            raise EmailNotConfigured("SMTP_HOST is not set")
        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = letter.to
        message["Subject"] = letter.subject
        message.set_content(letter.body)

        def send() -> None:
            with smtplib.SMTP(
                host, settings.smtp_port, timeout=SMTP_TIMEOUT_SECONDS
            ) as smtp:
                if settings.smtp_starttls:
                    smtp.starttls()
                if settings.smtp_username:
                    password = settings.smtp_password
                    smtp.login(
                        settings.smtp_username,
                        password.get_secret_value() if password else "",
                    )
                smtp.send_message(message)

        await run_in_threadpool(send)


def get_mailer() -> Mailer:
    return SMTPMailer()


MailerDep = Annotated[Mailer, Depends(get_mailer)]


async def deliver(mailer: Mailer, letter: Letter) -> None:
    """Send one letter from a background task; failures are logged, not raised."""
    try:
        await mailer.send(letter)
    except EmailNotConfigured:
        logger.warning("Email not configured; %s letter dropped", letter.purpose)
    except (OSError, smtplib.SMTPException):
        logger.warning("Could not send %s letter", letter.purpose, exc_info=True)
