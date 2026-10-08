from datetime import datetime, timezone
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User
from app.schemas import AuthUserRead, LoginInput, SignUpInput
from app.services.auth import (
    SESSION_COOKIE,
    SESSION_LIFETIME,
    create_session,
    current_user_dependency,
    hash_password,
    profile_id_for_user,
    revoke_session,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def _set_session_cookie(response: Response, token: str) -> None:
    secure_setting = os.getenv("CAREERTWIN_COOKIE_SECURE")
    secure_cookie = (
        secure_setting.strip().lower() in {"1", "true", "yes"}
        if secure_setting is not None
        else os.getenv("CAREERTWIN_ENVIRONMENT", "development").strip().lower() == "production"
    )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )


def _safe_user(user: User, session: Session) -> AuthUserRead:
    return AuthUserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        profile_id=profile_id_for_user(session, user.id),
    )


@router.post("/signup", response_model=AuthUserRead, status_code=status.HTTP_201_CREATED)
def sign_up(data: SignUpInput, response: Response, session: Session = Depends(get_db)) -> AuthUserRead:
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        created_at=datetime.now(timezone.utc),
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from error
    session.refresh(user)
    _set_session_cookie(response, create_session(session, user))
    return _safe_user(user, session)


@router.post("/login", response_model=AuthUserRead)
def log_in(data: LoginInput, response: Response, session: Session = Depends(get_db)) -> AuthUserRead:
    user = session.scalar(select(User).where(User.email == data.email))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    _set_session_cookie(response, create_session(session, user))
    return _safe_user(user, session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def log_out(request: Request, response: Response, session: Session = Depends(get_db)) -> Response:
    revoke_session(session, request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(key=SESSION_COOKIE, httponly=True, samesite="lax", path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=AuthUserRead)
def me(user: User = Depends(current_user_dependency), session: Session = Depends(get_db)) -> AuthUserRead:
    return _safe_user(user, session)
