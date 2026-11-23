from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.auth.schemas import SessionRead, UserRead


class AdminUser(UserRead):
    ban_reason: str | None = None
    banned_at: datetime | None = None
    locked_until: datetime | None = None

    @classmethod
    def of(cls, user) -> "AdminUser":  # type: ignore[override]
        base = UserRead.of(user).model_dump()
        return cls(**base, ban_reason=user.ban_reason, banned_at=user.banned_at, locked_until=user.locked_until)


class BanIn(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


class RoleIn(BaseModel):
    role: Literal["user", "admin"]


class BulkUsersIn(BaseModel):
    action: Literal["ban", "unban"]
    ids: list[int] = Field(min_length=1, max_length=200)
    reason: str | None = Field(default=None, max_length=300)


class BulkIdsIn(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=200)


class ActivityRead(BaseModel):
    id: int
    user_id: int | None
    email: str | None
    action: str
    detail: str | None
    ip: str | None
    user_agent: str | None
    created_at: datetime


class GroupAdminRead(BaseModel):
    id: int
    name: str
    owner_id: int
    owner_name: str
    member_count: int
    product_count: int
    created_at: datetime


class UserDetail(BaseModel):
    user: AdminUser
    products: list[dict]
    groups: list[dict]
    sessions: list[SessionRead]
    activity: list[ActivityRead]
