import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AIVisibilityQueryCreate(BaseModel):
    query: str = Field(min_length=2, max_length=1024)
    enabled: bool = True


class AIVisibilityQueryUpdate(BaseModel):
    query: Optional[str] = Field(default=None, min_length=2, max_length=1024)
    enabled: Optional[bool] = None


class AIVisibilityQueryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    query: str
    enabled: bool
    created_at: datetime


class AIVisibilityCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    query_id: uuid.UUID
    provider: str
    response_text: str
    brand_mentioned: bool
    mention_position: Optional[int] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    competitors_mentioned: List[str] = []
    checked_at: datetime
