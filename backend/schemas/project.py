import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectTagBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    color: str = Field(default="#6b7280", max_length=16)


class ProjectTagCreate(ProjectTagBase):
    pass


class ProjectTagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    color: Optional[str] = Field(default=None, max_length=16)


class ProjectTagOut(ProjectTagBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime


def _normalize_domain(d: str) -> str:
    d = d.strip().lower()
    for p in ("https://", "http://"):
        if d.startswith(p):
            d = d[len(p):]
    if d.startswith("www."):
        d = d[4:]
    return d.rstrip("/")


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=3, max_length=255)
    gsc_property: Optional[str] = Field(default=None, max_length=255)
    competitors: List[str] = Field(default_factory=list)
    country: str = Field(default="US", min_length=2, max_length=2)

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, v: str) -> str:
        return _normalize_domain(v)

    @field_validator("competitors")
    @classmethod
    def normalize_competitors(cls, v: List[str]) -> List[str]:
        return [_normalize_domain(d) for d in v if d and d.strip()]

    @field_validator("country")
    @classmethod
    def upper_country(cls, v: str) -> str:
        return v.upper()


class ProjectCreate(ProjectBase):
    tag_ids: List[uuid.UUID] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    domain: Optional[str] = Field(default=None, min_length=3, max_length=255)
    gsc_property: Optional[str] = Field(default=None, max_length=255)
    competitors: Optional[List[str]] = None
    country: Optional[str] = Field(default=None, min_length=2, max_length=2)
    tag_ids: Optional[List[uuid.UUID]] = None

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, v):
        return _normalize_domain(v) if v else v

    @field_validator("competitors")
    @classmethod
    def normalize_competitors(cls, v):
        if v is None:
            return v
        return [_normalize_domain(d) for d in v if d and d.strip()]

    @field_validator("country")
    @classmethod
    def upper_country(cls, v):
        return v.upper() if v else v


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    tags: List[ProjectTagOut] = Field(default_factory=list)
