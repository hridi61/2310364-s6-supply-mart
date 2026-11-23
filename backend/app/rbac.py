"""একটাই RBAC মডিউল: endpoint-এ `require(P.…)`, গ্রুপের ভেতরে `group_permissions(…)`।"""
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.groups.models import Group, GroupMember
from app.rbac_constants import GROUP_PERMS, P, ROLE_PERMISSIONS  # noqa: F401


def require(permission: str):
    """endpoint-এর dependency: ব্যবহারকারীর role-এ এই অনুমতি না থাকলে 403।"""

    def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if permission not in ROLE_PERMISSIONS.get(user.role, set()):
            raise HTTPException(403, "Not enough permissions")
        return user

    return Depends(checker)


def group_permissions(session: Session, user: User, group: Group | None) -> set[str]:
    """এই গ্রুপে ব্যবহারকারীর অনুমতি: owner সব পায়, সদস্য শুধু যা দেওয়া হয়েছে।"""
    if group is None:
        return set()
    if group.owner_id == user.id:
        return set(GROUP_PERMS)
    member = session.exec(
        select(GroupMember).where(GroupMember.group_id == group.id, GroupMember.user_id == user.id)
    ).first()
    return {p for p in member.permissions.split(",") if p} if member else set()
