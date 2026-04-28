from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field


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


class ExtractFramesRequest(BaseModel):
    store_id: UUID
    input_video_s3_url: AnyHttpUrl


class ExtractFramesResponse(BaseModel):
    session_id: str
    status: Literal["SUCESS", "FAIL"]
    drafts: list[str] = Field(default_factory=list, max_length=3)
