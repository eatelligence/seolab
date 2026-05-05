import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers._helpers import get_project_or_404
from schemas.common import ok
from schemas.content import (
    CalendarRequest,
    MetaRequest,
    OptimizeContentRequest,
    SEOBriefRequest,
)
from services import claude_service, page_extract

router = APIRouter(prefix="/api/projects/{project_id}/content", tags=["content"])
log = logging.getLogger(__name__)


@router.post("/seo-brief")
async def seo_brief(
    project_id: uuid.UUID, payload: SEOBriefRequest, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    try:
        result = await claude_service.generate_seo_brief(
            payload.keyword, country=payload.country, search_intent=payload.search_intent,
        )
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))
    return ok(result)


@router.post("/optimize")
async def optimize(
    project_id: uuid.UUID, payload: OptimizeContentRequest, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    text = payload.content
    fetched_meta = None
    if not text:
        if not payload.url:
            raise HTTPException(400, "Provide either content or url")
        try:
            text, title, meta = await page_extract.fetch_text(payload.url)
            fetched_meta = {"title": title, "meta_description": meta, "url": payload.url}
        except Exception as e:
            raise HTTPException(400, f"Failed to fetch URL: {e}")
    if not text or len(text) < 50:
        raise HTTPException(400, "Content is too short to optimize")
    try:
        result = await claude_service.optimize_content(text, payload.target_keyword)
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))
    if fetched_meta:
        result["source"] = fetched_meta
    return ok(result)


@router.post("/meta")
async def meta(
    project_id: uuid.UUID, payload: MetaRequest, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    text = payload.content
    if not text:
        if not payload.url:
            raise HTTPException(400, "Provide either content or url")
        try:
            text, _t, _m = await page_extract.fetch_text(payload.url)
        except Exception as e:
            raise HTTPException(400, f"Failed to fetch URL: {e}")
    if not text or len(text) < 50:
        raise HTTPException(400, "Content too short")
    try:
        return ok(await claude_service.generate_meta(text, n_variants=payload.n_variants))
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))


@router.post("/calendar")
async def calendar(
    project_id: uuid.UUID, payload: CalendarRequest, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    try:
        return ok(await claude_service.generate_content_calendar(
            niche=payload.niche, goals=payload.goals, days=payload.days,
        ))
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))
