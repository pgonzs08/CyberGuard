from fastapi import APIRouter

from app.api.chatbot_api import router as chatbot_router

router = APIRouter(tags=["API"])

@router.get("/")
async def api_root():
    return {"message": "CyberGuard API Running"}

router.include_router(chatbot_router, prefix="/chatbot")