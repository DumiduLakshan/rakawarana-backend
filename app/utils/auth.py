from fastapi import Header

from app.utils.exception_handlers import AppError
from app.utils.settings import get_settings


def require_admin_token(x_api_token: str | None = Header(None)) -> None:
    """Dependency to enforce admin token header."""
    settings = get_settings()
    if not settings.admin_token:
        raise AppError(
            message="Admin token not configured",
            status_code=500,
            details={"missing": "ADMIN_TOKEN"},
        )

    if not x_api_token or x_api_token != settings.admin_token:
        raise AppError(
            message="Unauthorized",
            status_code=401,
            details={"error": "Invalid or missing x-api-token"},
        )
