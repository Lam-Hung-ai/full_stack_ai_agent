"""Structured logging: JSON lines on servers, plain text on a dev machine.

Context goes in `extra={"fields": {...}}`: ids, statuses, counts. Never chat
content, tokens or personal data (backend AGENTS §20).
"""

import json
import logging
from datetime import UTC, datetime

from app.common.request_context import current_request_id
from app.config.settings import get_settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if request_id := current_request_id():
            entry["request_id"] = request_id
        entry.update(getattr(record, "fields", None) or {})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)s %(name)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        line = super().format(record)
        fields = getattr(record, "fields", None)
        if fields:
            line += " " + " ".join(f"{key}={value}" for key, value in fields.items())
        return line


def configure_logging() -> None:
    settings = get_settings()
    handler = logging.StreamHandler()
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level)
