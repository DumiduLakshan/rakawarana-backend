import inspect
import logging
from typing import Optional
from fastapi import Request

from supabase import Client, create_client

from app.utils.settings import get_settings

logger = logging.getLogger(__name__)


def init_supabase_client() -> Client:
    """Create and return a Supabase client using configured settings."""
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_key)
    logger.info("Supabase client initialized")
    return client


async def close_supabase_client(client: Optional[Client]) -> None:
    """Close the Supabase client if it exposes a close method."""
    if client is None:
        return

    close_method = getattr(client, "close", None)
    if not callable(close_method):
        return

    try:
        result = close_method()
        if inspect.isawaitable(result):
            await result
        logger.info("Supabase client closed")
    except Exception:  # pragma: no cover - defensive cleanup
        logger.exception("Failed to close Supabase client cleanly")


def get_supabase(request):
    """Convenience dependency to fetch Supabase client from app state."""
    return request.app.state.supabase


def get_supabase(request: Request):
    return request.app.state.supabase
