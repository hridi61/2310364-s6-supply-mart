"""পাসওয়ার্ড hash, JWT তৈরি/যাচাই, refresh token — সব নিরাপত্তার যন্ত্রপাতি এখানে।"""
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config import settings

_hasher = PasswordHash((Argon2Hasher(),))


def _peppered(password: str) -> str:
    # pepper: সার্ভারের গোপন লেখা মিশিয়ে নিই, যাতে শুধু ডেটাবেস চুরি হলে পাসওয়ার্ড ভাঙা না যায়
    return hmac.new(settings.pepper.encode(), password.encode(), hashlib.sha256).hexdigest()


def hash_password(password: str) -> str:
    return _hasher.hash(_peppered(password))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(_peppered(password), password_hash)
    except Exception:
        return False


# ইমেইল নেই এমন লগইনেও একই সময় লাগানোর জন্য (timing থেকে ইমেইল চেনা যেন না যায়)
DUMMY_HASH = hash_password("dummy-password-for-constant-time")


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    minutes = settings.access_token_minutes
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256"), minutes * 60


def decode_access_token(token: str) -> dict:
    """সই, মেয়াদ ও দরকারি ঘর যাচাই করে। ভুল হলে 401।"""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],  # algorithm আগে থেকে ঠিক করা, token-এর header বিশ্বাস করা হয় না
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired", headers={"WWW-Authenticate": "Bearer"})
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token", headers={"WWW-Authenticate": "Bearer"})


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    # ডেটাবেসে refresh token-এর hash থাকে, আসল token না
    return hashlib.sha256(token.encode()).hexdigest()
