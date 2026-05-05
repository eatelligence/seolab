import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.gsc import GSCToken
from models.project import Project
from routers._helpers import get_project_or_404
from schemas.common import ok
from services import gsc_service
from services.gsc_service import GSCError

router = APIRouter(prefix="/api", tags=["gsc"])
log = logging.getLogger(__name__)


@router.get("/projects/{project_id}/gsc/auth-url")
async def get_auth_url(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await get_project_or_404(db, project_id)
    try:
        url = gsc_service.authorization_url(project_id)
    except GSCError as e:
        raise HTTPException(400, str(e))
    return ok({"auth_url": url})


@router.get("/gsc/oauth/callback")
async def oauth_callback(
    code: str = Query(...), state: str = Query(...), db: AsyncSession = Depends(get_db)
):
    try:
        project_id = uuid.UUID(state)
    except ValueError:
        raise HTTPException(400, "Invalid state")
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    try:
        await gsc_service.exchange_code(db, project_id, code)
    except GSCError as e:
        raise HTTPException(400, f"GSC connection failed: {e}")
    # Redirect to frontend project settings page (added in M4).
    return RedirectResponse(url=f"/?gsc=connected&project={project_id}", status_code=302)


@router.get("/projects/{project_id}/gsc/status")
async def gsc_status(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await get_project_or_404(db, project_id)
    token = (await db.execute(
        select(GSCToken).where(GSCToken.project_id == project_id)
    )).scalar_one_or_none()
    return ok({"connected": token is not None})


@router.get("/projects/{project_id}/gsc/properties")
async def list_props(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await get_project_or_404(db, project_id)
    try:
        props = await gsc_service.list_properties(db, project_id)
    except GSCError as e:
        raise HTTPException(400, str(e))
    return ok([{"site_url": p.get("siteUrl"), "permission_level": p.get("permissionLevel")} for p in props])


@router.post("/projects/{project_id}/gsc/property")
async def set_property(
    project_id: uuid.UUID, payload: dict, db: AsyncSession = Depends(get_db)
):
    project = await get_project_or_404(db, project_id)
    site_url = (payload or {}).get("site_url")
    if not site_url:
        raise HTTPException(400, "site_url required")
    project.gsc_property = site_url
    await db.commit()
    return ok({"gsc_property": site_url})


@router.delete("/projects/{project_id}/gsc")
async def disconnect(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await get_project_or_404(db, project_id)
    token = (await db.execute(
        select(GSCToken).where(GSCToken.project_id == project_id)
    )).scalar_one_or_none()
    if token:
        await db.delete(token)
    project.gsc_property = None
    await db.commit()
    return ok({"disconnected": True})


@router.get("/projects/{project_id}/gsc/performance")
async def performance(
    project_id: uuid.UUID,
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    if not project.gsc_property:
        raise HTTPException(400, "GSC property not configured for this project")
    try:
        return ok(await gsc_service.performance_summary(db, project_id, project.gsc_property, days))
    except GSCError as e:
        raise HTTPException(400, str(e))


@router.get("/projects/{project_id}/gsc/top-keywords")
async def gsc_top_keywords(
    project_id: uuid.UUID,
    days: int = Query(default=28, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    if not project.gsc_property:
        raise HTTPException(400, "GSC property not configured")
    try:
        return ok(await gsc_service.top_keywords(db, project_id, project.gsc_property, days, limit))
    except GSCError as e:
        raise HTTPException(400, str(e))


@router.get("/projects/{project_id}/gsc/top-pages")
async def gsc_top_pages(
    project_id: uuid.UUID,
    days: int = Query(default=28, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    if not project.gsc_property:
        raise HTTPException(400, "GSC property not configured")
    try:
        return ok(await gsc_service.top_pages(db, project_id, project.gsc_property, days, limit))
    except GSCError as e:
        raise HTTPException(400, str(e))
