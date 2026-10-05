from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(
        ..., description="Message author role: system, user, or assistant"
    )
    content: str = Field(..., description="The textual content of the message")


class ChatCompletionRequest(BaseModel):
    character_id: str = Field(
        ..., description="Historical character ID to converse with (e.g., 'tariq-ibn-ziyad', 'al-khwarizmi')"
    )
    messages: List[ChatMessage] = Field(
        ..., description="List of previous conversation messages forming dialogue context"
    )
    stream: bool = Field(
        default=True, description="Whether to stream back partial progress via Server-Sent Events (SSE)"
    )
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature for Vertex AI"
    )
    max_tokens: Optional[int] = Field(
        default=1024, description="Maximum tokens to generate"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "character_id": "ibn-battuta",
                "messages": [
                    {
                        "role": "user",
                        "content": "ما هي أغرب مغامرة واجهتها في بلاد الهند والصين؟"
                    }
                ],
                "stream": True,
                "temperature": 0.7
            }
        }
    }


class ChatCompletionResponseChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    character_id: str
    choices: List[ChatCompletionResponseChoice]


class StreamDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: StreamDelta
    finish_reason: Optional[str] = None


class ChatStreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    character_id: str
    choices: List[StreamChoice]
