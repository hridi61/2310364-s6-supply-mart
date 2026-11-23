from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request, Response, status

from app.audit.service import record
from app.auth.dependencies import OptionalUser
from app.auth.models import User
from app.catalog import service
from app.catalog.schemas import CategoryRead, ProductCreate, ProductRead, ProductUpdate
from app.database import SessionDep
from app.rbac import P, require

router = APIRouter(prefix="/api/v1", tags=["catalog"])

Writer = Annotated[User, require(P.PRODUCT_WRITE)]


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(session: SessionDep):
    """সব ক্যাটাগরির তালিকা (পাবলিক)।"""
    return service.list_categories(session)


@router.get("/products", response_model=list[ProductRead])
def list_products(
    response: Response,
    session: SessionDep,
    category: Annotated[str | None, Query(max_length=40, description="ক্যাটাগরির slug")] = None,
    q: Annotated[str | None, Query(max_length=100, description="নামে খোঁজা")] = None,
    sort: Annotated[Literal["price_asc", "price_desc"] | None, Query(description="দাম অনুযায়ী সাজানো")] = None,
    group_id: Annotated[int | None, Query(description="একটি গ্রুপের পণ্য")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """পণ্যের তালিকা (পাবলিক)। মোট সংখ্যা `X-Total-Count` header-এ আসে।"""
    items, total = service.list_products(
        session, category=category, q=q, sort=sort, group_id=group_id, offset=offset, limit=limit
    )
    response.headers["X-Total-Count"] = str(total)
    return items


# "/products/mine" অবশ্যই "/products/{id}"-এর আগে থাকবে, নইলে "mine" সংখ্যা ভেবে 422 দেবে
@router.get("/products/mine", response_model=list[ProductRead])
def my_products(
    response: Response,
    session: SessionDep,
    user: Writer,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """শুধু আমার নিজের পণ্য।"""
    items, total = service.list_products(session, owner_id=user.id, offset=offset, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: SessionDep, user: OptionalUser):
    """একটি পণ্যের বিস্তারিত (পাবলিক; লগইন থাকলে can_edit/can_delete আসে)।"""
    return service.get_product(session, product_id, user)


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, session: SessionDep, user: Writer):
    """নতুন পণ্য। মালিক = যে বানাচ্ছে। group_id দিলে গ্রুপের `create` অনুমতি লাগে।"""
    return service.create_product(session, user, data)


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, data: ProductUpdate, session: SessionDep, user: Writer):
    """পণ্যের কিছু ঘর বদলায়। মালিক, অথবা গ্রুপে `update` (বা শুধু স্টকের জন্য `stock`) অনুমতিওয়ালা সদস্য।"""
    return service.update_product(session, user, product_id, data)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, request: Request, session: SessionDep, user: Writer):
    """পণ্য মোছা: শুধু মালিক বা গ্রুপের owner।"""
    product = service.delete_product(session, user, product_id)
    record(session, request, "delete", user=user, detail=f"product {product.id}: {product.name_bn}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
