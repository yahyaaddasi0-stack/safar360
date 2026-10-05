"""Arabic Google Cloud TTS, using the mounted Vertex service account file."""

import re

from fastapi import HTTPException
from google.cloud import texttospeech
from pydantic import BaseModel, Field

from app.core.gcp_auth import load_service_account
from app.services.ai_service import filter_tts_text


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice_id: str = Field(pattern=r"^ar-XA-(?:Wavenet|Neural2)-[A-D]$")


class TTSService:
    def __init__(self) -> None:
        credentials = load_service_account()
        self.client = texttospeech.TextToSpeechAsyncClient(credentials=credentials)

    async def generate_audio(self, request: TTSRequest) -> bytes:
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", request.text)
        text = filter_tts_text(text).strip()
        if not text:
            raise HTTPException(status_code=422, detail="No speakable text")
        voice = texttospeech.VoiceSelectionParams(language_code="ar-XA", name=request.voice_id)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = await self.client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=voice,
            audio_config=audio_config,
        )
        return response.audio_content


def get_tts_service() -> TTSService:
    return TTSService()
