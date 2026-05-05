import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.audit import AuditRun
from models.backlink import BacklinkSnapshot
from models.keyword import Keyword
from models.ranking import Ranking
from routers._helpers import get_project_or_404
from schemas.common import ok
from services import gsc_service, openpr
from services.gsc_service import GSCError
from services.rank_tracker import visibility_score

router = APIRouter(prefix="/api/projects/{project_id}", tags=["dashboard"])
log = logging.getLogger(__name__)


@router.get("/dashboard")
async def dashboard(
    project_id: uuid.UUID,
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(db, project_id)
    out: Dict[str, Any] = {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "domain": project.domain,
            "country": project.country,
            "gsc_connected": bool(project.gsc_property),
        },
        "metrics": {},
        "gsc_traffic": None,
        "top_keywords": [],
        "top_pages": [],
        "rank_overview": {"avg_position": None, "visibility": None, "tracked_count": 0},
        "audit": {"latest_score": None, "issues_count": 0},
        "backlinks": {"total": 0, "referring_domains": 0, "domain_rating": None},
    }

    # ----- GSC data (optional) -----
    if project.gsc_property:
        try:
            perf = await gsc_service.performance_summary(db, project_id, project.gsc_property, days)
            out["gsc_traffic"] = perf
            out["metrics"]["organic_clicks"] = perf["totals"]["clicks"]
            out["metrics"]["organic_impressions"] = perf["totals"]["impressions"]
            out["top_keywords"] = await gsc_service.top_keywords(
                db, project_id, project.gsc_property, days=28, limit=10
            )
            out["top_pages"] = await gsc_service.top_pages(
                db, project_id, project.gsc_property, days=28, limit=5
            )
        except GSCError as e:
            log.info("GSC unavailable for project=%s: %s", project_id, e)

    # ----- Rank overview -----
    keyword_count = (await db.execute(
        select(func.count()).select_from(Keyword).where(Keyword.project_id == project_id)
    )).scalar_one()
    tracked_keywords = (await db.execute(
        select(Keyword).where(Keyword.project_id == project_id, Keyword.tracked.is_(True))
    )).scalars().all()
    positions = []
    for kw in tracked_keywords:
        latest = (await db.execute(
            select(Ranking).where(Ranking.keyword_id == kw.id)
            .order_by(desc(Ranking.checked_at)).limit(1)
        )).scalar_one_or_none()
        positions.append(latest.position if latest else None)
    valid = [p for p in positions if p is not None]
    out["rank_overview"] = {
        "tracked_count": len(tracked_keywords),
        "avg_position": round(sum(valid) / len(valid), 2) if valid else None,
        "visibility": visibility_score(positions),
    }
    out["metrics"]["total_keywords"] = keyword_count

    # ----- Audit -----
    last_audit = (await db.execute(
        select(AuditRun).where(AuditRun.project_id == project_id, AuditRun.status == "completed")
        .order_by(desc(AuditRun.completed_at)).limit(1)
    )).scalar_one_or_none()
    if last_audit:
        from models.audit import AuditIssue
        issues = (await db.execute(
            select(func.count()).select_from(AuditIssue).where(AuditIssue.run_id == last_audit.id)
        )).scalar_one()
        out["audit"] = {"latest_score": last_audit.health_score, "issues_count": issues}

    # ----- Backlinks (latest snapshot) -----
    last_snap = (await db.execute(
        select(BacklinkSnapshot).where(BacklinkSnapshot.project_id == project_id)
        .order_by(desc(BacklinkSnapshot.snapshot_date)).limit(1)
    )).scalar_one_or_none()
    if last_snap:
        out["backlinks"] = {
            "total": last_snap.total_backlinks,
            "referring_domains": last_snap.referring_domains,
            "domain_rating": last_snap.domain_rating,
        }

    # ----- Domain authority (Open PageRank) -----
    try:
        pr = await openpr.domain_authority([project.domain])
        out["metrics"]["domain_authority"] = pr.get(project.domain.lower(), 0.0)
    except Exception as e:
        log.info("OpenPageRank unavailable: %s", e)
        out["metrics"]["domain_authority"] = None

    return ok(out)
