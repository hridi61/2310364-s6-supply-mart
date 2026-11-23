from datetime import datetime

from sqlmodel import Field, SQLModel

from app.catalog.models import utcnow


class User(SQLModel, table=True):
    __tablename__ = "app_user"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(max_length=254, unique=True, index=True)
    name: str = Field(max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    password_hash: str = Field(max_length=255)
    role: str = Field(default="user", max_length=10, index=True)  # "user" | "admin"
    is_banned: bool = False
    ban_reason: str | None = Field(default=None, max_length=300)
    banned_at: datetime | None = None
    failed_login_count: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class AuthSession(SQLModel, table=True):
    """একটা লগইন = একটা session (একটা ডিভাইস/ব্রাউজার)। refresh token এর hash এখানে।"""

    __tablename__ = "auth_session"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)
    token_hash: str = Field(max_length=64, unique=True, index=True)
    prev_token_hash: str | None = Field(default=None, max_length=64, index=True)  # reuse ধরার জন্য
    ip: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=utcnow)
    last_used_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime
    revoked_at: datetime | None = None
