"""Public catalogue of historical characters backed by the versioned JSON file."""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.character import CharacterBase, CharacterListResponse, CharacterResponse

router = APIRouter()
CHARACTERS_FILE = Path(__file__).resolve().parents[3] / "data" / "characters.json"


def load_characters() -> list[CharacterBase]:
    """Fail visibly if the deployed image lacks its catalogue; never return [] silently."""
    with CHARACTERS_FILE.open(encoding="utf-8") as source:
        records = json.load(source)
    if not isinstance(records, list) or not records:
        raise ValueError("characters.json must contain a non-empty array")
    characters = [CharacterBase.model_validate(record) for record in records]
    if len({character.id for character in characters}) != len(characters):
        raise ValueError("characters.json contains duplicate character IDs")
    return characters


@router.get("/characters", response_model=CharacterListResponse)
async def get_characters(category: Optional[str] = Query(None)) -> CharacterListResponse:
    characters = load_characters()
    if category and category != "all":
        characters = [character for character in characters if character.category == category]
    return CharacterListResponse(status="success", count=len(characters), data=characters)


@router.get("/characters/{character_id}", response_model=CharacterResponse)
async def get_character_by_id(character_id: str) -> CharacterResponse:
    character = next((item for item in load_characters() if item.id == character_id), None)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unknown character: {character_id}")
    return CharacterResponse(status="success", data=character)
