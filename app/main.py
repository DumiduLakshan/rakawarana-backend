import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes import health, posts
from app.routes import admin
from app.utils.exception_handlers import register_exception_handlers
from app.utils.logging_setup import configure_logging
from app.utils.supabase_client import close_supabase_client, init_supabase_client


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    supabase_client = init_supabase_client()
    app.state.supabase = supabase_client
    try:
        yield
    finally:
        await close_supabase_client(supabase_client)


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Rescue API", version="0.1.0", lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(posts.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    return app




app = create_app()

