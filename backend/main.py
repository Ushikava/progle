from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.exceptions import AppError, app_error_handler
from core.security import security_middleware
from core.settings import API_DOCS, CORS_ORIGINS, check_settings
from core.words import load_dictionary, load_words
from db.models import Base
from db.session import engine
from routers.auth import router as auth_router
from routers.progle import router as progle_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_settings()
    load_words()
    load_dictionary()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Progle API",
    lifespan=lifespan,
    docs_url="/api/docs" if API_DOCS else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if API_DOCS else None,
)
app.add_exception_handler(AppError, app_error_handler)
app.middleware("http")(security_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(progle_router, prefix="/api")
