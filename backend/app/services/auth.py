from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import AuthSession, StudentProfile, User

SESSION_COOKIE = "careertwin_session"
SESSION_LIFETIME = timedelta(days=14)
_SCRYPT_N = 2**14


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=8, p=1, dklen=64)
    return "$scrypt$n=16384,r=8,p=1$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, parameters, salt_text, digest_text = encoded.split("$", 4)[1:]
        if algorithm != "scrypt" or parameters != "n=16384,r=8,p=1":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=8, p=1, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def create_session(session: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    session.add(AuthSession(
        user_id=user.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        created_at=now,
        expires_at=now + SESSION_LIFETIME,
    ))
    session.commit()
    return token


def revoke_session(session: Session, token: str | None) -> None:
    if not token:
        return
    record = session.scalar(select(AuthSession).where(AuthSession.token_hash == hashlib.sha256(token.encode()).hexdigest()))
    if record is not None:
        session.delete(record)
        session.commit()


def current_user_for_token(session: Session, token: str | None) -> User | None:
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    record = session.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash))
    if record is None:
        return None
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        session.delete(record)
        session.commit()
        return None
    return session.get(User, record.user_id)


def get_current_user(request: Request, session: Session) -> User:
    user = current_user_for_token(session, request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.")
    return user


def current_user_dependency(request: Request, session: Session = Depends(get_db)) -> User:
    return get_current_user(request, session)


def profile_id_for_user(session: Session, user_id: int) -> int | None:
    profile = session.scalar(select(StudentProfile.id).where(StudentProfile.user_id == user_id))
    return profile
