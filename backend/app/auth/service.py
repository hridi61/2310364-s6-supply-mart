from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.audit.service import client_ip, record
from app.auth.models import AuthSession, User
from app.auth.schemas import PasswordChange, ProfileUpdate, SignupIn
from app.catalog.models import utcnow
from app.config import settings
from app.security import (
    DUMMY_HASH, create_access_token, hash_password, hash_token, new_refresh_token, verify_password,
)


def as_utc(value: datetime | None) -> datetime | None:
    """ডেটাবেস থেকে tzinfo ছাড়া আসে; তুলনা করার আগে UTC চিহ্ন বসাই।"""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def signup(session: Session, request: Request, data: SignupIn) -> User:
    user = User(email=data.email, name=data.name, password_hash=hash_password(data.password), role="user")
    session.add(user)
    try:
        session.commit()
    except IntegrityError:  # unique email
        session.rollback()
        raise HTTPException(409, "This email is already registered")
    session.refresh(user)
    record(session, request, "signup", user=user)
    return user


def _new_session(session: Session, request: Request, user: User) -> tuple[AuthSession, str]:
    refresh = new_refresh_token()
    row = AuthSession(
        user_id=user.id,
        token_hash=hash_token(refresh),
        ip=client_ip(request),
        user_agent=(request.headers.get("user-agent") or "")[:300] or None,
        expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row, refresh


def login(session: Session, request: Request, email: str, password: str) -> tuple[User, str, int, str]:
    user = session.exec(select(User).where(User.email == email)).first()

    # অ্যাকাউন্ট লক থাকলে পাসওয়ার্ড দেখারও দরকার নেই
    if user and user.locked_until and as_utc(user.locked_until) > utcnow():
        record(session, request, "login_failed", user=user, detail="account locked")
        raise HTTPException(429, f"Too many failed attempts. Try again in {settings.lockout_minutes} minutes")

    ok = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if not user or not ok:
        detail = "unknown email" if not user else "wrong password"
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= settings.max_failed_logins:
                user.locked_until = utcnow() + timedelta(minutes=settings.lockout_minutes)
                user.failed_login_count = 0
                detail = "wrong password, account locked"
            session.add(user)
            session.commit()
        record(session, request, "login_failed", user=user, email=email, detail=detail)
        raise HTTPException(401, "Invalid email or password")  # দুই ক্ষেত্রেই একই বার্তা

    if user.is_banned:
        record(session, request, "login_failed", user=user, detail="banned user")
        raise HTTPException(403, f"Account banned: {user.ban_reason or 'no reason given'}")

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = utcnow()
    session.add(user)
    session.commit()

    _, refresh = _new_session(session, request, user)
    access, expires_in = create_access_token(user.id, user.role)
    record(session, request, "login", user=user)
    return user, access, expires_in, refresh


def refresh_session(session: Session, request: Request, token: str | None) -> tuple[User, str, int, str]:
    """refresh token ঘুরিয়ে (rotation) নতুন access token দেয়।"""
    unauth = HTTPException(401, "Session expired, please log in again")
    if not token:
        raise unauth
    digest = hash_token(token)
    row = session.exec(select(AuthSession).where(AuthSession.token_hash == digest)).first()

    if row is None:
        # পুরনো (ইতিমধ্যে ঘোরানো) token আবার এলে ধরে নিই চুরি হয়েছে → ওই session বন্ধ
        stolen = session.exec(select(AuthSession).where(AuthSession.prev_token_hash == digest)).first()
        age = (utcnow() - as_utc(stolen.last_used_at)).total_seconds() if stolen else 0
        if stolen and stolen.revoked_at is None and age > settings.reuse_grace_seconds:
            stolen.revoked_at = utcnow()
            session.add(stolen)
            session.commit()
            record(session, request, "token_reuse", user=session.get(User, stolen.user_id), detail="old refresh token reused")
        raise unauth

    if row.revoked_at is not None or as_utc(row.expires_at) <= utcnow():
        raise unauth
    user = session.get(User, row.user_id)
    if user is None or user.is_banned:
        row.revoked_at = utcnow()
        session.add(row)
        session.commit()
        raise unauth

    new_token = new_refresh_token()
    row.prev_token_hash = row.token_hash
    row.token_hash = hash_token(new_token)
    row.last_used_at = utcnow()
    row.ip = client_ip(request)
    session.add(row)
    session.commit()
    access, expires_in = create_access_token(user.id, user.role)
    return user, access, expires_in, new_token


def logout(session: Session, request: Request, token: str | None) -> None:
    if not token:
        return
    row = session.exec(select(AuthSession).where(AuthSession.token_hash == hash_token(token))).first()
    if row and row.revoked_at is None:
        row.revoked_at = utcnow()  # সার্ভারে session সত্যিই বাতিল
        session.add(row)
        session.commit()
        record(session, request, "logout", user=session.get(User, row.user_id))


def active_sessions(session: Session, user_id: int) -> list[AuthSession]:
    rows = session.exec(
        select(AuthSession)
        .where(AuthSession.user_id == user_id, col(AuthSession.revoked_at).is_(None))
        .order_by(col(AuthSession.last_used_at).desc())
    ).all()
    return [r for r in rows if as_utc(r.expires_at) > utcnow()]


def revoke_session(session: Session, request: Request, user: User, session_id: int) -> None:
    row = session.get(AuthSession, session_id)
    if row is None or row.user_id != user.id:  # অন্যের session-ও "নেই" বলে 404
        raise HTTPException(404, "Session not found")
    if row.revoked_at is None:
        row.revoked_at = utcnow()
        session.add(row)
        session.commit()
        record(session, request, "session_revoke", user=user, detail=f"session {row.id}")


def revoke_all(session: Session, user_id: int, except_hash: str | None = None) -> None:
    for row in active_sessions(session, user_id):
        if except_hash and row.token_hash == except_hash:
            continue
        row.revoked_at = utcnow()
        session.add(row)
    session.commit()


def update_profile(session: Session, user: User, data: ProfileUpdate) -> User:
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"] is None:
        raise HTTPException(422, "name cannot be null")
    for key, value in changes.items():
        setattr(user, key, value or None if key == "phone" else value)
    user.updated_at = utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def change_password(session: Session, request: Request, user: User, data: PasswordChange, current_token: str | None) -> None:
    if not verify_password(data.current_password, user.password_hash):
        record(session, request, "password_change_failed", user=user, detail="wrong current password")
        raise HTTPException(400, "Current password is incorrect")
    if data.new_password == data.current_password:
        raise HTTPException(400, "New password must be different")
    user.password_hash = hash_password(data.new_password)
    user.updated_at = utcnow()
    session.add(user)
    session.commit()
    # এই ডিভাইস বাদে বাকি সব session বন্ধ
    revoke_all(session, user.id, except_hash=hash_token(current_token) if current_token else None)
    record(session, request, "password_change", user=user)
