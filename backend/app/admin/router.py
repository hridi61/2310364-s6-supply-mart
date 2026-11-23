from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request, Response, status

from app.admin import service
from app.admin.schemas import (
    ActivityRead, AdminUser, BanIn, BulkIdsIn, BulkUsersIn, GroupAdminRead, RoleIn, UserDetail,
)
from app.audit.models import AuditLog
from app.audit.service import record
from app.auth.models import User
from app.catalog import service as catalog
from app.catalog.models import Product
from app.catalog.schemas import ProductRead
from app.database import SessionDep
from app.rbac import P, require
from sqlmodel import col, select

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

StatsAdmin = Annotated[User, require(P.ADMIN_STATS)]
UsersReader = Annotated[User, require(P.ADMIN_USERS_READ)]
Banner = Annotated[User, require(P.ADMIN_USERS_BAN)]
RoleAdmin = Annotated[User, require(P.ADMIN_USERS_ROLE)]
Moderator = Annotated[User, require(P.ADMIN_CONTENT)]
LogReader = Annotated[User, require(P.ADMIN_ACTIVITY)]
Exporter = Annotated[User, require(P.ADMIN_EXPORT)]

Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]
Role = Annotated[Literal["user", "admin"] | None, Query()]
Status = Annotated[Literal["active", "banned"] | None, Query()]
MAX_EXPORT = 5000


@router.get("/stats")
def stats(session: SessionDep, _: StatsAdmin):
    return service.stats(session)


# ---------- ব্যবহারকারী ----------
@router.get("/users", response_model=list[AdminUser])
def list_users(
    response: Response, session: SessionDep, _: UsersReader,
    q: Annotated[str | None, Query(max_length=100)] = None, role: Role = None, status: Status = None,
    offset: Offset = 0, limit: Limit = 20,
):
    items, total = service.list_users(session, q, role, status, offset, limit)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/users/bulk")
def bulk_users(data: BulkUsersIn, request: Request, session: SessionDep, admin: Banner):
    return service.bulk_users(session, request, admin, data.action, data.ids, data.reason)


@router.get("/users/{user_id}", response_model=UserDetail)
def user_detail(user_id: int, session: SessionDep, _: UsersReader):
    return service.user_detail(session, user_id)


@router.post("/users/{user_id}/ban", response_model=AdminUser)
def ban(user_id: int, data: BanIn, request: Request, session: SessionDep, admin: Banner):
    return service.ban(session, request, admin, user_id, data.reason.strip())


@router.post("/users/{user_id}/unban", response_model=AdminUser)
def unban(user_id: int, request: Request, session: SessionDep, admin: Banner):
    return service.unban(session, request, admin, user_id)


@router.patch("/users/{user_id}/role", response_model=AdminUser)
def change_role(user_id: int, data: RoleIn, request: Request, session: SessionDep, admin: RoleAdmin):
    return service.change_role(session, request, admin, user_id, data.role)


@router.post("/users/{user_id}/revoke-sessions")
def revoke_sessions(user_id: int, request: Request, session: SessionDep, admin: Banner):
    return {"revoked": service.revoke_user_sessions(session, request, admin, user_id)}


# ---------- কনটেন্ট মডারেশন ----------
@router.get("/products", response_model=list[ProductRead])
def list_products(
    response: Response, session: SessionDep, _: Moderator,
    q: Annotated[str | None, Query(max_length=100)] = None, category: Annotated[str | None, Query(max_length=40)] = None,
    owner_id: int | None = None, group_id: int | None = None, offset: Offset = 0, limit: Limit = 20,
):
    items, total = catalog.list_products(session, q=q, category=category, owner_id=owner_id, group_id=group_id,
                                         offset=offset, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, request: Request, session: SessionDep, admin: Moderator):
    catalog.get_product(session, product_id)  # নেই হলে 404
    service.delete_products(session, request, admin, [product_id])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/products/bulk-delete")
def bulk_delete_products(data: BulkIdsIn, request: Request, session: SessionDep, admin: Moderator):
    return {"deleted": service.delete_products(session, request, admin, data.ids)}


@router.get("/groups", response_model=list[GroupAdminRead])
def list_groups(
    response: Response, session: SessionDep, _: Moderator,
    q: Annotated[str | None, Query(max_length=100)] = None, offset: Offset = 0, limit: Limit = 20,
):
    items, total = service.list_groups(session, q, offset, limit)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/groups/bulk-delete")
def bulk_delete_groups(data: BulkIdsIn, request: Request, session: SessionDep, admin: Moderator):
    return {"deleted": service.delete_groups(session, request, admin, data.ids)}


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, request: Request, session: SessionDep, admin: Moderator):
    if service.delete_groups(session, request, admin, [group_id]) == 0:
        from fastapi import HTTPException
        raise HTTPException(404, "Group not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- activity ও security ----------
@router.get("/activity", response_model=list[ActivityRead])
def activity(
    response: Response, session: SessionDep, _: LogReader,
    action: Annotated[str | None, Query(max_length=30)] = None, q: Annotated[str | None, Query(max_length=100)] = None,
    user_id: int | None = None, offset: Offset = 0, limit: Limit = 20,
):
    items, total = service.list_activity(session, action, q, user_id, offset, limit)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/security")
def security(session: SessionDep, _: LogReader, days: Annotated[int, Query(ge=1, le=30)] = 7):
    return service.security_overview(session, days)


# ---------- CSV export (ফিল্টার মেনে চলে) ----------
def _csv(name: str, text: str) -> Response:
    return Response(text, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})


@router.get("/export/users")
def export_users(
    request: Request, session: SessionDep, admin: Exporter,
    q: Annotated[str | None, Query(max_length=100)] = None, role: Role = None, status: Status = None,
):
    users = session.exec(service.users_query(q, role, status).order_by(col(User.id)).limit(MAX_EXPORT)).all()
    record(session, request, "export", user=admin, detail=f"users csv ({len(users)} rows)")
    return _csv("users", service.to_csv(
        ["id", "email", "name", "role", "banned", "ban_reason", "created_at", "last_login_at"],
        [[u.id, u.email, u.name, u.role, u.is_banned, u.ban_reason, u.created_at, u.last_login_at] for u in users]))


@router.get("/export/products")
def export_products(
    request: Request, session: SessionDep, admin: Exporter,
    q: Annotated[str | None, Query(max_length=100)] = None, category: Annotated[str | None, Query(max_length=40)] = None,
    owner_id: int | None = None, group_id: int | None = None,
):
    items, _ = catalog.list_products(session, q=q, category=category, owner_id=owner_id, group_id=group_id, limit=100)
    # list_products সর্বোচ্চ ১০০ দেয়; পাতা ধরে ধরে সব আনি
    all_items, offset = list(items), 100
    while len(all_items) < MAX_EXPORT:
        more, _ = catalog.list_products(session, q=q, category=category, owner_id=owner_id, group_id=group_id,
                                        offset=offset, limit=100)
        if not more:
            break
        all_items += more
        offset += 100
    record(session, request, "export", user=admin, detail=f"products csv ({len(all_items)} rows)")
    return _csv("products", service.to_csv(
        ["id", "name", "category", "unit", "price", "stock", "active", "owner", "group", "created_at"],
        [[p.id, p.name_bn, p.category_name_bn, p.unit, p.price, p.stock, p.is_active, p.owner_name, p.group_name,
          p.created_at] for p in all_items]))


@router.get("/export/activity")
def export_activity(
    request: Request, session: SessionDep, admin: Exporter,
    action: Annotated[str | None, Query(max_length=30)] = None, q: Annotated[str | None, Query(max_length=100)] = None,
    user_id: int | None = None,
):
    rows = session.exec(service.activity_query(action, q, user_id).order_by(col(AuditLog.id).desc()).limit(MAX_EXPORT)).all()
    record(session, request, "export", user=admin, detail=f"activity csv ({len(rows)} rows)")
    return _csv("activity", service.to_csv(
        ["id", "time", "action", "user_id", "email", "ip", "browser", "detail"],
        [[a.id, a.created_at, a.action, a.user_id, a.email, a.ip, a.user_agent, a.detail] for a in rows]))
