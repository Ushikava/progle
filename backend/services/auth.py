import re
from datetime import UTC, datetime, timedelta
from typing import NamedTuple
from urllib.parse import urlencode

import httpx
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from core import settings
from core.exceptions import ExternalServiceError
from db.models import User
from repositories.users import UserRepo

DISCORD_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
DISCORD_API_URL = "https://discord.com/api/v10"
DISCORD_CDN_URL = "https://cdn.discordapp.com"

DISCORD_ID_PATTERN = re.compile(r"\d{1,20}")
AVATAR_HASH_PATTERN = re.compile(r"(a_)?[0-9a-f]{32}")
USERNAME_MAX_LENGTH = 64


class TokenClaims(NamedTuple):
    user_id: int
    version: int


def build_login_url(state: str) -> str:
    params = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": state,
    }
    return f"{DISCORD_AUTHORIZE_URL}?{urlencode(params)}"


async def _fetch_discord_user(code: str) -> dict:
    try:
        async with httpx.AsyncClient(base_url=DISCORD_API_URL, timeout=10) as client:
            token_response = await client.post(
                "/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.DISCORD_REDIRECT_URI,
                },
                auth=(settings.DISCORD_CLIENT_ID, settings.DISCORD_CLIENT_SECRET),
            )
            if token_response.status_code != 200:
                raise ExternalServiceError("Discord не принял код авторизации")
            access_token = token_response.json().get("access_token")
            if not isinstance(access_token, str):
                raise ExternalServiceError("Discord не выдал токен доступа")

            user_response = await client.get(
                "/users/@me", headers={"Authorization": f"Bearer {access_token}"}
            )
            if user_response.status_code != 200:
                raise ExternalServiceError("Не удалось получить профиль Discord")
            return user_response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ExternalServiceError("Discord недоступен, попробуйте позже") from exc


def _parse_discord_user(data: dict) -> tuple[str, str, str | None]:
    discord_id = data.get("id")
    username = data.get("global_name") or data.get("username")
    avatar = data.get("avatar")
    if not isinstance(discord_id, str) or not DISCORD_ID_PATTERN.fullmatch(discord_id):
        raise ExternalServiceError("Discord вернул некорректный профиль")
    if not isinstance(username, str) or not username.strip():
        raise ExternalServiceError("Discord вернул некорректный профиль")
    if not isinstance(avatar, str) or not AVATAR_HASH_PATTERN.fullmatch(avatar):
        avatar = None
    return discord_id, username.strip()[:USERNAME_MAX_LENGTH], avatar


async def login_with_discord(session: AsyncSession, code: str) -> User:
    discord_id, username, avatar = _parse_discord_user(await _fetch_discord_user(code))
    user = await UserRepo(session).upsert(discord_id=discord_id, username=username, avatar=avatar)
    await session.commit()
    return user


def create_access_token(user: User) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "ver": user.token_version,
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> TokenClaims | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            options={"require": ["sub", "ver", "exp"]},
        )
        return TokenClaims(user_id=int(payload["sub"]), version=int(payload["ver"]))
    except (jwt.PyJWTError, TypeError, ValueError):
        return None


def avatar_url(user: User) -> str:
    if user.avatar:
        return f"{DISCORD_CDN_URL}/avatars/{user.discord_id}/{user.avatar}.png"
    return f"{DISCORD_CDN_URL}/embed/avatars/{(int(user.discord_id) >> 22) % 6}.png"
