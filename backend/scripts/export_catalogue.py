"""Regenerate the static public catalogue from the validated backend source.

Run from any directory: python3 backend/scripts/export_catalogue.py
Never export system prompts to the browser.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.api.v1.endpoints.characters import load_characters  # noqa: E402


if __name__ == "__main__":
    characters = [character.model_dump(mode="json") for character in load_characters()]
    assert characters and all("system_prompt" not in character for character in characters)
    payload = {"status": "success", "count": len(characters), "data": characters}
    output = ROOT / "characters-public.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(characters)} public characters to {output}")
