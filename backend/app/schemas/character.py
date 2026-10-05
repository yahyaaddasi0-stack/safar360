"""API schemas for the Safar 360 catalogue and interactive canvas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    year: str
    title: str
    desc: str


class ArtifactItem(BaseModel):
    name: str
    type: str
    icon: str
    desc: str


class MapLocation(BaseModel):
    name: str
    coords: list[float]
    desc: str


class CharacterBase(BaseModel):
    id: str
    name: str
    arabic_name: str
    latin_name: str
    title: str
    role_tag: str
    category: str
    category_ar: str
    era: str
    era_tag: str
    origin: str
    achievement: str
    quote: str
    avatar: str
    featured: bool
    system_prompt: str = Field(exclude=True)
    canvas_type: str
    canvas_data: dict[str, Any]
    voice_name: str
    death_boundary: str
    quick_prompts: list[str] = Field(default_factory=list)
    timeline: Optional[list[TimelineEvent]] = Field(default_factory=list)
    artifacts: Optional[list[ArtifactItem]] = Field(default_factory=list)
    map_locations: Optional[list[MapLocation]] = Field(default_factory=list)


class CharacterResponse(BaseModel):
    status: str = "success"
    data: CharacterBase


class CharacterListResponse(BaseModel):
    status: str = "success"
    count: int
    data: list[CharacterBase]
