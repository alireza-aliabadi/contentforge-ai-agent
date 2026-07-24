"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.api.routes import assets, auth, content, health, platforms
from backend.api.routes.auth import ensure_default_admin
from backend.core.config import get_settings
from backend.core.logging import setup_logging
from backend.core.rate_limit import limiter
from backend.core.telemetry import instrument_fastapi, setup_telemetry
from backend.db.session import Base, async_session_factory, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.debug)
    setup_telemetry(settings)
    if settings.app_env != "test":
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async with async_session_factory() as session:
                await ensure_default_admin(session)
        except Exception:
            logger.warning("Database unavailable during startup; skipping bootstrap", exc_info=True)
    logger.info("Application started")
    yield
    await engine.dispose()
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    prefix = settings.api_prefix
    app.include_router(health.router)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(assets.router, prefix=prefix)
    app.include_router(content.router, prefix=prefix)
    app.include_router(platforms.router, prefix=prefix)

    app.mount("/metrics", make_asgi_app())
    instrument_fastapi(app, settings)
    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",  # nosec B104
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
