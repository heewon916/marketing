from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class WeatherInfo(BaseModel):
    condition: str = Field(..., min_length=1)
    temperature: float


class ProcessUtteranceRequest(BaseModel):
    store_id: UUID
    utterance: str = Field(..., min_length=1)
    owner_persona: str = Field(..., min_length=1)
    date: date
    weather: WeatherInfo


class ProcessUtteranceResponse(BaseModel):
    session_id: str
    guide_text: str
    keywords: list[str] | None = None
