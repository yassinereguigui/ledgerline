from fastapi import Header

from app.problems import ProblemException


def require_api_key(authorization: str | None = Header(default=None)) -> bool:
    if authorization and authorization.startswith("Bearer ll_live_"):
        return True
    if authorization and authorization.startswith("Bearer ll_test_"):
        return False
    raise ProblemException(
        status=401,
        title="Unauthorized",
        detail="No valid API key was provided. Include your key as 'Authorization: Bearer ll_test_...'.",
        type_="https://api.ledgerline.com/problems/unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )
