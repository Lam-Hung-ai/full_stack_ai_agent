"""Central error contract: `{"error": {code, message, details, request_id}}`.

Services raise `DomainError` (through `fail`); this module maps it and the
framework errors to HTTP. Responses never carry SQL, stack traces or tokens.
"""

import logging
from collections.abc import Mapping
from typing import NoReturn

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException
from starlette.middleware.base import RequestResponseEndpoint

from app.common.request_context import current_request_id

logger = logging.getLogger(__name__)

#: Integrity, check, exclusion and serialization failures the client can act on.
CONFLICT_SQLSTATES = {"23505", "23503", "23001", "23514", "23P01", "40P01", "40001"}


class DomainError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message
        #: Safe data that helps the frontend react; never internals.
        self.details = details


def fail(
    status: int, code: str, message: str | None = None, details: dict | None = None
) -> NoReturn:
    raise DomainError(status, code, message, details)


def error_response(
    status: int,
    code: str,
    *,
    message: str | None = None,
    details: dict | list | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    error: dict = {"code": code, "request_id": current_request_id()}
    if message is not None:
        error["message"] = message
    if details is not None:
        error["details"] = details
    return JSONResponse(
        {"error": error},
        status_code=status,
        headers=dict(headers) if headers else None,
    )


def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        errors = [
            {"location": list(error["loc"]), "type": error["type"]}
            for error in exc.errors()
        ]
        return error_response(422, "validation_error", details=errors)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        code = "not_found" if exc.status_code == 404 else "http_error"
        return error_response(exc.status_code, code, headers=exc.headers)

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return error_response(
            exc.status, exc.code, message=exc.message, details=exc.details
        )

    @app.exception_handler(DBAPIError)
    async def database_error(request: Request, exc: DBAPIError):
        if getattr(exc.orig, "sqlstate", None) in CONFLICT_SQLSTATES:
            return error_response(409, "data_conflict")
        raise exc

    # Unexpected errors are caught by middleware rather than
    # exception_handler(Exception): Starlette runs that handler outside
    # CORSMiddleware, so the 500 would lack CORS headers and the browser would
    # report a network failure. main.py installs this before CORS for that reason.
    @app.middleware("http")
    async def unhandled_error(request: Request, call_next: RequestResponseEndpoint):
        try:
            return await call_next(request)
        except Exception:
            # Method and path only: query strings and bodies may be sensitive.
            logger.exception(
                "Unhandled error on %s %s", request.method, request.url.path
            )
            return error_response(500, "internal_error")
