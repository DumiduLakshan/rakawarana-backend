from app.repositories.health_repository import fetch_health


def get_health_status() -> dict:
    return {"status": "ok", "details": fetch_health()}

