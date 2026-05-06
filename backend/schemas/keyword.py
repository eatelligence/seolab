import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class KeywordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    keyword: str
    country: str
    search_volume: Optional[int] = None
    keyword_difficulty: Optional[float] = None
    cpc: Optional[float] = None
    intent: Optional[str] = None
    tracked: bool
    created_at: datetime


class ResearchRequest(BaseModel):
    seed: str = Field(min_length=1, max_length=255)
    country: str = Field(default="US", min_length=2, max_length=2)
    suggest_levels: int = Field(default=2, ge=1, le=3)
    max_results: int = Field(default=300, ge=10, le=2000)
    include_metrics: bool = True


class ResearchKeyword(BaseModel):
    keyword: str
    search_volume: Optional[int] = None
    keyword_difficulty: Optional[float] = None
    cpc: Optional[float] = None
    competition: Optional[str] = None
    intent: Optional[str] = None
    monthly_searches: List[dict] = Field(default_factory=list)


class ResearchResult(BaseModel):
    seed: str
    country: str
    total: int
    keywords: List[ResearchKeyword]


class SaveKeywordsRequest(BaseModel):
    keywords: List[ResearchKeyword]
    country: str = Field(default="US", min_length=2, max_length=2)
    track: bool = False


class KeywordListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    keyword_ids: List[uuid.UUID] = Field(default_factory=list)


class KeywordListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime
    keyword_count: int = 0


class BulkTrackRequest(BaseModel):
    keyword_ids: List[uuid.UUID]
    tracked: bool = True


class KeywordImportRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000_000)
    country: str = Field(default="US", min_length=2, max_length=2)
    track: bool = False


class ResearchHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    seed: str
    country: str
    suggest_levels: int
    total: int
    created_at: datetime


class ResearchHistoryDetail(ResearchHistoryOut):
    keywords: List[ResearchKeyword]
