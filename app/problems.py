from enum import StrEnum
from collections.abc import Mapping
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from http import HTTPStatus
from starlette.exceptions import HTTPException as StarletteHTTPException

_logger = logging.getLogger("ledgerline")

_LOCATION_SEGMENTS = {"body", "query", "path", "header", "cookie"}
_PROBLEM_BASE = "https://api.ledgerline.com/problems"


class ErrorCode(StrEnum):
    UNAUTHORIZED = "unauthorized"
    CUSTOMER_NOT_FOUND = "customer_not_found"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    INTERNAL_ERROR = "internal_error"


_HTTP_ERROR_CODES = {
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
}


class FieldErrorCode(StrEnum):
    REQUIRED = "required"
    UNKNOWN_FIELD = "unknown_field"
    INVALID_TYPE = "invalid_type"
    INVALID = "invalid"


_PYDANTIC_TO_FIELD_CODE: dict[str, FieldErrorCode] = {
    "missing": FieldErrorCode.REQUIRED,
    "extra_forbidden": FieldErrorCode.UNKNOWN_FIELD,
    "string_type": FieldErrorCode.INVALID_TYPE,
    "int_type": FieldErrorCode.INVALID_TYPE,
    "bool_type": FieldErrorCode.INVALID_TYPE,
}


def _field_code(pydantic_type: str) -> FieldErrorCode:
    return _PYDANTIC_TO_FIELD_CODE.get(pydantic_type, FieldErrorCode.INVALID)


def problem_type(slug: str) -> str:
    return f"{_PROBLEM_BASE}/{slug}"


class ProblemException(Exception):
    """An error to be rendered as an RFC 9457 application/problem+json response"""

    def __init__(
        self,
        *,
        status: int,
        title: str,
        code: ErrorCode,
        type_: str,
        detail: str | None = None,
        instance: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:

        self.status = status
        self.title = title
        self.code = code
        self.detail = detail
        self.instance = instance
        self.type = type_
        self.headers = headers


def render_problem(
    *,
    status: int,
    title: str,
    code: ErrorCode,
    detail: str | None = None,
    instance: str | None = None,
    type_: str = "about:blank",
    errors: list[dict] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:

    body: dict = {"type": type_, "title": title, "status": status, "code": code}

    if detail is not None:
        body["detail"] = detail
    if instance is not None:
        body["instance"] = instance
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content=body,
        headers=headers,
    )


def _field_from_loc(loc: tuple) -> str:
    parts = [str(p) for p in loc]
    if parts and parts[0] in _LOCATION_SEGMENTS:
        parts = parts[1:]
    return ".".join(parts) if parts else "(root)"


async def problem_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    assert isinstance(exc, ProblemException)

    return render_problem(
        status=exc.status,
        title=exc.title,
        code=exc.code,
        detail=exc.detail,
        instance=exc.instance,
        type_=exc.type,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:

    assert isinstance(exc, RequestValidationError)

    errors = [
        {
            "field": _field_from_loc(e["loc"]),
            "code": _field_code(e["type"]),
            "message": e["msg"],
        }
        for e in exc.errors()
    ]

    return render_problem(
        status=422,
        title="Unprocessable Entity",
        code=ErrorCode.VALIDATION_ERROR,
        detail="The request body failed validation.",
        type_=problem_type("validation-error"),
        errors=errors,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    assert isinstance(exc, StarletteHTTPException)

    return render_problem(
        status=exc.status_code,
        title=HTTPStatus(exc.status_code).phrase,
        code=_HTTP_ERROR_CODES[exc.status_code],
        headers=exc.headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    _logger.exception("Unhandled exception", exc_info=exc)

    return render_problem(
        status=500, title="Internal Server Error", code=ErrorCode.INTERNAL_ERROR
    )
