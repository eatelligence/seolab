import asyncio
import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers._helpers import get_project_or_404
from schemas.common import ok
from services import dataforseo, openpr
from services.dataforseo import DataForSEOError

router = APIRouter(prefix="/api/projects/{project_id}/competitors", tags=["competitors"])
log = logging.getLogger(__name__)


def _domains_for(project) -> List[str]:
    return [project.domain, *(project.competitors or [])][:6]


@router.get("/overview")
async def overview(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Side-by-side comparison: DA, organic traffic estimate, ranking keywords, backlinks."""
    project = await get_project_or_404(db, project_id)
    domains = _domains_for(project)
    if not domains:
        return ok([])

    pr = await openpr.domain_authority(domains)

    async def _per_domain(d: str):
        try:
            domain_data = await dataforseo.domain_overview(d, country=project.country)
            metrics = (domain_data.get("metrics") or {}).get("organic") or {}
            backlinks = await dataforseo.backlinks_summary(d)
        except DataForSEOError as e:
            log.warning("competitor data failed for %s: %s", d, e)
            return {
                "domain": d, "domain_authority": pr.get(d.lower(), 0.0),
                "organic_traffic": None, "organic_keywords": None,
                "backlinks": None, "referring_domains": None, "error": str(e),
            }
        return {
            "domain": d,
            "is_self": d == project.domain,
            "domain_authority": pr.get(d.lower(), 0.0),
            "organic_traffic": metrics.get("etv"),
            "organic_keywords": metrics.get("count"),
            "estimated_paid_traffic": (domain_data.get("metrics") or {}).get("paid", {}).get("etv"),
            "backlinks": backlinks.get("backlinks"),
            "referring_domains": backlinks.get("referring_domains"),
        }

    rows = await asyncio.gather(*(_per_domain(d) for d in domains))
    return ok(rows)


@router.get("/keyword-gap")
async def keyword_gap(
    project_id: uuid.UUID,
    limit: int = Query(default=200, ge=10, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Keywords each competitor ranks for that the project does not."""
    project = await get_project_or_404(db, project_id)
    if not project.competitors:
        return ok([])
    try:
        items = await dataforseo.keyword_gap(
            target=project.domain,
            competitors=project.competitors,
            country=project.country,
            limit=limit,
        )
    except DataForSEOError as e:
        raise HTTPException(400, str(e))
    out = []
    for it in items:
        kd = it.get("keyword_data") or it
        info = (kd.get("keyword_info") or {})
        out.append({
            "keyword": kd.get("keyword"),
            "search_volume": info.get("search_volume"),
            "cpc": info.get("cpc"),
            "competition": info.get("competition_level"),
            "difficulty": (kd.get("keyword_properties") or {}).get("keyword_difficulty"),
        })
    return ok(out)


@router.get("/content-gap")
async def content_gap(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=10, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Top trafficked pages for each competitor."""
    project = await get_project_or_404(db, project_id)
    competitors = (project.competitors or [])[:5]
    if not competitors:
        return ok([])

    async def _top(d: str):
        try:
            return {"domain": d, "pages": await dataforseo.top_pages(d, country=project.country, limit=limit)}
        except DataForSEOError as e:
            return {"domain": d, "pages": [], "error": str(e)}

    rows = await asyncio.gather(*(_top(d) for d in competitors))
    return ok(rows)


@router.get("/serp-overlap")
async def serp_overlap(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Returns shared organic competitors as reported by DataForSEO."""
    project = await get_project_or_404(db, project_id)
    try:
        items = await dataforseo.organic_competitors(project.domain, country=project.country, limit=20)
    except DataForSEOError as e:
        raise HTTPException(400, str(e))
    out = []
    for it in items:
        metrics = (it.get("metrics") or {}).get("organic") or {}
        out.append({
            "domain": it.get("domain"),
            "intersections": it.get("intersections"),
            "organic_traffic": metrics.get("etv"),
            "organic_keywords": metrics.get("count"),
            "is_competitor": it.get("domain", "").lower() in {c.lower() for c in (project.competitors or [])},
        })
    return ok(out)
