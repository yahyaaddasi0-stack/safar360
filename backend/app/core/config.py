from typing import List, Union
import os
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Safar 360 API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "REST API & SSE Streaming Backend for Safar 360 Interactive Historical SPA"

    # CORS Configuration - Dynamic from env
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "*")

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        if self.FRONTEND_URL == "*":
            return ["*"]
        return [
            self.FRONTEND_URL,
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]

    # Google Vertex AI Configuration (Prepared for Phase 3)
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "safar360-vertex-ai")
    VERTEX_AI_LOCATION: str = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    VERTEX_AI_MODEL: str = os.getenv("VERTEX_AI_MODEL", "gemini-1.5-pro")
    VERTEX_AI_CREDENTIALS_FILE: str = ""
    MOCK_AI_RESPONSE_DELAY: float = 0.04  # Delay between SSE tokens in seconds for realistic streaming

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
