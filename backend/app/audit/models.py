from datetime import datetime

from sqlmodel import Field, SQLModel

from app.catalog.models import utcnow


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="app_user.id", index=True)
    email: str | None = Field(default=None, max_length=254, index=True)
    action: str = Field(max_length=30, index=True)
    detail: str | None = Field(default=None, max_length=300)
    ip: str | None = Field(default=None, max_length=64, index=True)
    user_agent: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=utcnow, index=True)
