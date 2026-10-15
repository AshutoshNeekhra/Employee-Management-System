"""Minimal signed-token authentication for a single admin (bonus feature).

Credentials come from ADMIN_USERNAME / ADMIN_PASSWORD; tokens are HMAC-SHA256
signed and expire after TOKEN_TTL_SECONDS. No external dependencies.
"""
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "28800"))

bearer = HTTPBearer(auto_error=False)


def _sign(payload: str) -> str:
    return hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_token(username: str) -> str:
    body = json.dumps({"sub": username, "exp": int(time.time()) + TOKEN_TTL_SECONDS})
    payload = base64.urlsafe_b64encode(body.encode()).decode()
    return f"{payload}.{_sign(payload)}"


def verify_token(token: str) -> Optional[str]:
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(payload)):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload.encode()))
        if data["exp"] < time.time():
            return None
        return data["sub"]
    except Exception:
        return None


def authenticate(username: str, password: str) -> bool:
    return hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD)


def require_auth(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> str:
    user = verify_token(creds.credentials) if creds else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
