"""Root API router combining all endpoint modules."""

from fastapi import APIRouter

from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.health import router as health_router

api_router = APIRouter(prefix="/api")

api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(chat_router)
