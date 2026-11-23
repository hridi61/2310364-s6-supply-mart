import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.rbac_constants import ROLE_PERMISSIONS

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_RE.match(value):
        raise ValueError("Invalid email address")
    return value


def check_password(value: str) -> str:
    """৮-১২৮ অক্ষর, অন্তত একটা অক্ষর আর একটা সংখ্যা।"""
    if len(value) < 8 or len(value) > 128:
        raise ValueError("Password must be 8 to 128 characters")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("Password must contain a letter and a number")
    return value


class SignupIn(BaseModel):
    email: str = Field(max_length=254)
    name: str = Field(min_length=2, max_length=100)
    password: str

    _email = field_validator("email")(clean_email)
    _password = field_validator("password")(check_password)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name is too short")
        return v


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def lower(cls, v: str) -> str:
        return v.strip().lower()


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, pattern=r"^(01[3-9]\d{8})?$")


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str

    _new = field_validator("new_password")(check_password)


class UserRead(BaseModel):
    id: int
    email: str
    name: str
    phone: str | None
    role: str
    is_banned: bool
    created_at: datetime
    last_login_at: datetime | None
    permissions: list[str] = []

    @classmethod
    def of(cls, user) -> "UserRead":
        return cls(
            id=user.id, email=user.email, name=user.name, phone=user.phone, role=user.role,
            is_banned=user.is_banned, created_at=user.created_at, last_login_at=user.last_login_at,
            permissions=sorted(ROLE_PERMISSIONS.get(user.role, set())),
        )


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class SessionRead(BaseModel):
    id: int
    ip: str | None
    user_agent: str | None
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    current: bool = False
