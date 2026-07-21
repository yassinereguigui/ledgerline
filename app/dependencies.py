from fastapi import Header

from app.problems import ErrorCode, ProblemException, problem_type


def require_api_key(authorization: str | None = Header(default=None)) -> bool:
    if authorization and authorization.startswith("Bearer ll_live_"):
        return True
    if authorization and authorization.startswith("Bearer ll_test_"):
        return False
    raise ProblemException(
        status=401,
        title="Unauthorized",
        code=ErrorCode.UNAUTHORIZED,
        detail="No valid API key was provided. Include your key as 'Authorization: Bearer ll_test_...'.",
        type_=problem_type("unauthorized"),
        headers={"WWW-Authenticate": "Bearer"},
    )
