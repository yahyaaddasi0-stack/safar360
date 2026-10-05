import os
from google.cloud import texttospeech
from pydantic import BaseModel

class TTSRequest(BaseModel):
    text: str
    voice_id: str

class TTSService:
    def __init__(self):
        try:
            self.client = texttospeech.TextToSpeechAsyncClient()
            self.is_initialized = True
            print("✅ [Google Cloud TTS] Initialized successfully.")
        except Exception as e:
            self.is_initialized = False
            print(f"⚠️ [Google Cloud TTS] Initialization failed: {e}")

    async def generate_audio(self, request: TTSRequest) -> bytes:
        if not self.is_initialized:
            # Fallback to an empty 1-byte wav for graceful degradation
            return b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"

        synthesis_input = texttospeech.SynthesisInput(text=request.text)

        # Parse voice_id to determine language and name
        # e.g., ar-XA-Wavenet-B
        parts = request.voice_id.split('-')
        language_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "ar-XA"

        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=request.voice_id
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = await self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return response.audio_content

def get_tts_service() -> TTSService:
    return TTSService()
