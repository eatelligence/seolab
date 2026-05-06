"""Auth: bcrypt password hashing + JWT issue/verify."""

from __future__ import annotations

import datetime as dt
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
TOKEN_TTL_DAYS = 7


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(password, hashed)
    except Exception:
        return False


def make_token(user_id) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(days=TOKEN_TTL_DAYS)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    """Returns user_id (string) if token is valid, otherwise None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
