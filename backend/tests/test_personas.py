"""Run with: cd backend && python3 -m unittest discover -s tests -v"""

import asyncio
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import ChatCompletionRequest, ChatMessage
from app.services.ai_service import SafeStreamFilter, VertexAIService, filter_tts_text


class CharacterCatalogueTests(unittest.TestCase):
    def test_public_route_contains_all_twelve_without_system_prompts(self):
        response = TestClient(app).get("/api/v1/characters")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 12)
        self.assertEqual(len({character["id"] for character in payload["data"]}), 12)
        for character in payload["data"]:
            self.assertNotIn("system_prompt", character)
            self.assertNotIn("sources", character)
            self.assertTrue(character["canvas_data"])
            self.assertTrue(character["voice_name"])

    def test_private_personas_obey_historical_boundaries(self):
        data_file = Path(__file__).resolve().parents[1] / "app/data/characters.json"
        catalogue = json.loads(data_file.read_text(encoding="utf-8"))
        self.assertEqual(len(catalogue), 12)
        for character in catalogue:
            prompt = character["system_prompt"]
            self.assertGreater(len(prompt), 500)
            self.assertIn("سؤال", prompt)
            self.assertTrue("قوس" in prompt or "أقواس" in prompt)
            self.assertTrue("زمن" in prompt or "وفا" in prompt)
            self.assertTrue(character["death_boundary"])
        zenobia = next(item for item in catalogue if item["id"] == "zenobia")
        self.assertIn("غير معروف", zenobia["death_boundary"])
        bilqis = next(item for item in catalogue if item["id"] == "bilqis")
        self.assertIn("غير معروف", bilqis["death_boundary"])

    def test_strict_cors_excludes_arbitrary_sites(self):
        response = TestClient(app).options(
            "/api/v1/characters",
            headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"},
        )
        self.assertNotEqual(response.headers.get("access-control-allow-origin"), "*")
        self.assertNotEqual(response.headers.get("access-control-allow-origin"), "https://untrusted.example")


class StreamingSafetyTests(unittest.TestCase):
    def test_default_token_budget_allows_complete_gemini_stream(self):
        request = ChatCompletionRequest(
            character_id="salah-al-din",
            messages=[ChatMessage(role="user", content="حدثني عن القدس")],
        )
        self.assertEqual(request.max_tokens, 8192)

    def test_filters_actions_and_patronizing_terms_across_chunk_boundaries(self):
        stream = SafeStreamFilter()
        chunks = ["أهلاً يا ب", "ني بك (ين", "ظر إلى الخريطة) ماذا", " ترغب في معرفة؟"]
        output = "".join(stream.feed(piece) for piece in chunks) + stream.feed("", final=True)
        self.assertNotIn("يا بني", output)
        self.assertNotIn("الخريطة)", output)
        self.assertNotIn("(ينظر", output)
        self.assertIn("ماذا ترغب", output)

    def test_image_tag_is_intercepted_without_speaking_it(self):
        stream = SafeStreamFilter()
        output = stream.feed("أهلاً [GENERATE_", final=False)
        output += stream.feed("IMAGE: ancient Palmyra] ماذا تود معرفة؟", final=True)
        self.assertNotIn("GENERATE_IMAGE", output)
        self.assertEqual(stream.image_prompts, ["ancient Palmyra"])
        self.assertEqual(filter_tts_text("يا بنيتي (تبتسم) كيف حالك؟").strip(), "كيف حالك؟")

    def test_sse_uses_real_generator_and_finishes_with_open_question(self):
        class StubChat:
            async def send_message_async(self, *_args, **_kwargs):
                async def response_chunks():
                    for fragment in ("أهلاً (ينظر", " حوله) بالقارئ الكريم."):
                        yield SimpleNamespace(text=fragment)
                return response_chunks()

        service = VertexAIService.__new__(VertexAIService)
        service.model_name = "test-gemini"
        request = ChatCompletionRequest(character_id="salah-al-din", messages=[ChatMessage(role="user", content="مرحبا")])

        async def receive():
            return [event async for event in service.stream_completion(request)]

        with patch.object(VertexAIService, "_chat", return_value=(StubChat(), None)):
            frames = asyncio.run(receive())
        self.assertEqual(frames[-1], "data: [DONE]\n\n")
        text = "".join(json.loads(event.removeprefix("data: "))["choices"][0]["delta"].get("content", "")
                       for event in frames if event.startswith("data: {") and '"choices"' in event)
        self.assertNotIn("(ينظر", text)
        self.assertTrue(text.endswith("؟"))


if __name__ == "__main__":
    unittest.main()
