import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, get_db
from models.audit import AuditIssue, AuditPage, AuditRun
from routers._helpers import get_project_or_404
from schemas.audit import AuditIssueOut, AuditPageOut, AuditRunOut, AuditRunRequest
from schemas.common import ok
from services.audit import run_audit, start_audit_run

router = APIRouter(prefix="/api/projects/{project_id}/audit", tags=["audit"])
log = logging.getLogger(__name__)


async def _run_audit_bg(run_id: uuid.UUID, run_pagespeed: bool):
    async with AsyncSessionLocal() as db:
        try:
            await run_audit(db, run_id, run_pagespeed=run_pagespeed)
        except Exception:
            log.exception("background audit failed for run=%s", run_id)


@router.post("/runs")
async def start_audit(
    project_id: uuid.UUID,
    payload: AuditRunRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger an audit asynchronously. Returns immediately with the run id."""
    await get_project_or_404(db, project_id)
    # Block parallel runs for same project
    in_flight = (await db.execute(
        select(AuditRun).where(AuditRun.project_id == project_id, AuditRun.status.in_(["pending", "running"]))
    )).scalar_one_or_none()
    if in_flight:
        raise HTTPException(409, "An audit is already running for this project")

    run_id = await start_audit_run(db, project_id)
    background.add_task(_run_audit_bg, run_id, payload.run_pagespeed)
    return ok({"run_id": str(run_id), "status": "pending"})


@router.get("/runs")
async def list_runs(
    project_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    rows = (await db.execute(
        select(AuditRun).where(AuditRun.project_id == project_id)
        .order_by(desc(AuditRun.created_at)).limit(limit)
    )).scalars().all()
    return ok([AuditRunOut.model_validate(r).model_dump(mode="json") for r in rows])


@router.get("/runs/latest")
async def latest_run(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await get_project_or_404(db, project_id)
    run = (await db.execute(
        select(AuditRun).where(AuditRun.project_id == project_id, AuditRun.status == "completed")
        .order_by(desc(AuditRun.completed_at)).limit(1)
    )).scalar_one_or_none()
    if not run:
        return ok(None)
    return ok(AuditRunOut.model_validate(run).model_dump(mode="json"))


@router.get("/runs/{run_id}")
async def get_run(project_id: uuid.UUID, run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await db.get(AuditRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Run not found")
    return ok(AuditRunOut.model_validate(run).model_dump(mode="json"))


@router.get("/runs/{run_id}/issues")
async def list_issues(
    project_id: uuid.UUID,
    run_id: uuid.UUID,
    severity: Optional[str] = Query(default=None, pattern="^(high|medium|low)$"),
    issue_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    run = await db.get(AuditRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Run not found")
    stmt = select(AuditIssue).where(AuditIssue.run_id == run_id)
    if severity:
        stmt = stmt.where(AuditIssue.severity == severity)
    if issue_type:
        stmt = stmt.where(AuditIssue.issue_type == issue_type)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(AuditIssue.severity, AuditIssue.issue_type).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()
    return ok({
        "items": [AuditIssueOut.model_validate(r).model_dump(mode="json") for r in rows],
        "page": page, "page_size": page_size, "total": total,
    })


@router.get("/runs/{run_id}/pages")
async def list_pages(
    project_id: uuid.UUID,
    run_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    run = await db.get(AuditRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Run not found")
    stmt = select(AuditPage).where(AuditPage.run_id == run_id)
    if search:
        stmt = stmt.where(AuditPage.url.ilike(f"%{search.lower()}%"))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(AuditPage.depth, AuditPage.url).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()
    return ok({
        "items": [AuditPageOut.model_validate(r).model_dump(mode="json") for r in rows],
        "page": page, "page_size": page_size, "total": total,
    })


@router.get("/runs/{run_id}/pages/{page_id}")
async def page_detail(
    project_id: uuid.UUID, run_id: uuid.UUID, page_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    p = await db.get(AuditPage, page_id)
    if not p or p.run_id != run_id:
        raise HTTPException(404, "Page not found")
    issues = (await db.execute(
        select(AuditIssue).where(AuditIssue.run_id == run_id, AuditIssue.url == p.url)
    )).scalars().all()
    return ok({
        "page": AuditPageOut.model_validate(p).model_dump(mode="json"),
        "issues": [AuditIssueOut.model_validate(i).model_dump(mode="json") for i in issues],
    })


@router.get("/runs/{run_id}/report.pdf")
async def report_pdf(project_id: uuid.UUID, run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await get_project_or_404(db, project_id)
    run = await db.get(AuditRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Run not found")
    if run.status != "completed":
        raise HTTPException(400, f"Run is not completed (status={run.status})")
    issues = (await db.execute(
        select(AuditIssue).where(AuditIssue.run_id == run_id)
    )).scalars().all()
    from services import audit_pdf
    pdf = audit_pdf.render(project, run, issues)
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="audit-{project.domain}-{run_id}.pdf"'},
    )
