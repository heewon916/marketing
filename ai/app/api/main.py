from fastapi import APIRouter

from app.api.routes import health, inference, sessions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(inference.router)
api_router.include_router(sessions.router)
