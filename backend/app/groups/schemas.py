from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.auth.schemas import clean_email
from app.rbac_constants import GROUP_PERMS


def _check_perms(values: list[str]) -> list[str]:
    bad = [v for v in values if v not in GROUP_PERMS]
    if bad:
        raise ValueError(f"Unknown permission: {', '.join(bad)} (allowed: {', '.join(GROUP_PERMS)})")
    return sorted(set(values), key=GROUP_PERMS.index)


class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    description: str | None = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name is too short")
        return v


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)
    description: str | None = Field(default=None, max_length=200)


class MemberAdd(BaseModel):
    email: str = Field(max_length=254)
    permissions: list[str] = []

    _email = field_validator("email")(clean_email)
    _perms = field_validator("permissions")(_check_perms)


class MemberUpdate(BaseModel):
    permissions: list[str]

    _perms = field_validator("permissions")(_check_perms)


class MemberRead(BaseModel):
    user_id: int
    name: str
    email: str
    permissions: list[str]
    is_owner: bool = False


class GroupRead(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    owner_name: str
    member_count: int
    my_permissions: list[str]
    is_owner: bool
    created_at: datetime


class GroupDetail(GroupRead):
    members: list[MemberRead]
