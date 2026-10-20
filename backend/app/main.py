"""Project Campus — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
import logging
import math
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.schemas.health import HealthResponse

# Initialize structured logging
setup_logging()
logger = logging.getLogger("project_campus")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]"
    )
    # Seed initial roles and foundational curricula idempotently
    try:
        from app.core.database import AsyncSessionLocal
        from app.core.seed import seed_initial_data

        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)
    except Exception as exc:
        logger.warning(f"Initial seed execution deferred: {exc}")

    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Project Campus — Educational Learning & Assessment Platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Reverse Proxy Header Middleware (populates client IP from X-Forwarded-For securely)
app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts=settings.FORWARDED_ALLOW_IPS,
)


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively convert non-JSON-compliant values (e.g. NaN, Infinity) to string representations."""
    if isinstance(obj, float) and not math.isfinite(obj):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    return obj


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors, ensuring non-finite floats in inputs do not crash json serialization."""
    sanitized_errors = _sanitize_for_json(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": jsonable_encoder(sanitized_errors)},
    )


# Global Exception Handler (prevents leaking internal stack traces / secrets)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected server error occurred. Please try again later.",
        },
    )


# Direct Root Health Endpoint required by Milestone 1 specifications
@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Root Health Check",
)
async def root_health(request: Request) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
    )


# Mount API v1 Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
