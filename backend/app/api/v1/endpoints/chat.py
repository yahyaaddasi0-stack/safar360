from fastapi import APIRouter, Depends, status, Request, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from app.services.ai_service import BaseAIService, get_ai_service
from app.services.tts_service import TTSService, TTSRequest, get_tts_service
from app.db.database import get_db
from app.services.credit_service import CreditService

router = APIRouter()

@router.post(
    "/chat/completions",
    summary="Create historical character chat completion"
)
async def create_chat_completion(
    request: Request,
    chat_req: ChatCompletionRequest,
    ai_service: BaseAIService = Depends(get_ai_service),
    db: AsyncSession = Depends(get_db)
):
    # Determine user identity (IP-based for anonymous users in Phase 5)
    user_id = request.headers.get("x-user-id", request.client.host if request.client else "anonymous")

    # We will assume normal message credit check here.
    has_credit, reason = await CreditService.check_credit(db, user_id, is_image=False)
    if not has_credit:
        raise HTTPException(status_code=402, detail=reason)

    if chat_req.stream:
        async def stream_with_deduction():
            try:
                async for chunk in ai_service.stream_completion(chat_req):
                    yield chunk
                # Deduct only after successful generation
                await CreditService.deduct_credit(db, user_id, is_image=False)
            except Exception as e:
                # Do not deduct if fails during stream
                print(f"Stream failed, no credit deducted: {e}")

        return StreamingResponse(
            stream_with_deduction(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream; charset=utf-8",
                "X-Accel-Buffering": "no",
            }
        )

    # Non-streaming
    response = await ai_service.generate_completion(chat_req)
    await CreditService.deduct_credit(db, user_id, is_image=False)
    return response

@router.post(
    "/chat/audio",
    summary="Generate TTS Audio from Text",
    description="Returns MP3 audio stream for the given text using Google Cloud Text-to-Speech."
)
async def generate_chat_audio(
    request: Request,
    tts_req: TTSRequest,
    tts_service: TTSService = Depends(get_tts_service),
    db: AsyncSession = Depends(get_db)
):
    user_id = request.headers.get("x-user-id", request.client.host if request.client else "anonymous")
    # For now we might not strictly deduct credit for TTS, but could be added here
    audio_content = await tts_service.generate_audio(tts_req)
    return Response(content=audio_content, media_type="audio/mpeg")
