import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.content import ContentOutput
from routers._helpers import get_project_or_404
from schemas.common import ok
from schemas.content import (
    CalendarRequest,
    ContentOutputOut,
    ContentOutputSummary,
    MetaRequest,
    OptimizeContentRequest,
    SEOBriefRequest,
)
from services import claude_service, page_extract

router = APIRouter(prefix="/api/projects/{project_id}/content", tags=["content"])
log = logging.getLogger(__name__)


async def _save_output(
    db: AsyncSession,
    project_id: uuid.UUID,
    tool_type: str,
    title: str,
    input_payload: dict,
    output: dict,
) -> ContentOutput:
    record = ContentOutput(
        project_id=project_id,
        tool_type=tool_type,
        title=(title or "(untitled)")[:512],
        input=input_payload or {},
        output=output or {},
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


# --------------- Generation endpoints ---------------

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
    record = await _save_output(
        db, project_id, "brief",
        title=f"{payload.keyword} · {payload.country}",
        input_payload=payload.model_dump(),
        output=result,
    )
    return ok({"id": str(record.id), "result": result})


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
    record = await _save_output(
        db, project_id, "optimize",
        title=f"{payload.target_keyword} · {payload.url or 'pasted'}",
        input_payload=payload.model_dump(),
        output=result,
    )
    return ok({"id": str(record.id), "result": result})


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
        result = await claude_service.generate_meta(text, n_variants=payload.n_variants)
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))
    record = await _save_output(
        db, project_id, "meta",
        title=payload.url or (text[:80] + "…"),
        input_payload=payload.model_dump(),
        output=result,
    )
    return ok({"id": str(record.id), "result": result})


@router.post("/calendar")
async def calendar(
    project_id: uuid.UUID, payload: CalendarRequest, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    try:
        result = await claude_service.generate_content_calendar(
            niche=payload.niche, goals=payload.goals, days=payload.days,
        )
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))
    record = await _save_output(
        db, project_id, "calendar",
        title=f"{payload.niche} · {payload.days}d",
        input_payload=payload.model_dump(),
        output=result,
    )
    return ok({"id": str(record.id), "result": result})


# --------------- History endpoints ---------------

@router.get("/history")
async def history(
    project_id: uuid.UUID,
    tool_type: Optional[str] = Query(default=None, pattern="^(brief|optimize|meta|calendar)$"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    stmt = select(ContentOutput).where(ContentOutput.project_id == project_id)
    if tool_type:
        stmt = stmt.where(ContentOutput.tool_type == tool_type)
    stmt = stmt.order_by(desc(ContentOutput.created_at)).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return ok([ContentOutputSummary.model_validate(r).model_dump(mode="json") for r in rows])


@router.get("/history/{output_id}")
async def history_get(
    project_id: uuid.UUID, output_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    rec = await db.get(ContentOutput, output_id)
    if not rec or rec.project_id != project_id:
        raise HTTPException(404, "Output not found")
    return ok(ContentOutputOut.model_validate(rec).model_dump(mode="json"))


@router.delete("/history/{output_id}")
async def history_delete(
    project_id: uuid.UUID, output_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    rec = await db.get(ContentOutput, output_id)
    if not rec or rec.project_id != project_id:
        raise HTTPException(404, "Output not found")
    await db.delete(rec)
    await db.commit()
    return ok({"deleted": str(output_id)})
