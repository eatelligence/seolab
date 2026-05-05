import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AuditRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    health_score: Optional[int] = None
    pages_crawled: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    summary: dict = {}
    created_at: datetime


class AuditIssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    run_id: uuid.UUID
    issue_type: str
    severity: str
    url: str
    details: dict = {}
    created_at: datetime


class AuditPageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    run_id: uuid.UUID
    url: str
    status_code: Optional[int] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_count: int
    word_count: int
    depth: int
    load_time_ms: Optional[int] = None
    canonical: Optional[str] = None
    is_https: bool
    data: dict = {}
    crawled_at: datetime


class AuditRunRequest(BaseModel):
    run_pagespeed: bool = True
