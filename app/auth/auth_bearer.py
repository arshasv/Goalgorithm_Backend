from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.auth_service import decode_access_token


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=False)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        try:
            credentials = await super().__call__(request)
        except Exception:
            raise HTTPException(status_code=401, detail="Not authenticated")

        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if not credentials.scheme.lower() == "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme. Expected Bearer token")
        payload = decode_access_token(credentials.credentials)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return payload


security = JWTBearer()
