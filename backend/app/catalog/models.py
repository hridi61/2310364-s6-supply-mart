from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """UTC সময়, tzinfo ছাড়া (SQLite ও PostgreSQL দুটোতেই একইভাবে জমা হয়)।"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Category(SQLModel, table=True):
    __tablename__ = "category"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(max_length=40, unique=True, index=True)
    name_bn: str = Field(max_length=60)
    icon: str = Field(max_length=8)


class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: int | None = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    name_bn: str = Field(max_length=60)
    unit: str = Field(max_length=10)
    price: int  # পুরো টাকা (দশমিক নেই, তাই হিসাবে ভুল হয় না)
    stock: int = 0
    icon: str | None = Field(default=None, max_length=8)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)