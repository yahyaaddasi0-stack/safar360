from fastapi import APIRouter
from app.api.v1.endpoints import characters, chat, webhooks

api_router = APIRouter()

api_router.include_router(
    characters.router,
    tags=["Historical Characters"]
)

api_router.include_router(
    chat.router,
    tags=["Conversational AI Engine"]
)

api_router.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["Payments & Webhooks"]
)
