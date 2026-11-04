import secrets
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Response
from fastapi.responses import RedirectResponse

from core import settings
from core.exceptions import AuthError
from core.security import RateLimiter
from models.user import UserModel
from repositories.users import UserRepo
from routers.dependencies import ACCESS_TOKEN_COOKIE, CurrentUser, OptionalUser, SessionDep
from services.auth import (
    avatar_url,
    build_login_url,
    create_access_token,
    login_with_discord,
)

router = APIRouter(prefix="/auth", tags=["auth"])

STATE_COOKIE = "oauth_state"
STATE_COOKIE_PATH = "/api/auth"
STATE_MAX_AGE = 600
QUERY_MAX_LENGTH = 512

login_limiter = RateLimiter(max_requests=10, window_seconds=60)

QueryParam = Annotated[str | None, Query(max_length=QUERY_MAX_LENGTH)]


def _set_session_cookie(response: Response, name: str, value: str, max_age: int, path: str = "/"):
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        path=path,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


def _delete_session_cookie(response: Response, name: str, path: str = "/"):
    response.delete_cookie(
        name, path=path, httponly=True, secure=settings.COOKIE_SECURE, samesite="lax"
    )


@router.get("/discord/login", dependencies=[Depends(login_limiter)])
async def discord_login():
    state = secrets.token_urlsafe(32)
    response = RedirectResponse(build_login_url(state))
    _set_session_cookie(response, STATE_COOKIE, state, STATE_MAX_AGE, STATE_COOKIE_PATH)
    return response


@router.get("/discord/callback", dependencies=[Depends(login_limiter)])
async def discord_callback(
    session: SessionDep,
    code: QueryParam = None,
    state: QueryParam = None,
    error: QueryParam = None,
    saved_state: Annotated[str | None, Cookie(alias=STATE_COOKIE)] = None,
):
    if error or not code:
        return RedirectResponse(f"{settings.FRONTEND_URL}?auth_error=cancelled")
    if not state or not saved_state or not secrets.compare_digest(state.encode(), saved_state.encode()):
        raise AuthError("Неверный параметр state, начните вход заново")

    user = await login_with_discord(session, code)

    response = RedirectResponse(settings.FRONTEND_URL)
    _delete_session_cookie(response, STATE_COOKIE, STATE_COOKIE_PATH)
    _set_session_cookie(
        response,
        ACCESS_TOKEN_COOKIE,
        create_access_token(user),
        settings.JWT_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return response


@router.get("/me", response_model=UserModel)
async def me(user: CurrentUser):
    return UserModel(id=user.id, username=user.username, avatar_url=avatar_url(user))


@router.post("/logout", status_code=204)
async def logout(response: Response, session: SessionDep, user: OptionalUser):
    if user is not None:
        await UserRepo(session).revoke_tokens(user.id)
        await session.commit()
    _delete_session_cookie(response, ACCESS_TOKEN_COOKIE)
