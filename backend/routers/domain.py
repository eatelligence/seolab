"""Domain Overview — generic domain lookup. Plug any domain (yours or a
competitor's) and pull headline metrics + top keywords + top pages + competitors
in one round-trip. Reuses caches: 24h on labs endpoints, 7d on Open PageRank."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers._helpers import get_project_or_404
from schemas.common import ok
from services import dataforseo, openpr
from services.dataforseo import DataForSEOError

router = APIRouter(prefix="/api/projects/{project_id}/domain", tags=["domain"])
log = logging.getLogger(__name__)


def _normalize(domain: str) -> str:
    d = (domain or "").strip().lower()
    for p in ("https://", "http://"):
        if d.startswith(p):
            d = d[len(p):]
    if d.startswith("www."):
        d = d[4:]
    return d.rstrip("/")


@router.get("/overview")
async def domain_overview(
    project_id: uuid.UUID,
    target: str = Query(min_length=3, max_length=255),
    country: str = Query(default="US", min_length=2, max_length=2),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    target = _normalize(target)
    if not target:
        raise HTTPException(400, "Invalid target")

    async def _safe(coro, default=None):
        try:
            return await coro
        except DataForSEOError as e:
            log.warning("domain overview component failed: %s", e)
            return default
        except Exception as e:
            log.warning("domain overview unexpected: %s", e)
            return default

    overview, backlinks, da, top_kws, competitors, top_pages_data = await asyncio.gather(
        _safe(dataforseo.domain_overview(target, country=country.upper()), {}),
        _safe(dataforseo.backlinks_summary(target), {}),
        _safe(openpr.domain_authority([target]), {}),
        _safe(dataforseo.domain_organic_keywords(target, country=country.upper(), limit=50), []),
        _safe(dataforseo.organic_competitors(target, country=country.upper(), limit=10), []),
        _safe(dataforseo.top_pages(target, country=country.upper(), limit=20), []),
    )

    metrics = (overview or {}).get("metrics") or {}
    organic = metrics.get("organic") or {}
    paid = metrics.get("paid") or {}

    competitors_out = []
    for it in (competitors or []):
        m = ((it.get("metrics") or {}).get("organic") or {})
        competitors_out.append({
            "domain": it.get("domain"),
            "intersections": it.get("intersections"),
            "organic_traffic": m.get("etv"),
            "organic_keywords": m.get("count"),
        })

    pages_out = []
    for it in (top_pages_data or []):
        m = ((it.get("metrics") or {}).get("organic") or {})
        pages_out.append({
            "page": it.get("page_address") or it.get("page"),
            "organic_traffic": m.get("etv"),
            "organic_keywords": m.get("count"),
        })

    return ok({
        "target": target,
        "country": country.upper(),
        "is_self": target.lower() == project.domain.lower(),
        "metrics": {
            "domain_authority": (da or {}).get(target.lower(), 0.0),
            "organic_traffic": organic.get("etv"),
            "organic_keywords": organic.get("count"),
            "paid_traffic": paid.get("etv"),
            "paid_keywords": paid.get("count"),
            "backlinks": (backlinks or {}).get("backlinks") or 0,
            "referring_domains": (backlinks or {}).get("referring_domains") or 0,
            "broken_backlinks": (backlinks or {}).get("broken_backlinks") or 0,
            "rank": (backlinks or {}).get("rank"),
        },
        "top_keywords": top_kws or [],
        "top_pages": pages_out,
        "competitors": competitors_out,
    })
