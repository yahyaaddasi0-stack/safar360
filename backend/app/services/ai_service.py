"""Vertex AI Gemini dialogue with persona-level system instructions and safe SSE output."""

import asyncio
import base64
import json
import re
import tempfile
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator

import vertexai
from fastapi import HTTPException
from vertexai.generative_models import Content, GenerationConfig, GenerativeModel, Part
from vertexai.preview.vision_models import ImageGenerationModel

from app.api.v1.endpoints.characters import load_characters
from app.core.config import settings
from app.core.gcp_auth import load_service_account
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
)

IMAGE_TAG = re.compile(r"\[GENERATE_IMAGE:\s*([^\]]{1,500})\]", re.I)
PARENTHETICAL = re.compile(r"\([^)]*\)|（[^）]*）|\[[^\]]*\]", re.S)
PATRONIZING = re.compile(r"يا\s*(?:بنيتي|بني|هذا|هذه)(?![\u0621-\u064a])", re.I)


def filter_tts_text(text: str) -> str:
    """Remove stage directions and unwanted forms of address before UI or TTS output."""
    text = PARENTHETICAL.sub(" ", text)
    text = re.sub(r"[（(\[][^)）\]]*$", "", text)  # unfinished stage direction
    text = PATRONIZING.sub("", text)
    return re.sub(r"[ \t]{2,}", " ", text)


class SafeStreamFilter:
    """Retain two words and incomplete brackets so chunk boundaries cannot leak actions."""

    def __init__(self) -> None:
        self.pending = ""
        self.output = ""
        self.image_prompts: list[str] = []

    def feed(self, chunk: str, *, final: bool = False) -> str:
        self.pending += chunk
        if final:
            limit = len(self.pending)
        else:
            spaces = [match.end() for match in re.finditer(r"\s", self.pending)]
            if len(spaces) < 3:
                return ""
            limit = spaces[-2]
            # A parenthesis/tag begun before this boundary must remain buffered.
            for opening, closing in (("(", ")"), ("（", "）"), ("[", "]")):
                prefix = self.pending[:limit]
                if prefix.rfind(opening) > prefix.rfind(closing):
                    limit = min(limit, prefix.rfind(opening))
        if limit <= 0:
            return ""
        segment, self.pending = self.pending[:limit], self.pending[limit:]
        self.image_prompts.extend(match.group(1).strip() for match in IMAGE_TAG.finditer(segment))
        safe = filter_tts_text(segment)
        self.output += safe
        return safe


class BaseAIService(ABC):
    @abstractmethod
    async def generate_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream_completion(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        if False:
            yield ""
        raise NotImplementedError


class VertexAIService(BaseAIService):
    """Uses only the configured Google service account, never implicit ADC."""

    def __init__(self) -> None:
        credentials = load_service_account()
        project_id = settings.GOOGLE_CLOUD_PROJECT or credentials.project_id
        if not project_id:
            raise HTTPException(status_code=503, detail="Google Cloud project is not configured")
        vertexai.init(
            project=project_id,
            location=settings.VERTEX_AI_LOCATION,
            credentials=credentials,
        )
        self.model_name = settings.VERTEX_AI_MODEL

    @staticmethod
    def _persona(character_id: str):
        persona = next((item for item in load_characters() if item.id == character_id), None)
        if persona is None:
            raise HTTPException(status_code=404, detail="Unknown historical character")
        return persona

    @staticmethod
    def _history(messages: list[ChatMessage]) -> list[Content]:
        # Client-supplied system instructions are not trusted; only our catalogue is.
        return [
            Content(role="model" if message.role == "assistant" else "user",
                    parts=[Part.from_text(message.content)])
            for message in messages[:-1]
            if message.role in ("assistant", "user")
        ]

    def _chat(self, request: ChatCompletionRequest):
        persona = self._persona(request.character_id)
        if not request.messages or request.messages[-1].role != "user":
            raise HTTPException(status_code=422, detail="The final message must be from the user")
        model = GenerativeModel(self.model_name, system_instruction=persona.system_prompt)
        chat = model.start_chat(history=self._history(request.messages))
        config = GenerationConfig(
            temperature=request.temperature if request.temperature is not None else 0.7,
            max_output_tokens=request.max_tokens or 8192,
        )
        return chat, config

    @staticmethod
    async def _generate_image(prompt: str) -> str:
        """Generate an embeddable image; never pass a private gs:// URI to the browser."""
        def create() -> str:
            model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
            response = model.generate_images(prompt=prompt, number_of_images=1, aspect_ratio="1:1")
            if not response.images:
                return ""
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as output:
                image_path = Path(output.name)
            try:
                response.images[0].save(location=str(image_path))
                content = image_path.read_bytes()
                if not content or len(content) > 3_000_000:
                    return ""
                return "data:image/png;base64," + base64.b64encode(content).decode("ascii")
            finally:
                image_path.unlink(missing_ok=True)

        return await asyncio.to_thread(create)

    async def generate_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        chat, config = self._chat(request)
        result = await chat.send_message_async(request.messages[-1].content, generation_config=config)
        response = SafeStreamFilter()
        response.feed(result.text, final=True)
        content = response.output.strip()
        if not content:
            raise RuntimeError("Vertex AI returned no usable text")
        if not content.endswith(("؟", "?")):
            content += " ما الجانب الذي ترغب في استكشافه أكثر؟"
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}", created=int(time.time()),
            model=self.model_name, character_id=request.character_id,
            choices=[ChatCompletionResponseChoice(
                message=ChatMessage(role="assistant", content=content), finish_reason="stop")],
        )

    async def stream_completion(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        chat, config = self._chat(request)
        stream_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())

        def frame(delta: dict, finish_reason=None) -> str:
            payload = {
                "id": stream_id, "object": "chat.completion.chunk", "created": created,
                "model": self.model_name, "character_id": request.character_id,
                "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
            }
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        responses = await chat.send_message_async(
            request.messages[-1].content, stream=True, generation_config=config
        )
        cleaner = SafeStreamFilter()
        yield frame({"role": "assistant"})
        async for chunk in responses:
            safe = cleaner.feed(chunk.text or "")
            if safe:
                yield frame({"content": safe})
        last = cleaner.feed("", final=True)
        if last:
            yield frame({"content": last})
        if not cleaner.output.strip():
            raise RuntimeError("Vertex AI returned no usable text")
        if not cleaner.output.strip().endswith(("؟", "?")):
            yield frame({"content": " ما الجانب الذي ترغب في استكشافه أكثر؟"})
        for image_prompt in cleaner.image_prompts:
            try:
                yield frame({"content": f"[GENERATE_IMAGE: {image_prompt}]"})
                image_url = await self._generate_image(image_prompt)
                if image_url:
                    yield frame({"content": f"\n![Generated Image]({image_url})"})
                else:
                    yield frame({"content": "\nتعذّر إنشاء الصورة حالياً."})
            except Exception:
                yield frame({"content": "\nتعذّر إنشاء الصورة حالياً."})
        yield frame({}, "stop")
        yield "data: [DONE]\n\n"


def get_ai_service() -> BaseAIService:
    return VertexAIService()
