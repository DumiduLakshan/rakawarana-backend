from fastapi import APIRouter
from app.services.health_service import get_health_status
from app.utils.exception_handlers import InvalidDataException


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
def read_health():
    return "server running normally"



