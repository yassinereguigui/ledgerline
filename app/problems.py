from fastapi import Request
from fastapi.responses import JSONResponse


class ProblemException(Exception):
    """An error to be rendered as an RFC 9457 application/problem+json response"""

    def __init__(
        self,
        status: int,
        title: str,
        detail: str | None = None,
        instance: str | None = None,
        type_: str = "about:blank",
        headers: dict[str, str] | None = None,
    ) -> None:

        self.status = status
        self.title = title
        self.detail = detail
        self.instance = instance
        self.type = type_
        self.headers = headers


async def problem_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    assert isinstance(exc, ProblemException)

    body: dict = {"type": exc.type, "title": exc.title, "status": exc.status}

    if exc.detail is not None:
        body["detail"] = exc.detail

    if exc.instance is not None:
        body["instance"] = exc.instance

    return JSONResponse(
        status_code=exc.status,
        media_type="application/problem+json",
        content=body,
        headers=exc.headers,
    )
