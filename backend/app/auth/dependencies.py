from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.auth.models import User
from app.database import SessionDep
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)  # Swagger-এ "Authorize" বোতাম আসে
_UNAUTH = {"WWW-Authenticate": "Bearer"}


def _load_user(session: Session, payload: dict) -> User | None:
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        return None
    return session.get(User, user_id)


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: SessionDep,
) -> User:
    """প্রতিটি protected request-এ চলে: token যাচাই → ডেটাবেস থেকে user → ban দেখা।"""
    if creds is None:
        raise HTTPException(401, "Not authenticated", headers=_UNAUTH)
    payload = decode_access_token(creds.credentials)  # সই/মেয়াদ ভুল হলে 401
    user = _load_user(session, payload)
    if user is None:
        raise HTTPException(401, "Invalid token", headers=_UNAUTH)
    if user.is_banned:  # ban করলে পরের request-ই আটকে যায়, token-এর মেয়াদের জন্য অপেক্ষা নেই
        raise HTTPException(403, "Account banned")
    return user  # role ডেটাবেস থেকে আসে, তাই role বদলালে সাথে সাথে কার্যকর


def get_optional_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: SessionDep,
) -> User | None:
    """পাবলিক পেজে লগইন থাকলে user দেয়, না থাকলে None (পণ্যের বিস্তারিতে can_edit দেখানোর জন্য)।"""
    if creds is None:
        return None
    try:
        payload = decode_access_token(creds.credentials)
    except HTTPException:
        return None
    user = _load_user(session, payload)
    return None if user is None or user.is_banned else user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
