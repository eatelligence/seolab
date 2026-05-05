from typing import List, Optional

from pydantic import BaseModel


class GSCAuthURL(BaseModel):
    auth_url: str


class GSCProperty(BaseModel):
    site_url: str
    permission_level: Optional[str] = None


class GSCPropertyChoice(BaseModel):
    site_url: str


class GSCPerformancePoint(BaseModel):
    date: str
    clicks: int
    impressions: int
    ctr: float
    position: float


class GSCPerformanceSummary(BaseModel):
    series: List[GSCPerformancePoint]
    totals: dict
    days: int


class GSCQueryRow(BaseModel):
    keyword: str
    clicks: int
    impressions: int
    ctr: float
    position: float


class GSCPageRow(BaseModel):
    page: str
    clicks: int
    impressions: int
    ctr: float
    position: float
