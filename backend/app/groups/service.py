from fastapi import HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.audit.service import record
from app.auth.models import User
from app.catalog.models import Product
from app.groups.models import Group, GroupMember
from app.groups.schemas import GroupCreate, GroupDetail, GroupRead, GroupUpdate, MemberAdd, MemberRead, MemberUpdate
from app.rbac import group_permissions
from app.rbac_constants import GROUP_PERMS


def _read(session: Session, user: User, group: Group) -> GroupRead:
    owner = session.get(User, group.owner_id)
    members = session.exec(select(GroupMember).where(GroupMember.group_id == group.id)).all()
    return GroupRead(
        id=group.id, name=group.name, description=group.description, owner_id=group.owner_id,
        owner_name=owner.name if owner else "?", member_count=len(members) + 1,  # +১ = owner
        my_permissions=sorted(group_permissions(session, user, group)),
        is_owner=group.owner_id == user.id, created_at=group.created_at,
    )


def _member_for(session: Session, user: User, group_id: int) -> Group:
    """গ্রুপের সদস্য (বা owner) না হলে 404, অর্থাৎ বাইরের লোক গ্রুপ আছে কিনাও জানে না।"""
    group = session.get(Group, group_id)
    if group is None or (group.owner_id != user.id and not group_permissions_member(session, user, group)):
        raise HTTPException(404, "Group not found")
    return group


def group_permissions_member(session: Session, user: User, group: Group) -> bool:
    return session.exec(
        select(GroupMember).where(GroupMember.group_id == group.id, GroupMember.user_id == user.id)
    ).first() is not None


def _owner_only(group: Group, user: User) -> None:
    if group.owner_id != user.id:
        raise HTTPException(403, "Only the group owner can do this")


def create_group(session: Session, user: User, data: GroupCreate) -> GroupRead:
    group = Group(name=data.name, description=data.description, owner_id=user.id)
    session.add(group)
    session.commit()
    session.refresh(group)
    return _read(session, user, group)


def my_groups(session: Session, user: User) -> list[GroupRead]:
    member_ids = select(GroupMember.group_id).where(GroupMember.user_id == user.id)
    groups = session.exec(
        select(Group).where((Group.owner_id == user.id) | col(Group.id).in_(member_ids)).order_by(col(Group.id).desc())
    ).all()
    return [_read(session, user, g) for g in groups]


def detail(session: Session, user: User, group_id: int) -> GroupDetail:
    group = _member_for(session, user, group_id)
    owner = session.get(User, group.owner_id)
    rows = session.exec(
        select(GroupMember, User).join(User, GroupMember.user_id == User.id).where(GroupMember.group_id == group.id)
    ).all()
    members = [MemberRead(user_id=owner.id, name=owner.name, email=owner.email, permissions=list(GROUP_PERMS), is_owner=True)]
    members += [
        MemberRead(user_id=u.id, name=u.name, email=u.email, permissions=[p for p in m.permissions.split(",") if p])
        for m, u in rows
    ]
    return GroupDetail(**_read(session, user, group).model_dump(), members=members)


def update_group(session: Session, user: User, group_id: int, data: GroupUpdate) -> GroupRead:
    group = _member_for(session, user, group_id)
    _owner_only(group, user)  # নাম বদলানো শুধু owner
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "name" and value is None:
            raise HTTPException(422, "name cannot be null")
        setattr(group, key, value)
    session.add(group)
    session.commit()
    return _read(session, user, group)


def delete_group(session: Session, request: Request, user: User, group_id: int) -> None:
    group = _member_for(session, user, group_id)
    _owner_only(group, user)
    purge_group(session, group)
    record(session, request, "delete", user=user, detail=f"group {group.id}: {group.name}")


def purge_group(session: Session, group: Group) -> None:
    """গ্রুপ মোছে: পণ্যগুলো থাকে (মালিকের নামে), শুধু গ্রুপের সাথে সম্পর্ক কাটে।"""
    for product in session.exec(select(Product).where(Product.group_id == group.id)).all():
        product.group_id = None
        session.add(product)
    for member in session.exec(select(GroupMember).where(GroupMember.group_id == group.id)).all():
        session.delete(member)
    session.delete(group)
    session.commit()


def add_member(session: Session, user: User, group_id: int, data: MemberAdd) -> GroupDetail:
    group = _member_for(session, user, group_id)
    _owner_only(group, user)
    target = session.exec(select(User).where(User.email == data.email)).first()
    if target is None:
        raise HTTPException(404, "No user with this email")
    if target.id == group.owner_id:
        raise HTTPException(400, "The owner is already in the group")
    session.add(GroupMember(group_id=group.id, user_id=target.id, permissions=",".join(data.permissions)))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "This user is already a member")
    return detail(session, user, group_id)


def _member_row(session: Session, group: Group, target_id: int) -> GroupMember:
    row = session.exec(
        select(GroupMember).where(GroupMember.group_id == group.id, GroupMember.user_id == target_id)
    ).first()
    if row is None:
        raise HTTPException(404, "Member not found")
    return row


def update_member(session: Session, user: User, group_id: int, target_id: int, data: MemberUpdate) -> GroupDetail:
    group = _member_for(session, user, group_id)
    _owner_only(group, user)
    row = _member_row(session, group, target_id)
    row.permissions = ",".join(data.permissions)
    session.add(row)
    session.commit()
    return detail(session, user, group_id)


def remove_member(session: Session, user: User, group_id: int, target_id: int) -> None:
    group = _member_for(session, user, group_id)
    _owner_only(group, user)
    session.delete(_member_row(session, group, target_id))
    session.commit()
