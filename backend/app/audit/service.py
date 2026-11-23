from fastapi import Request
from sqlmodel import Session

from app.audit.models import AuditLog


def client_ip(request: Request) -> str:
    # Vercel proxy-র পেছনে থাকে, তাই আসল IP x-forwarded-for header-এ আসে
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def record(session: Session, request: Request, action: str, *, user=None, email: str | None = None, detail: str | None = None) -> None:
    """audit log-এ একটা সারি যোগ করে (কে, কী, কোন IP/browser থেকে, কখন)।"""
    session.add(
        AuditLog(
            user_id=user.id if user else None,
            email=email or (user.email if user else None),
            action=action,
            detail=(detail or "")[:300] or None,
            ip=client_ip(request),
            user_agent=(request.headers.get("user-agent") or "")[:300] or None,
        )
    )
    session.commit()
