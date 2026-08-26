"""API package — route aggregation."""

from fastapi import APIRouter
from app.api.uploads import router as uploads_router
from app.api.jobs import router as jobs_router
from app.api.webhooks import router as webhooks_router
from app.api.admin import router as admin_router
from app.api.sample import router as sample_router

# Main router that includes all sub-routers
api_router = APIRouter()
api_router.include_router(uploads_router)
api_router.include_router(jobs_router)
api_router.include_router(webhooks_router)
api_router.include_router(admin_router)
api_router.include_router(sample_router)

__all__ = ["api_router"]
