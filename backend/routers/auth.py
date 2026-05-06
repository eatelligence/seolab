import datetime as dt
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models.user import User
from schemas.auth import ChangePasswordRequest, LoginRequest
from schemas.common import ok
from services.auth import hash_password, make_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
log = logging.getLogger(__name__)


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = res.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        # Generic message: don't disclose which one is wrong.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    user.last_login_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()

    token = make_token(user.id)
    return ok({
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": str(user.id), "email": user.email, "is_admin": user.is_admin},
    })


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return ok({"id": str(user.id), "email": user.email, "is_admin": user.is_admin})


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is wrong")
    if payload.current_password == payload.new_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "New password must differ from current")
    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return ok({"changed": True})


@router.post("/logout")
async def logout(_: User = Depends(get_current_user)):
    # JWTs are stateless. The client is expected to drop the token; we just
    # acknowledge so the UI can clear localStorage.
    return ok({"logged_out": True})
