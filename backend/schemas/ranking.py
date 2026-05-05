import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RankingPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    keyword_id: uuid.UUID
    position: Optional[int] = None
    url: Optional[str] = None
    serp_features: List[str] = []
    competitor_positions: dict = {}
    checked_at: datetime


class TrackedKeywordRow(BaseModel):
    keyword_id: uuid.UUID
    keyword: str
    country: str
    search_volume: Optional[int] = None
    current_position: Optional[int] = None
    previous_position: Optional[int] = None
    delta: Optional[int] = None
    url: Optional[str] = None
    serp_features: List[str] = []
    last_checked: Optional[datetime] = None


class VisibilityPoint(BaseModel):
    date: str
    score: float
    keywords_tracked: int
    avg_position: Optional[float] = None


class RankingAlert(BaseModel):
    keyword_id: uuid.UUID
    keyword: str
    previous_position: Optional[int]
    current_position: Optional[int]
    delta: int
    direction: str  # "up" | "down"
    checked_at: datetime
