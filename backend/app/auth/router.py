from typing import Annotated

from fastapi import APIRouter, Cookie, Request, Response, status

from app.auth import service
from app.auth.models import User
from app.auth.schemas import (
    LoginIn, PasswordChange, ProfileUpdate, SessionRead, SignupIn, TokenOut, UserRead,
)
from app.config import settings
from app.database import SessionDep
from app.rbac import P, require
from app.security import hash_token

router = APIRouter(prefix="/api/v1", tags=["auth"])
COOKIE = "refresh_token"
COOKIE_PATH = "/api/v1/auth"  # শুধু auth endpoint-এ cookie যায়


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE, token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,  # JavaScript পড়তে পারে না (XSS থেকে নিরাপদ)
        secure=settings.cookie_secure,
        samesite="strict",
        path=COOKIE_PATH,
    )


def _token_out(user, access: str, expires_in: int) -> TokenOut:
    return TokenOut(access_token=access, expires_in=expires_in, user=UserRead.of(user))


@router.post("/auth/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(data: SignupIn, request: Request, session: SessionDep):
    """নতুন অ্যাকাউন্ট (সবসময় role = user; admin শুধু seed স্ক্রিপ্ট/অ্যাডমিন বানাতে পারে)।"""
    return UserRead.of(service.signup(session, request, data))


@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, response: Response, session: SessionDep):
    user, access, expires_in, refresh = service.login(session, request, data.email, data.password)
    _set_cookie(response, refresh)
    return _token_out(user, access, expires_in)


@router.post("/auth/refresh", response_model=TokenOut)
def refresh(
    request: Request, response: Response, session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    user, access, expires_in, new_refresh = service.refresh_session(session, request, refresh_token)
    _set_cookie(response, new_refresh)
    return _token_out(user, access, expires_in)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request, session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    service.logout(session, request, refresh_token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
    return response


@router.get("/auth/sessions", response_model=list[SessionRead])
def my_sessions(
    session: SessionDep,
    user: Annotated[User, require(P.SESSION_MANAGE)],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    current = hash_token(refresh_token) if refresh_token else None
    return [
        SessionRead(
            id=s.id, ip=s.ip, user_agent=s.user_agent, created_at=s.created_at,
            last_used_at=s.last_used_at, expires_at=s.expires_at, current=s.token_hash == current,
        )
        for s in service.active_sessions(session, user.id)
    ]


@router.delete("/auth/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_my_session(
    session_id: int, request: Request, session: SessionDep,
    user: Annotated[User, require(P.SESSION_MANAGE)],
):
    service.revoke_session(session, request, user, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/me", response_model=UserRead)
def me(user: Annotated[User, require(P.PROFILE)]):
    return UserRead.of(user)


@router.patch("/users/me", response_model=UserRead)
def update_me(data: ProfileUpdate, session: SessionDep, user: Annotated[User, require(P.PROFILE)]):
    return UserRead.of(service.update_profile(session, user, data))


@router.post("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    data: PasswordChange, request: Request, session: SessionDep,
    user: Annotated[User, require(P.PROFILE)],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    service.change_password(session, request, user, data, refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
