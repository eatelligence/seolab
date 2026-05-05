import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.ai_visibility import AIVisibilityCheck, AIVisibilityQuery
from routers._helpers import get_project_or_404
from schemas.ai_visibility import (
    AIVisibilityCheckOut,
    AIVisibilityQueryCreate,
    AIVisibilityQueryOut,
    AIVisibilityQueryUpdate,
)
from schemas.common import ok
from services import ai_visibility, claude_service

router = APIRouter(prefix="/api/projects/{project_id}/ai-visibility", tags=["ai-visibility"])
log = logging.getLogger(__name__)


# ---------------- Queries CRUD ----------------

@router.get("/queries")
async def list_queries(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await get_project_or_404(db, project_id)
    rows = (await db.execute(
        select(AIVisibilityQuery).where(AIVisibilityQuery.project_id == project_id)
        .order_by(desc(AIVisibilityQuery.created_at))
    )).scalars().all()
    return ok([AIVisibilityQueryOut.model_validate(r).model_dump(mode="json") for r in rows])


@router.post("/queries", status_code=status.HTTP_201_CREATED)
async def create_query(
    project_id: uuid.UUID, payload: AIVisibilityQueryCreate, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    q = AIVisibilityQuery(project_id=project_id, query=payload.query.strip(), enabled=payload.enabled)
    db.add(q)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Query already tracked for this project")
    await db.refresh(q)
    return ok(AIVisibilityQueryOut.model_validate(q).model_dump(mode="json"))


@router.patch("/queries/{query_id}")
async def update_query(
    project_id: uuid.UUID, query_id: uuid.UUID,
    payload: AIVisibilityQueryUpdate, db: AsyncSession = Depends(get_db),
):
    q = await db.get(AIVisibilityQuery, query_id)
    if not q or q.project_id != project_id:
        raise HTTPException(404, "Query not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(q, f, v)
    await db.commit()
    await db.refresh(q)
    return ok(AIVisibilityQueryOut.model_validate(q).model_dump(mode="json"))


@router.delete("/queries/{query_id}")
async def delete_query(project_id: uuid.UUID, query_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    q = await db.get(AIVisibilityQuery, query_id)
    if not q or q.project_id != project_id:
        raise HTTPException(404, "Query not found")
    await db.delete(q)
    await db.commit()
    return ok({"deleted": str(query_id)})


# ---------------- Checks ----------------

@router.post("/check")
async def check_now(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Run an AI visibility check for ALL enabled queries of the project."""
    await get_project_or_404(db, project_id)
    try:
        n = await ai_visibility.run_for_project(db, project_id)
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))
    return ok({"checked": n})


@router.post("/queries/{query_id}/check")
async def check_query_now(
    project_id: uuid.UUID, query_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    q = await db.get(AIVisibilityQuery, query_id)
    if not q or q.project_id != project_id:
        raise HTTPException(404, "Query not found")
    project = await get_project_or_404(db, project_id)
    try:
        check = await ai_visibility.run_check(db, project, q)
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))
    return ok(AIVisibilityCheckOut.model_validate(check).model_dump(mode="json"))


@router.get("/queries/{query_id}/checks")
async def list_checks(
    project_id: uuid.UUID, query_id: uuid.UUID,
    limit: int = Query(default=30, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = await db.get(AIVisibilityQuery, query_id)
    if not q or q.project_id != project_id:
        raise HTTPException(404, "Query not found")
    rows = (await db.execute(
        select(AIVisibilityCheck).where(AIVisibilityCheck.query_id == query_id)
        .order_by(desc(AIVisibilityCheck.checked_at)).limit(limit)
    )).scalars().all()
    return ok([AIVisibilityCheckOut.model_validate(r).model_dump(mode="json") for r in rows])


# ---------------- Aggregates ----------------

@router.get("/overview")
async def overview(
    project_id: uuid.UUID,
    days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    return ok(await ai_visibility.overview(db, project_id, days=days))


@router.get("/history")
async def history(
    project_id: uuid.UUID,
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    return ok(await ai_visibility.history(db, project_id, days=days))


@router.get("/suggestions")
async def suggestions(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await get_project_or_404(db, project_id)
    recent = (await db.execute(
        select(AIVisibilityCheck.response_text)
        .join(AIVisibilityQuery, AIVisibilityQuery.id == AIVisibilityCheck.query_id)
        .where(AIVisibilityQuery.project_id == project_id)
        .order_by(desc(AIVisibilityCheck.checked_at)).limit(10)
    )).scalars().all()
    if not recent:
        return ok({"markdown": "Run some AI visibility checks first to receive recommendations."})
    try:
        md = await ai_visibility.suggestions(project, list(recent))
    except claude_service.ClaudeError as e:
        raise HTTPException(400, str(e))
    return ok({"markdown": md})
