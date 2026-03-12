"""Autonomous Pothole Intelligence System — FastAPI Application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.database import engine, Base
from app.utils.logging import setup_logging, get_logger
from sqlalchemy import text as sqlalchemy_text

# ── Structured logging ────────────────────────────────────────
setup_logging()
logger = get_logger("main")

# ── Socket.IO server ─────────────────────────────────────────
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    namespaces=["/dashboard-stream", "/admin-stream"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create tables on startup, cleanup on shutdown."""
    logger.info("starting_application")

    try:
        # Create PostGIS extension + tables if they don't exist
        async with engine.begin() as conn:
            await conn.execute(sqlalchemy_text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await conn.run_sync(Base.metadata.create_all)

        # Create default admin user if not exists
        from app.utils.auth import hash_password
        from app.models import AdminUser
        from app.database import async_session_factory
        from sqlalchemy import select

        async with async_session_factory() as session:
            result = await session.execute(
                select(AdminUser).where(AdminUser.email == settings.ADMIN_DEFAULT_EMAIL)
            )
            if result.scalar_one_or_none() is None:
                admin = AdminUser(
                    email=settings.ADMIN_DEFAULT_EMAIL,
                    name="System Admin",
                    role="SUPER_ADMIN",
                    password_hash=hash_password(settings.ADMIN_DEFAULT_PASSWORD),
                    status="ACTIVE",
                )
                session.add(admin)
                await session.commit()
                logger.info("default_admin_created", email=settings.ADMIN_DEFAULT_EMAIL)
    except Exception as e:
        logger.warning("startup_db_init_failed", error=str(e))

    yield

    logger.info("shutting_down_application")
    await engine.dispose()


# ── FastAPI app ───────────────────────────────────────────────
app = FastAPI(
    title="Pothole Intelligence System",
    description="Autonomous Pothole Detection, Complaint Filing, and Road Safety Platform",
    version="3.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prometheus metrics ────────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ── Import and mount routers ─────────────────────────────────
from app.routers import public, admin, mobile, dashboard  # noqa: E402

app.include_router(public.router, prefix="/api/public", tags=["Public"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(mobile.router, prefix="/api/mobile", tags=["Mobile"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

# ── Mount Socket.IO ──────────────────────────────────────────
sio_asgi = socketio.ASGIApp(sio)
app.mount("/socket.io", sio_asgi)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """System health check endpoint."""
    return {"status": "healthy", "service": "pothole-intelligence-system"}


# ── Socket.IO Event Handlers ─────────────────────────────────
@sio.on("connect", namespace="/dashboard-stream")
async def dashboard_connect(sid: str, environ: dict) -> None:
    logger.info("dashboard_client_connected", sid=sid)


@sio.on("disconnect", namespace="/dashboard-stream")
async def dashboard_disconnect(sid: str) -> None:
    logger.info("dashboard_client_disconnected", sid=sid)


@sio.on("connect", namespace="/admin-stream")
async def admin_connect(sid: str, environ: dict) -> None:
    logger.info("admin_client_connected", sid=sid)


@sio.on("disconnect", namespace="/admin-stream")
async def admin_disconnect(sid: str) -> None:
    logger.info("admin_client_disconnected", sid=sid)


async def broadcast_event(namespace: str, event: str, data: dict) -> None:
    """Broadcast an event to all connected clients on a namespace."""
    await sio.emit(event, data, namespace=namespace)
