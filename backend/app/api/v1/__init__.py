from fastapi import APIRouter
from app.api.v1 import sessions, chat, knowledge

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(knowledge.router, tags=["knowledge"])
