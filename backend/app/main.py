from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db import base  # noqa: F401
from app.db.session import Base, engine


def create_app() -> FastAPI:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Self-hosted lead enrichment application. Phase 1 includes uploads, validation, jobs, and schema.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()

