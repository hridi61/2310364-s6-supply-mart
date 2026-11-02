from typing import Literal

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.catalog.models import Category, Product, utcnow
from app.catalog.schemas import ProductCreate, ProductRead, ProductUpdate


def _to_read(product: Product, category: Category) -> ProductRead:
    return ProductRead(
        id=product.id,
        name_bn=product.name_bn,
        category_id=category.id,
        category_slug=category.slug,
        category_name_bn=category.name_bn,
        unit=product.unit,
        price=product.price,
        stock=product.stock,
        icon=product.icon or category.icon,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def _require_category(session: Session, category_id: int) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=422, detail="Category not found")
    return category


def _get_row(session: Session, product_id: int) -> tuple[Product, Category]:
    row = session.exec(
        select(Product, Category)
        .join(Category, Product.category_id == Category.id)
        .where(Product.id == product_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return row


def list_categories(session: Session) -> list[Category]:
    return list(session.exec(select(Category).order_by(Category.id)).all())


def list_products(
    session: Session,
    *,
    category: str | None,
    q: str | None,
    sort: Literal["price_asc", "price_desc"] | None,
    offset: int,
    limit: int,
) -> tuple[list[ProductRead], int]:
    """ফিল্টার, সার্চ, সাজানো ও pagination সহ পণ্যের তালিকা, আর মোট সংখ্যা।"""
    query = select(Product, Category).join(Category, Product.category_id == Category.id)
    count_query = select(func.count()).select_from(Product).join(Category, Product.category_id == Category.id)

    if category:
        query = query.where(Category.slug == category)
        count_query = count_query.where(Category.slug == category)
    if q:
        query = query.where(col(Product.name_bn).contains(q))
        count_query = count_query.where(col(Product.name_bn).contains(q))

    if sort == "price_asc":
        query = query.order_by(col(Product.price).asc(), col(Product.id).desc())
    elif sort == "price_desc":
        query = query.order_by(col(Product.price).desc(), col(Product.id).desc())
    else:
        query = query.order_by(col(Product.id).desc())  # সবচেয়ে নতুন আগে

    total = session.exec(count_query).one()
    rows = session.exec(query.offset(offset).limit(limit)).all()
    return [_to_read(p, c) for p, c in rows], total


def get_product(session: Session, product_id: int) -> ProductRead:
    product, category = _get_row(session, product_id)
    return _to_read(product, category)


def create_product(session: Session, data: ProductCreate) -> ProductRead:
    category = _require_category(session, data.category_id)
    product = Product(**data.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return _to_read(product, category)


def update_product(session: Session, product_id: int, data: ProductUpdate) -> ProductRead:
    product, category = _get_row(session, product_id)
    changes = data.model_dump(exclude_unset=True)  # শুধু যা পাঠানো হয়েছে

    if "category_id" in changes:
        category = _require_category(session, changes["category_id"])

    for field, value in changes.items():
        setattr(product, field, value)
    product.updated_at = utcnow()

    session.add(product)
    session.commit()
    session.refresh(product)
    return _to_read(product, category)


def delete_product(session: Session, product_id: int) -> None:
    product, _ = _get_row(session, product_id)
    session.delete(product)
    session.commit()