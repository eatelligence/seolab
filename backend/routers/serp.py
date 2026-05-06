"""SERP Overview — quick lookup of top organic results for any keyword in any
geo without having to track it. Reuses dataforseo.serp_organic which already
caches at 6h."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers._helpers import get_project_or_404
from schemas.common import ok
from services import dataforseo
from services.dataforseo import DataForSEOError

router = APIRouter(prefix="/api/projects/{project_id}/serp", tags=["serp"])
log = logging.getLogger(__name__)


@router.get("")
async def serp_overview(
    project_id: uuid.UUID,
    keyword: str = Query(min_length=1, max_length=255),
    country: str = Query(default="US", min_length=2, max_length=2),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    try:
        data = await dataforseo.serp_organic(
            keyword=keyword.strip(),
            country=country.upper(),
            target_domain=project.domain,
        )
    except DataForSEOError as e:
        raise HTTPException(400, str(e))

    competitor_set = {c.lower() for c in (project.competitors or [])}
    items = data.get("items") or []
    enriched = []
    for it in items[:20]:
        domain = (it.get("domain") or "").lower()
        is_self = domain == project.domain.lower() or domain.endswith("." + project.domain.lower())
        is_competitor = any(domain == c or domain.endswith("." + c) for c in competitor_set)
        enriched.append({
            "rank": it.get("rank_absolute") or it.get("rank_group"),
            "title": it.get("title"),
            "url": it.get("url"),
            "domain": it.get("domain"),
            "snippet": it.get("description") or it.get("snippet"),
            "breadcrumb": it.get("breadcrumb"),
            "is_self": is_self,
            "is_competitor": is_competitor,
        })

    return ok({
        "keyword": data.get("keyword"),
        "country": data.get("country"),
        "items": enriched,
        "serp_features": data.get("serp_features") or [],
        "target_position": data.get("target_position"),
        "target_url": data.get("target_url"),
        "target_domain": project.domain,
        "checked_at": data.get("checked_at"),
    })
