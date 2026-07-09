"""Service health endpoint."""

from typing import cast

from fastapi import APIRouter, Request, status

from app.core.config import Settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check service health",
)
async def health_check(request: Request) -> HealthResponse:
    """Return the backend service health status."""
    settings = cast(Settings, request.app.state.settings)
    return HealthResponse(status="ok", service=settings.app_name)
