import os
from os.path import dirname, join
from urllib.parse import urlsplit

from dotenv import load_dotenv

dotenv_path = join(dirname(dirname(__file__)), '.env')
load_dotenv(dotenv_path)

ALGORITHM = "HS256"
JWT_MIN_SECRET_LENGTH = 32

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.environ.get(
    "DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/discord/callback"
)

JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_EXPIRE_DAYS = int(os.environ.get("JWT_EXPIRE_DAYS", "30"))

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("CORS_ORIGINS", FRONTEND_URL).split(",")
    if origin.strip()
]
COOKIE_SECURE = (
    os.environ.get("COOKIE_SECURE", str(FRONTEND_URL.startswith("https://"))).lower() == "true"
)
API_DOCS = os.environ.get("API_DOCS", "false").lower() == "true"


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


TRUSTED_ORIGINS = frozenset({_origin(FRONTEND_URL), *CORS_ORIGINS})

REQUIRED = {
    "DATABASE_URL": DATABASE_URL,
    "DISCORD_CLIENT_ID": DISCORD_CLIENT_ID,
    "DISCORD_CLIENT_SECRET": DISCORD_CLIENT_SECRET,
    "JWT_SECRET": JWT_SECRET,
}


def check_settings() -> None:
    missing = [name for name, value in REQUIRED.items() if not value]
    if missing:
        raise RuntimeError(f"Не заданы переменные окружения: {', '.join(missing)}")

    problems = []
    if len(JWT_SECRET) < JWT_MIN_SECRET_LENGTH:
        problems.append(f"JWT_SECRET должен быть не короче {JWT_MIN_SECRET_LENGTH} символов")
    if "*" in CORS_ORIGINS:
        problems.append("CORS_ORIGINS не может содержать «*»: вместе с cookie это открывает API любому сайту")
    if FRONTEND_URL.startswith("https://") and not COOKIE_SECURE:
        problems.append("COOKIE_SECURE=false при https: cookie сессии уйдёт по незашифрованному соединению")
    if problems:
        raise RuntimeError("Небезопасные настройки: " + "; ".join(problems))
