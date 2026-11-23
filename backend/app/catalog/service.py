from typing import Literal

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.auth.models import User
from app.catalog.models import Category, Product, utcnow
from app.catalog.schemas import ProductCreate, ProductRead, ProductUpdate
from app.groups.models import Group
from app.rbac import group_permissions

STOCK_FIELDS = {"stock", "is_active"}  # "stock" অনুমতিওয়ালা সদস্য শুধু এগুলো বদলাতে পারে


# ---------- অনুমতির নিয়ম (এখানেই মালিকানা + গ্রুপ-অনুমতি) ----------
def _group_of(session: Session, product: Product) -> Group | None:
    return session.get(Group, product.group_id) if product.group_id else None


def can_update(session: Session, user: User, product: Product, fields: set[str]) -> bool:
    if product.owner_id == user.id:
        return True  # নিজের পণ্য
    perms = group_permissions(session, user, _group_of(session, product))
    if "update" in perms:
        return True
    return "stock" in perms and fields <= STOCK_FIELDS


def can_delete(session: Session, user: User, product: Product) -> bool:
    if product.owner_id == user.id:
        return True
    group = _group_of(session, product)
    return group is not None and group.owner_id == user.id  # গ্রুপের শুধু owner মুছতে পারে


# ---------- পড়া ----------
def _to_read(product: Product, category: Category, owner_name: str | None, group_name: str | None,
             can_edit: bool = False, can_del: bool = False, can_stock: bool = False) -> ProductRead:
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
        owner_id=product.owner_id,
        owner_name=owner_name,
        group_id=product.group_id,
        group_name=group_name,
        can_edit=can_edit,
        can_delete=can_del,
        can_stock=can_stock,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def _base_query():
    return (
        select(Product, Category, col(User.name), col(Group.name))
        .join(Category, Product.category_id == Category.id)
        .outerjoin(User, Product.owner_id == User.id)
        .outerjoin(Group, Product.group_id == Group.id)
    )


def _require_category(session: Session, category_id: int) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=422, detail="Category not found")
    return category


def list_categories(session: Session) -> list[Category]:
    return list(session.exec(select(Category).order_by(Category.id)).all())


def list_products(
    session: Session,
    *,
    category: str | None = None,
    q: str | None = None,
    sort: Literal["price_asc", "price_desc"] | None = None,
    group_id: int | None = None,
    owner_id: int | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[ProductRead], int]:
    """ফিল্টার, সার্চ, সাজানো ও pagination সহ পণ্যের তালিকা, আর মোট সংখ্যা।"""
    filters = []
    if category:
        filters.append(Category.slug == category)
    if q:
        filters.append(col(Product.name_bn).contains(q))
    if group_id is not None:
        filters.append(Product.group_id == group_id)
    if owner_id is not None:
        filters.append(Product.owner_id == owner_id)

    query = _base_query()
    count_query = select(func.count()).select_from(Product).join(Category, Product.category_id == Category.id)
    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    if sort == "price_asc":
        query = query.order_by(col(Product.price).asc(), col(Product.id).desc())
    elif sort == "price_desc":
        query = query.order_by(col(Product.price).desc(), col(Product.id).desc())
    else:
        query = query.order_by(col(Product.id).desc())  # সবচেয়ে নতুন আগে

    total = session.exec(count_query).one()
    rows = session.exec(query.offset(offset).limit(limit)).all()
    return [_to_read(p, c, on, gn) for p, c, on, gn in rows], total


def _get_row(session: Session, product_id: int):
    row = session.exec(_base_query().where(Product.id == product_id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return row


def get_product(session: Session, product_id: int, user: User | None = None) -> ProductRead:
    product, category, owner_name, group_name = _get_row(session, product_id)
    edit = delete = stock = False
    if user is not None:
        edit = can_update(session, user, product, {"name_bn"})  # পুরো সম্পাদনার অধিকার আছে কিনা
        delete = can_delete(session, user, product)
        stock = can_update(session, user, product, {"stock"})
    return _to_read(product, category, owner_name, group_name, edit, delete, stock)


# ---------- লেখা ----------
def create_product(session: Session, user: User, data: ProductCreate) -> ProductRead:
    category = _require_category(session, data.category_id)
    group = None
    if data.group_id is not None:
        group = session.get(Group, data.group_id)
        # গ্রুপ না থাকলে বা "create" অনুমতি না থাকলে একই 403 (গ্রুপ আছে কিনা জানানো হয় না)
        if group is None or "create" not in group_permissions(session, user, group):
            raise HTTPException(403, "You cannot add products to this group")
    product = Product(**data.model_dump(), owner_id=user.id)
    session.add(product)
    session.commit()
    session.refresh(product)
    return _to_read(product, category, user.name, group.name if group else None, True, True)


def update_product(session: Session, user: User, product_id: int, data: ProductUpdate) -> ProductRead:
    product, category, owner_name, group_name = _get_row(session, product_id)
    changes = data.model_dump(exclude_unset=True)  # শুধু যা পাঠানো হয়েছে
    if not can_update(session, user, product, set(changes)):
        raise HTTPException(403, "You are not allowed to change this product")

    if "category_id" in changes:
        category = _require_category(session, changes["category_id"])
    for field, value in changes.items():
        setattr(product, field, value)
    product.updated_at = utcnow()
    session.add(product)
    session.commit()
    session.refresh(product)
    return _to_read(product, category, owner_name, group_name, can_update(session, user, product, {"name_bn"}), can_delete(session, user, product), True)


def delete_product(session: Session, user: User, product_id: int) -> Product:
    product, *_ = _get_row(session, product_id)
    if not can_delete(session, user, product):
        raise HTTPException(403, "You are not allowed to delete this product")
    session.delete(product)
    session.commit()
    return product
