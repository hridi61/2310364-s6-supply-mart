from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response, status

from app.catalog import service
from app.catalog.schemas import CategoryRead, ProductCreate, ProductRead, ProductUpdate
from app.database import SessionDep

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(session: SessionDep):
    """সব ক্যাটাগরির তালিকা।"""
    return service.list_categories(session)


@router.get("/products", response_model=list[ProductRead])
def list_products(
    response: Response,
    session: SessionDep,
    category: Annotated[str | None, Query(max_length=40, description="ক্যাটাগরির slug")] = None,
    q: Annotated[str | None, Query(max_length=100, description="নামে খোঁজা")] = None,
    sort: Annotated[Literal["price_asc", "price_desc"] | None, Query(description="দাম অনুযায়ী সাজানো")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """পণ্যের তালিকা। মোট সংখ্যা `X-Total-Count` header-এ আসে।"""
    items, total = service.list_products(
        session, category=category, q=q, sort=sort, offset=offset, limit=limit
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: SessionDep):
    """একটি পণ্যের বিস্তারিত।"""
    return service.get_product(session, product_id)


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, session: SessionDep):
    """নতুন পণ্য যোগ করে।"""
    return service.create_product(session, data)


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, data: ProductUpdate, session: SessionDep):
    """পণ্যের কিছু ঘর বদলায় (যা পাঠানো হবে শুধু সেটাই)।"""
    return service.update_product(session, product_id, data)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: SessionDep):
    """পণ্য মুছে ফেলে।"""
    service.delete_product(session, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)