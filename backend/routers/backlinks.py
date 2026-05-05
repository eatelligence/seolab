import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers._helpers import get_project_or_404
from schemas.common import ok
from services import backlinks as svc
from services.dataforseo import DataForSEOError

router = APIRouter(prefix="/api/projects/{project_id}/backlinks", tags=["backlinks"])
log = logging.getLogger(__name__)


@router.get("/overview")
async def overview(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await get_project_or_404(db, project_id)
    try:
        return ok(await svc.overview(project.domain))
    except DataForSEOError as e:
        raise HTTPException(400, str(e))


@router.get("/list")
async def list_backlinks(
    project_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    try:
        return ok(await svc.backlinks_list(project.domain, limit=limit))
    except DataForSEOError as e:
        raise HTTPException(400, str(e))


@router.get("/refdomains")
async def refdomains(
    project_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    try:
        return ok(await svc.referring_domains(project.domain, limit=limit))
    except DataForSEOError as e:
        raise HTTPException(400, str(e))


@router.get("/anchors")
async def anchors(
    project_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    try:
        return ok(await svc.anchor_distribution(project.domain, limit=limit))
    except DataForSEOError as e:
        raise HTTPException(400, str(e))


@router.get("/toxic")
async def toxic(
    project_id: uuid.UUID,
    limit: int = Query(default=200, ge=10, le=1000),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    try:
        return ok(await svc.toxic_links(project.domain, limit=limit))
    except DataForSEOError as e:
        raise HTTPException(400, str(e))


@router.get("/history")
async def history(
    project_id: uuid.UUID,
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    return ok(await svc.history(db, project_id, days=days))


@router.post("/snapshot")
async def take_snapshot(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await get_project_or_404(db, project_id)
    try:
        snap = await svc.take_snapshot(db, project)
    except DataForSEOError as e:
        raise HTTPException(400, str(e))
    return ok({
        "date": snap.snapshot_date.date().isoformat(),
        "total_backlinks": snap.total_backlinks,
        "referring_domains": snap.referring_domains,
        "domain_rating": snap.domain_rating,
    })
