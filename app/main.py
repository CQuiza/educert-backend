"""Aplicación FastAPI."""

import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.rate_limit import limiter

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.core.settings import get_settings
from app.api.v1.router import api_router
from app.models import (  # noqa: F401 — registra metadatos
    Certificate,
    CertificateAudit,
    CertificateType,
    Course,
    CourseEnrollment,
    Lesson,
    LessonTask,
    Module,
    User,
    UserProgress,
    WorkerAudit,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def create_database_if_not_exists() -> None:
    """Crea la base de datos destino si no existe (solo para PostgreSQL)."""
    import re
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    settings = get_settings()
    db_url = settings.get_database_url()

    if not (db_url.startswith("postgresql") or db_url.startswith("postgres")):
        return

    # Parsear URL para conectarnos a la base de datos predeterminada 'postgres'
    match = re.match(r"^(postgresql(?:\+asyncpg)?://[^/]+/)([^?]+)(?:\?.*)?$", db_url)
    if not match:
        logger.warning("No se pudo parsear la URL de la base de datos para creación automática.")
        return

    base_url = match.group(1)
    db_name = match.group(2)

    postgres_url = f"{base_url}postgres"
    if postgres_url.startswith("postgresql://"):
        postgres_url = postgres_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql+asyncpg://", 1)

    temp_engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")
    try:
        async with temp_engine.connect() as conn:
            cleaned_db_name = re.sub(r"[^a-zA-Z0-9_]", "", db_name)
            if not cleaned_db_name:
                raise ValueError("El nombre de la base de datos es inválido.")

            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": cleaned_db_name}
            )
            exists = result.scalar()
            if not exists:
                logger.info("La base de datos '%s' no existe. Creando...", cleaned_db_name)
                await conn.execute(text(f'CREATE DATABASE "{cleaned_db_name}"'))
                logger.info("Base de datos '%s' creada exitosamente.", cleaned_db_name)
            else:
                logger.info("La base de datos '%s' ya existe.", cleaned_db_name)
    except Exception as e:
        logger.error("Error al verificar/crear la base de datos '%s': %s", db_name, e)
    finally:
        await temp_engine.dispose()


async def _seed_superuser() -> None:
    """Crea el superusuario inicial si no existe."""
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == settings.superuser_email)
        )
        if result.scalar_one_or_none() is not None:
            return

        superuser = User(
            email=settings.superuser_email,
            password_hash=get_password_hash(settings.superuser_password),
            name=settings.superuser_name,
            first_last_name=settings.superuser_first_last_name,
            role="superuser",
            identity_type=settings.superuser_identity_type,
            identity_number=settings.superuser_identity_number,
            phone_number=settings.superuser_phone_number,
            is_active=True,
        )
        session.add(superuser)
        await session.commit()
        logger.info("Superusuario '%s' creado.", settings.superuser_email)


async def _seed_system_bot() -> None:
    """Crea el usuario system bot si no existe."""
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == settings.system_bot_user_email)
        )
        if result.scalar_one_or_none() is not None:
            return

        bot = User(
            email=settings.system_bot_user_email,
            password_hash=get_password_hash(secrets.token_urlsafe(32)),
            name=settings.system_bot_user_name,
            first_last_name=settings.system_bot_user_first_last_name,
            role="superuser",
            identity_type="OTHER",
            identity_number=f"BOT-{settings.system_bot_user_email}",
            phone_number=f"+000{abs(hash(settings.system_bot_user_email)) % 10_000_000_000:010d}",
            is_active=True,
        )
        session.add(bot)
        await session.commit()
        logger.info("System bot '%s' creado.", settings.system_bot_user_email)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await create_database_if_not_exists()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_superuser()
    await _seed_system_bot()
    yield
    await engine.dispose()



settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    detail = str(exc.orig) if exc.orig else "Violación de restricción única"
    logger.warning("IntegrityError: %s", detail)
    return JSONResponse(
        status_code=409,
        content={"detail": "Ya existe un registro con ese valor"},
    )

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store"
    return response

app.include_router(api_router, prefix=settings.api_v1_prefix)

