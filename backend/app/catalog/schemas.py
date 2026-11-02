from datetime import datetime, timezone
from typing import Literal

from pydantic import field_validator, model_validator
from sqlmodel import Field, SQLModel

Unit = Literal["kg", "litre", "dozen", "piece"]


def _strip(value):
    """নাম ও icon-এর শুরু-শেষের ফাঁকা জায়গা কেটে দেয় ("   " যেন নাম না হয়)।"""
    return value.strip() if isinstance(value, str) else value


class CategoryRead(SQLModel):
    id: int
    slug: str
    name_bn: str
    icon: str


class ProductBase(SQLModel):
    name_bn: str = Field(min_length=2, max_length=60)
    category_id: int
    unit: Unit
    price: int = Field(ge=1, le=100000)
    stock: int = Field(ge=0, le=10000)
    icon: str | None = Field(default=None, max_length=8)

    @field_validator("name_bn", "icon", mode="before")
    @classmethod
    def strip_text(cls, value):
        return _strip(value)

    @field_validator("icon")
    @classmethod
    def empty_icon_is_none(cls, value):
        return value or None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    """PATCH-এর body: যে ঘরগুলো পাঠানো হবে শুধু সেগুলো বদলাবে।"""

    name_bn: str | None = Field(default=None, min_length=2, max_length=60)
    category_id: int | None = None
    unit: Unit | None = None
    price: int | None = Field(default=None, ge=1, le=100000)
    stock: int | None = Field(default=None, ge=0, le=10000)
    icon: str | None = Field(default=None, max_length=8)
    is_active: bool | None = None

    @field_validator("name_bn", "icon", mode="before")
    @classmethod
    def strip_text(cls, value):
        return _strip(value)

    @field_validator("icon")
    @classmethod
    def empty_icon_is_none(cls, value):
        return value or None

    @model_validator(mode="after")
    def no_null_for_required_fields(self):
        # শুধু icon খালি (null) করা যায়; বাকিগুলোতে null পাঠানো ভুল
        for name in self.model_fields_set:
            if name != "icon" and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class ProductRead(SQLModel):
    id: int
    name_bn: str
    category_id: int
    category_slug: str
    category_name_bn: str
    unit: str
    price: int
    stock: int
    icon: str  # নিজের icon না থাকলে ক্যাটাগরির icon
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        # ডেটাবেসে tzinfo ছাড়া জমা থাকে; response-এ UTC চিহ্ন দেওয়া হয়
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value