import asyncio
import json
import time
import uuid
import re
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import settings
from app.schemas.chat import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
)

import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
from vertexai.preview.vision_models import ImageGenerationModel

# Load character personas from JSON or define mock ones
CHARACTER_PERSONAS: Dict[str, Dict[str, str]] = {
    "salah-al-din": {
        "name": "صلاح الدين الأيوبي",
        "era": "القرن السادس الهجري",
        "greeting": "أهلاً بضيفنا الكريم في مجلسنا. ما الذي تود معرفته عن بيت المقدس؟",
        "system_prompt": "أنت صلاح الدين الأيوبي، القائد المسلم التاريخي البطل. تتحدث بحكمة وعدل وشجاعة. لا تستخدم ألقاباً مصطنعة مثل (يضحك) أو (يبتسم). إذا طلب منك المستخدم رسم صورة أو إظهار خريطة، أضف العلامة [GENERATE_IMAGE: وصف الصورة بالإنجليزية] في نهاية ردك.",
    },
    "al-mutanabbi": {
        "name": "أبو الطيب المتنبي",
        "era": "القرن الرابع الهجري",
        "greeting": "الخيل والليل والبيداء تعرفني. ماذا تريد أن تسمع من شعري؟",
        "system_prompt": "أنت الشاعر المتنبي. تتحدث بفخر واعتزاز وبلاغة عربية. لا تستخدم ألقاباً مصطنعة أو حركات مسرحية مثل (يتنهد) أو (يضحك). إذا طلب منك المستخدم رسم صورة أو مشهد، أضف العلامة [GENERATE_IMAGE: وصف المشهد بالإنجليزية] في نهاية ردك.",
    },
    "zenobia": {
        "name": "زنوبيا",
        "era": "القرن الثالث الميلادي",
        "greeting": "أنا ملكة تدمر وزوجة أذينة. سلني عن أمجاد الشرق.",
        "system_prompt": "أنت الملكة زنوبيا ملكة تدمر. تتحدثين بكبرياء وقوة ملكية. لا تستخدمي حركات أو انفعالات بين قوسين مثل (تبتسم). إذا طلب منك المستخدم رسم صورة أو معبد، أضفي العلامة [GENERATE_IMAGE: وصف الصورة بالإنجليزية] في نهاية ردك.",
    }
}

def filter_tts_text(text: str) -> str:
    """Strip out any parenthetical roleplay actions like (ابتسم) or (يضحك) and filter 'يا بني'"""
    # Remove any text within parentheses or brackets
    filtered = re.sub(r'\(.*?\)', '', text)
    filtered = re.sub(r'\[.*?\]', '', filtered)
    # Remove specific patronizing words
    filtered = filtered.replace('يا بني', '')
    return filtered.strip()

class BaseAIService(ABC):
    @abstractmethod
    async def generate_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        pass

    @abstractmethod
    async def stream_completion(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        if False:
            yield ""
        raise NotImplementedError

class VertexAIService(BaseAIService):
    """
    Live implementation of Google Vertex AI Gemini Integration.
    Requires GOOGLE_APPLICATION_CREDENTIALS to be set.
    """
    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.VERTEX_AI_LOCATION
        self.model_name = settings.VERTEX_AI_MODEL

        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_name)
            self.image_model = ImageGenerationModel.from_pretrained("imagegeneration@006")
            self.is_initialized = True
            print("✅ [Vertex AI] Initialized successfully.")
        except Exception as e:
            self.is_initialized = False
            print(f"⚠️ [Vertex AI] Initialization failed (Missing/Invalid Credentials): {e}")

    def _get_history(self, messages: List[ChatMessage]) -> List[Content]:
        history = []
        for msg in messages[:-1]:
            role = "model" if msg.role == "assistant" else "user"
            history.append(Content(role=role, parts=[Part.from_text(msg.content)]))
        return history

    async def _handle_imagen3(self, prompt: str) -> str:
        """Call Imagen 3 to generate image and return a mock/real URL depending on auth"""
        try:
            if not self.is_initialized:
                raise Exception("Not initialized")
            response = self.image_model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1"
            )
            if response.images:
                # Save it temporarily or return a placeholder since we can't host it easily here without Cloud Storage
                # For Phase 3 scope, returning a valid markdown image link placeholder
                return f"\n![Generated Image]({response.images[0]._gcs_uri})\n"
        except Exception as e:
            print(f"⚠️ [Imagen 3] Generation failed: {e}")
            return f"\n![Generated Image](https://via.placeholder.com/512?text=Imagen+3+Not+Configured)\n"
        return ""

    async def generate_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created_time = int(time.time())

        persona = CHARACTER_PERSONAS.get(request.character_id, CHARACTER_PERSONAS["salah-al-din"])
        sys_prompt = persona["system_prompt"]

        last_msg = request.messages[-1].content



        reply_content = "This is a mock fallback response due to missing GCP credentials."
        if self.is_initialized and last_msg:
            try:
                chat = self.model.start_chat(history=self._get_history(request.messages))
                full_prompt = f"System: {sys_prompt}\nUser: {last_msg}"
                response = await chat.send_message_async(full_prompt)
                reply_content = response.text
            except Exception as e:
                print(f"⚠️ [Vertex AI] Generation error: {e}")

        # Apply Regex Filters
        reply_content = filter_tts_text(reply_content)

        return ChatCompletionResponse(
            id=response_id,
            created=created_time,
            model=settings.VERTEX_AI_MODEL,
            character_id=request.character_id,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=reply_content),
                    finish_reason="stop",
                )
            ],
        )

    async def stream_completion(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        stream_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created_time = int(time.time())

        persona = CHARACTER_PERSONAS.get(request.character_id, CHARACTER_PERSONAS["salah-al-din"])
        sys_prompt = persona["system_prompt"]
        last_msg = request.messages[-1].content
        full_ai_response = ""
        img_response = ""

        initial_chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": settings.VERTEX_AI_MODEL,
            "character_id": request.character_id,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(initial_chunk, ensure_ascii=False)}\n\n"

        if self.is_initialized and last_msg:
            try:
                chat = self.model.start_chat(history=self._get_history(request.messages))
                full_prompt = f"System: {sys_prompt}\nUser: {last_msg}"
                responses = await chat.send_message_async(full_prompt, stream=True)

                async for chunk in responses:
                    filtered_text = filter_tts_text(chunk.text)
                    if filtered_text:
                        full_ai_response += filtered_text
                        data = {
                            "id": stream_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": settings.VERTEX_AI_MODEL,
                            "character_id": request.character_id,
                            "choices": [{"index": 0, "delta": {"content": filtered_text}, "finish_reason": None}],
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            except Exception as e:
                print(f"⚠️ [Vertex AI] Stream error: {e}")
                err_data = {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": settings.VERTEX_AI_MODEL,
                    "character_id": request.character_id,
                    "choices": [{"index": 0, "delta": {"content": "أعتذر، فقدنا الاتصال ببيت الحكمة."}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(err_data, ensure_ascii=False)}\n\n"
        else:
            # Fallback if no credentials
            fallback_msg = filter_tts_text(persona["greeting"])

            # Check user message for mock image request
            if "ارسم" in last_msg or "صورة" in last_msg:
                fallback_msg += " [GENERATE_IMAGE: majestic historical scene]"

            full_ai_response = fallback_msg
            words = fallback_msg.split(" ")
            for word in words:
                data = {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": settings.VERTEX_AI_MODEL,
                    "character_id": request.character_id,
                    "choices": [{"index": 0, "delta": {"content": word + " "}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)

        # Post-stream processing for images
        img_match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_ai_response)
        if img_match:
            img_prompt = img_match.group(1).strip()
            img_response = await self._handle_imagen3(img_prompt)
            if img_response:
                data = {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": settings.VERTEX_AI_MODEL,
                    "character_id": request.character_id,
                    "choices": [{"index": 0, "delta": {"content": img_response}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        stop_chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": settings.VERTEX_AI_MODEL,
            "character_id": request.character_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(stop_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"


def get_ai_service() -> BaseAIService:
    return VertexAIService()
