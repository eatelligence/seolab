import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SEOBriefRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=255)
    country: str = Field(default="US", min_length=2, max_length=2)
    search_intent: str = Field(default="informational")


class OptimizeContentRequest(BaseModel):
    target_keyword: str = Field(min_length=1, max_length=255)
    content: Optional[str] = None
    url: Optional[str] = None  # alternative: fetch + extract


class MetaRequest(BaseModel):
    content: Optional[str] = None
    url: Optional[str] = None
    n_variants: int = Field(default=5, ge=1, le=10)


class CalendarRequest(BaseModel):
    niche: str = Field(min_length=2, max_length=255)
    goals: str = Field(min_length=2, max_length=2000)
    days: int = Field(default=30, ge=7, le=90)


class ContentOutputOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    tool_type: str
    title: str
    input: dict
    output: dict
    created_at: datetime


class ContentOutputSummary(BaseModel):
    """Lightweight version for history list (no output blob)."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tool_type: str
    title: str
    created_at: datetime
