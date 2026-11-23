import csv
import io
from datetime import timedelta

from fastapi import HTTPException, Request
from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from app.admin.schemas import ActivityRead, AdminUser, GroupAdminRead, UserDetail
from app.audit.models import AuditLog
from app.audit.service import record
from app.auth.models import AuthSession, User
from app.auth.schemas import SessionRead
from app.auth.service import active_sessions, as_utc, revoke_all
from app.catalog.models import Product, utcnow
from app.groups.models import Group, GroupMember
from app.groups.service import purge_group


# ---------- পরিসংখ্যান ----------
def stats(session: Session) -> dict:
    week = utcnow() - timedelta(days=7)
    day = utcnow() - timedelta(days=1)

    def count(model, *conds) -> int:
        stmt = select(func.count()).select_from(model)
        for c in conds:
            stmt = stmt.where(c)
        return session.exec(stmt).one()

    return {
        "users": count(User),
        "admins": count(User, User.role == "admin"),
        "banned_users": count(User, col(User.is_banned).is_(True)),
        "products": count(Product),
        "groups": count(Group),
        "new_users_7d": count(User, User.created_at >= week),
        "new_products_7d": count(Product, Product.created_at >= week),
        "new_groups_7d": count(Group, Group.created_at >= week),
        "active_sessions": count(AuthSession, col(AuthSession.revoked_at).is_(None), AuthSession.expires_at > utcnow()),
        "failed_logins_24h": count(AuditLog, AuditLog.action == "login_failed", AuditLog.created_at >= day),
    }


# ---------- ব্যবহারকারী ----------
def users_query(q: str | None, role: str | None, status: str | None):
    stmt = select(User)
    if q:
        needle = q.strip().lower()
        stmt = stmt.where(or_(col(User.email).contains(needle), func.lower(User.name).contains(needle)))
    if role:
        stmt = stmt.where(User.role == role)
    if status == "banned":
        stmt = stmt.where(col(User.is_banned).is_(True))
    elif status == "active":
        stmt = stmt.where(col(User.is_banned).is_(False))
    return stmt


def list_users(session: Session, q, role, status, offset: int, limit: int) -> tuple[list[AdminUser], int]:
    stmt = users_query(q, role, status)
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = session.exec(stmt.order_by(col(User.id).desc()).offset(offset).limit(limit)).all()
    return [AdminUser.of(u) for u in rows], total


def _get_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    return user


def activity_read(a: AuditLog) -> ActivityRead:
    return ActivityRead(id=a.id, user_id=a.user_id, email=a.email, action=a.action, detail=a.detail,
                        ip=a.ip, user_agent=a.user_agent, created_at=a.created_at)


def user_detail(session: Session, user_id: int) -> UserDetail:
    user = _get_user(session, user_id)
    products = session.exec(select(Product).where(Product.owner_id == user.id).order_by(col(Product.id).desc()).limit(50)).all()
    owned = session.exec(select(Group).where(Group.owner_id == user.id)).all()
    member_of = session.exec(
        select(Group, GroupMember).join(GroupMember, GroupMember.group_id == Group.id).where(GroupMember.user_id == user.id)
    ).all()
    groups = [{"id": g.id, "name": g.name, "role": "owner", "permissions": "all"} for g in owned]
    groups += [{"id": g.id, "name": g.name, "role": "member", "permissions": m.permissions or "none"} for g, m in member_of]
    logs = session.exec(
        select(AuditLog).where(or_(AuditLog.user_id == user.id, AuditLog.email == user.email))
        .order_by(col(AuditLog.id).desc()).limit(20)
    ).all()
    return UserDetail(
        user=AdminUser.of(user),
        products=[{"id": p.id, "name_bn": p.name_bn, "price": p.price, "stock": p.stock} for p in products],
        groups=groups,
        sessions=[SessionRead(id=s.id, ip=s.ip, user_agent=s.user_agent, created_at=s.created_at,
                              last_used_at=s.last_used_at, expires_at=s.expires_at) for s in active_sessions(session, user.id)],
        activity=[activity_read(a) for a in logs],
    )


# ---------- নিরাপত্তার নিয়ম: এখানেই আটকানো হয় ----------
def ban_user(session: Session, request: Request, admin: User, target: User, reason: str) -> User:
    if target.role == "admin":  # নিজেকে বা অন্য অ্যাডমিনকে ban করা যায় না
        raise HTTPException(403, "Admins cannot be banned")
    target.is_banned = True
    target.ban_reason = reason
    target.banned_at = utcnow()
    session.add(target)
    session.commit()
    revoke_all(session, target.id)  # সব session বন্ধ
    record(session, request, "ban", user=admin, detail=f"banned {target.email}: {reason}")
    return target


def unban_user(session: Session, request: Request, admin: User, target: User) -> User:
    target.is_banned = False
    target.ban_reason = None
    target.banned_at = None
    session.add(target)
    session.commit()
    record(session, request, "unban", user=admin, detail=f"unbanned {target.email}")
    return target


def ban(session, request, admin, user_id: int, reason: str) -> AdminUser:
    return AdminUser.of(ban_user(session, request, admin, _get_user(session, user_id), reason))


def unban(session, request, admin, user_id: int) -> AdminUser:
    return AdminUser.of(unban_user(session, request, admin, _get_user(session, user_id)))


def change_role(session: Session, request: Request, admin: User, user_id: int, role: str) -> AdminUser:
    target = _get_user(session, user_id)
    if target.id == admin.id:  # নিজের role নিজে বদলানো যায় না
        raise HTTPException(403, "Admins cannot change their own role")
    if target.role != role:
        old, target.role, target.updated_at = target.role, role, utcnow()
        session.add(target)
        session.commit()
        record(session, request, "role_change", user=admin, detail=f"{target.email}: {old} -> {role}")
    return AdminUser.of(target)


def revoke_user_sessions(session: Session, request: Request, admin: User, user_id: int) -> int:
    target = _get_user(session, user_id)
    count = len(active_sessions(session, target.id))
    revoke_all(session, target.id)
    record(session, request, "session_revoke", user=admin, detail=f"revoked {count} sessions of {target.email}")
    return count


def bulk_users(session: Session, request: Request, admin: User, action: str, ids: list[int], reason: str | None) -> dict:
    if action == "ban" and (not reason or len(reason.strip()) < 3):
        raise HTTPException(422, "A reason is required to ban")
    done, skipped = [], []
    for target in session.exec(select(User).where(col(User.id).in_(ids))).all():
        try:
            if action == "ban":
                ban_user(session, request, admin, target, reason.strip())
            else:
                unban_user(session, request, admin, target)
            done.append(target.id)
        except HTTPException:
            skipped.append({"id": target.id, "reason": "admin account"})
    missing = sorted(set(ids) - set(done) - {s["id"] for s in skipped})
    skipped += [{"id": i, "reason": "not found"} for i in missing]
    return {"done": done, "skipped": skipped}


# ---------- কনটেন্ট ----------
def list_groups(session: Session, q: str | None, offset: int, limit: int) -> tuple[list[GroupAdminRead], int]:
    stmt = select(Group, col(User.name)).join(User, Group.owner_id == User.id)
    if q:
        stmt = stmt.where(func.lower(Group.name).contains(q.strip().lower()))
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = session.exec(stmt.order_by(col(Group.id).desc()).offset(offset).limit(limit)).all()
    out = []
    for g, owner_name in rows:
        members = session.exec(select(func.count()).select_from(GroupMember).where(GroupMember.group_id == g.id)).one()
        products = session.exec(select(func.count()).select_from(Product).where(Product.group_id == g.id)).one()
        out.append(GroupAdminRead(id=g.id, name=g.name, owner_id=g.owner_id, owner_name=owner_name,
                                  member_count=members + 1, product_count=products, created_at=g.created_at))
    return out, total


def delete_products(session: Session, request: Request, admin: User, ids: list[int]) -> int:
    rows = session.exec(select(Product).where(col(Product.id).in_(ids))).all()
    for p in rows:
        session.delete(p)
    session.commit()
    if rows:
        record(session, request, "delete", user=admin, detail=f"admin deleted products {[p.id for p in rows]}")
    return len(rows)


def delete_groups(session: Session, request: Request, admin: User, ids: list[int]) -> int:
    rows = session.exec(select(Group).where(col(Group.id).in_(ids))).all()
    names = [(g.id, g.name) for g in rows]
    for g in rows:
        purge_group(session, g)
    if names:
        record(session, request, "delete", user=admin, detail=f"admin deleted groups {names}")
    return len(names)


# ---------- activity ও security ----------
def activity_query(action: str | None, q: str | None, user_id: int | None):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if q:
        needle = q.strip().lower()
        stmt = stmt.where(or_(func.lower(AuditLog.email).contains(needle), col(AuditLog.ip).contains(needle),
                              func.lower(AuditLog.detail).contains(needle)))
    return stmt


def list_activity(session: Session, action, q, user_id, offset: int, limit: int) -> tuple[list[ActivityRead], int]:
    stmt = activity_query(action, q, user_id)
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = session.exec(stmt.order_by(col(AuditLog.id).desc()).offset(offset).limit(limit)).all()
    return [activity_read(a) for a in rows], total


def security_overview(session: Session, days: int) -> dict:
    since = utcnow() - timedelta(days=days)
    failed = (AuditLog.action == "login_failed", AuditLog.created_at >= since)
    by_ip = session.exec(
        select(AuditLog.ip, func.count(), func.count(func.distinct(AuditLog.email))).where(*failed)
        .group_by(AuditLog.ip).order_by(func.count().desc()).limit(10)
    ).all()
    by_account = session.exec(
        select(AuditLog.email, func.count(), func.max(AuditLog.created_at)).where(*failed, col(AuditLog.email).is_not(None))
        .group_by(AuditLog.email).order_by(func.count().desc()).limit(10)
    ).all()
    locked = [u for u in session.exec(select(User).where(col(User.locked_until).is_not(None))).all()
              if as_utc(u.locked_until) > utcnow()]
    return {
        "days": days,
        "by_ip": [{"ip": ip, "failures": n, "accounts": a} for ip, n, a in by_ip],
        "by_account": [{"email": e, "failures": n, "last_at": last} for e, n, last in by_account],
        "locked_accounts": [{"id": u.id, "email": u.email, "locked_until": u.locked_until} for u in locked],
    }


# ---------- CSV ----------
def _safe(value) -> str:
    """Excel-এ `=`, `+`, `-`, `@` দিয়ে শুরু হলে সূত্র হিসেবে চলে; আগে একটা ' বসিয়ে আটকাই।"""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def to_csv(header: list[str], rows: list[list]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow([_safe(c) for c in row])
    return "\ufeff" + buffer.getvalue()  # BOM: Excel-এ বাংলা ঠিকভাবে দেখায়
