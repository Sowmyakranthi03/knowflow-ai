from fastapi import APIRouter, status

from app.core.config import settings
from app.schemas.health import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check API health",
    description="Returns the current status and basic service information.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )