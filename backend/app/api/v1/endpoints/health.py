"""Health Check API Endpoint."""

from fastapi import APIRouter, Query, Response, status
from app.core.config import settings
from app.core.database import check_database_connectivity
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Health Check",
    description="Check the operational status of the Project Campus backend.",
)
async def get_health(
    response: Response,
    check_db: bool = Query(
        False, description="Genuinely test database connectivity"
    ),
) -> HealthResponse:
    """Returns application health and optionally verifies real database connectivity."""
    db_status = None

    if check_db:
        is_connected = await check_database_connectivity()
        if is_connected:
            db_status = "connected"
        else:
            db_status = "unavailable"
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return HealthResponse(
                status="degraded",
                version=settings.APP_VERSION,
                database=db_status,
            )

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database=db_status,
    )
