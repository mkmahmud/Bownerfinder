from fastapi import APIRouter

from app.api.v1.exports import router as exports_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.results import router as results_router
from app.api.v1.uploads import router as uploads_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(uploads_router)
api_router.include_router(jobs_router)
api_router.include_router(results_router)
api_router.include_router(exports_router)

