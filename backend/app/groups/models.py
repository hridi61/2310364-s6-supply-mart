from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.catalog.models import utcnow


class Group(SQLModel, table=True):
    """দোকান-টিম: একজন owner, আর সদস্যদের আলাদা আলাদা অনুমতি।"""

    __tablename__ = "shop_group"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=60)
    description: str | None = Field(default=None, max_length=200)
    owner_id: int = Field(foreign_key="app_user.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)


class GroupMember(SQLModel, table=True):
    __tablename__ = "group_member"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="shop_group.id", index=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)
    permissions: str = Field(default="", max_length=60)  # কমা দিয়ে: "create,update,stock"
