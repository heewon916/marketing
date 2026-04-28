from datetime import date
from typing import Annotated
from typing import Literal
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


class ExtractFramesRequest(BaseModel):
    session_id: UUID
    video: str = Field(..., min_length=1)


class ExtractFramesResponse(BaseModel):
    session_id: str
    status: Literal["FRAME_EXTRACTED", "TEXT_GENERATED"]
    drafts: list[str] = Field(default_factory=list, max_length=3)


class FinalEditRequest(BaseModel):
    session_id: UUID
    drafts: list[Annotated[str, Field(min_length=1)]] = Field(
        default_factory=list,
        max_length=3,
    )


class FinalEditResponse(BaseModel):
    session_id: str
    status: Literal["FRAME_EXTRACTED", "PHOTO_EDITED"]
    results: list[str] = Field(default_factory=list, max_length=3)
