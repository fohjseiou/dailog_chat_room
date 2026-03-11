from fastapi import APIRouter
from app.api.v1 import sessions, chat, knowledge, auth, preferences

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(knowledge.router, tags=["knowledge"])
api_router.include_router(preferences.router, tags=["preferences"])
