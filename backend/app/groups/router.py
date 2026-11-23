from typing import Annotated

from fastapi import APIRouter, Request, Response, status

from app.auth.models import User
from app.database import SessionDep
from app.groups import service
from app.groups.schemas import GroupCreate, GroupDetail, GroupRead, GroupUpdate, MemberAdd, MemberUpdate
from app.rbac import P, require

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])

# গ্রুপ বানানো ও দেখার জন্য গ্লোবাল অনুমতি; ভেতরের কাজ (সদস্য, নাম, মোছা) owner-only নিয়মে service-এ আটকানো
Member = Annotated[User, require(P.GROUP_CREATE)]


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(data: GroupCreate, session: SessionDep, user: Member):
    return service.create_group(session, user, data)


@router.get("", response_model=list[GroupRead])
def my_groups(session: SessionDep, user: Member):
    """আমার গ্রুপ (যেগুলোর owner অথবা সদস্য)।"""
    return service.my_groups(session, user)


@router.get("/{group_id}", response_model=GroupDetail)
def get_group(group_id: int, session: SessionDep, user: Member):
    return service.detail(session, user, group_id)


@router.patch("/{group_id}", response_model=GroupRead)
def update_group(group_id: int, data: GroupUpdate, session: SessionDep, user: Member):
    return service.update_group(session, user, group_id, data)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, request: Request, session: SessionDep, user: Member):
    service.delete_group(session, request, user, group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/members", response_model=GroupDetail, status_code=status.HTTP_201_CREATED)
def add_member(group_id: int, data: MemberAdd, session: SessionDep, user: Member):
    return service.add_member(session, user, group_id, data)


@router.patch("/{group_id}/members/{user_id}", response_model=GroupDetail)
def update_member(group_id: int, user_id: int, data: MemberUpdate, session: SessionDep, user: Member):
    return service.update_member(session, user, group_id, user_id, data)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(group_id: int, user_id: int, session: SessionDep, user: Member):
    service.remove_member(session, user, group_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
