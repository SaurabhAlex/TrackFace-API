from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


# Dummy JWT settings (for demo only)
# In production, load from env vars / secret manager.
JWT_SECRET = "change-me-dummy-secret"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

# Default dummy user (credential)
DUMMY_USERNAME = "admin"
DUMMY_PASSWORD = "admin123"

security = HTTPBearer(auto_error=False)


def create_access_token(subject: str, expires_minutes: int = JWT_EXPIRE_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


async def get_current_subject(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    scheme = credentials.scheme.lower()
    if scheme != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme.",
        )

    try:
        payload = decode_token(credentials.credentials)
        subject = str(payload.get("sub"))
        if not subject:
            raise ValueError("Missing sub")
        return subject
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )

