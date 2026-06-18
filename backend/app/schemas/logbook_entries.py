from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

LogbookSectionKey = Literal["airframe", "engine", "propeller"]


class LogbookEntryCreateRequest(BaseModel):
    section: LogbookSectionKey
    entryDate: date
    description: str = Field(min_length=1)
    performerName: Optional[str] = Field(default=None, max_length=255)
    performerCredential: Optional[str] = Field(default=None, max_length=255)
    tachTime: Optional[float] = Field(default=None, ge=0)
    hobbsTime: Optional[float] = Field(default=None, ge=0)
    totalTime: Optional[float] = Field(default=None, ge=0)


class LogbookEntryUpdateRequest(BaseModel):
    section: Optional[LogbookSectionKey] = None
    entryDate: Optional[date] = None
    description: Optional[str] = Field(default=None, min_length=1)
    performerName: Optional[str] = Field(default=None, max_length=255)
    performerCredential: Optional[str] = Field(default=None, max_length=255)
    tachTime: Optional[float] = Field(default=None, ge=0)
    hobbsTime: Optional[float] = Field(default=None, ge=0)
    totalTime: Optional[float] = Field(default=None, ge=0)
    reviewStatus: Optional[Literal["draft", "needs_review", "verified"]] = None


class LogbookEntryResponse(BaseModel):
    id: str
    aircraftId: str
    section: str
    entryDate: date
    description: str
    performerName: Optional[str]
    performerCredential: Optional[str]
    sourceType: str
    reviewStatus: str
    tachTime: Optional[float]
    hobbsTime: Optional[float]
    totalTime: Optional[float]


class LogbookEntryListResponse(BaseModel):
    entries: list[LogbookEntryResponse]
