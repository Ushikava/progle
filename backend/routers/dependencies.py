from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import AuthError
from db.models import User
from db.session import get_session
from repositories.users import UserRepo
from services.auth import decode_access_token

ACCESS_TOKEN_COOKIE = "access_token"

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_optional_user(
    session: SessionDep,
    access_token: Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE)] = None,
) -> User | None:
    claims = decode_access_token(access_token) if access_token else None
    if claims is None:
        return None
    user = await UserRepo(session).get_by_id(claims.user_id)
    if user is None or user.token_version != claims.version:
        return None
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_current_user(user: OptionalUser) -> User:
    if user is None:
        raise AuthError("Требуется вход через Discord")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
