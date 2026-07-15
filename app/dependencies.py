from fastapi import Header, HTTPException


def require_api_key(authorization: str | None = Header(default=None)) -> bool:
    if authorization and authorization.startswith("Bearer ll_live_"):
        return True
    if authorization and authorization.startswith("Bearer ll_test_"):
        return False
    raise HTTPException(status_code=401, detail="No valid API key provided")
