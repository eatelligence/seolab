import datetime as dt
import logging
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.keyword import Keyword
from models.ranking import Ranking
from routers._helpers import get_project_or_404
from schemas.common import ok
from schemas.ranking import RankingAlert, RankingPoint, TrackedKeywordRow, VisibilityPoint
from services.rank_tracker import ALERT_DELTA_THRESHOLD, check_project, visibility_score

router = APIRouter(prefix="/api/projects/{project_id}", tags=["rank-tracker"])
log = logging.getLogger(__name__)


@router.get("/rankings")
async def list_rankings(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Latest ranking per tracked keyword + delta vs the previous check."""
    await get_project_or_404(db, project_id)
    keywords = (await db.execute(
        select(Keyword).where(Keyword.project_id == project_id, Keyword.tracked.is_(True))
    )).scalars().all()

    rows: List[dict] = []
    for kw in keywords:
        recent = (await db.execute(
            select(Ranking).where(Ranking.keyword_id == kw.id)
            .order_by(desc(Ranking.checked_at)).limit(2)
        )).scalars().all()
        current = recent[0] if recent else None
        previous = recent[1] if len(recent) > 1 else None
        delta = None
        if current and previous and current.position is not None and previous.position is not None:
            delta = previous.position - current.position  # positive = moved up
        rows.append(TrackedKeywordRow(
            keyword_id=kw.id,
            keyword=kw.keyword,
            country=kw.country,
            search_volume=kw.search_volume,
            current_position=current.position if current else None,
            previous_position=previous.position if previous else None,
            delta=delta,
            url=current.url if current else None,
            serp_features=current.serp_features if current else [],
            last_checked=current.checked_at if current else None,
        ).model_dump(mode="json"))
    return ok(rows)


@router.post("/rankings/check")
async def check_now(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Trigger an immediate rank check for all tracked keywords (synchronous)."""
    await get_project_or_404(db, project_id)
    n = await check_project(db, project_id)
    return ok({"checked": n})


@router.post("/keywords/{keyword_id}/track")
async def start_tracking(
    project_id: uuid.UUID, keyword_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    kw = await db.get(Keyword, keyword_id)
    if not kw or kw.project_id != project_id:
        raise HTTPException(404, "Keyword not found")
    kw.tracked = True
    await db.commit()
    return ok({"keyword_id": str(kw.id), "tracked": True})


@router.delete("/keywords/{keyword_id}/track")
async def stop_tracking(
    project_id: uuid.UUID, keyword_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    kw = await db.get(Keyword, keyword_id)
    if not kw or kw.project_id != project_id:
        raise HTTPException(404, "Keyword not found")
    kw.tracked = False
    await db.commit()
    return ok({"keyword_id": str(kw.id), "tracked": False})


@router.get("/keywords/{keyword_id}/history")
async def position_history(
    project_id: uuid.UUID,
    keyword_id: uuid.UUID,
    days: int = Query(default=90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    kw = await db.get(Keyword, keyword_id)
    if not kw or kw.project_id != project_id:
        raise HTTPException(404, "Keyword not found")
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    rows = (await db.execute(
        select(Ranking).where(Ranking.keyword_id == keyword_id, Ranking.checked_at >= since)
        .order_by(Ranking.checked_at.asc())
    )).scalars().all()
    return ok([RankingPoint.model_validate(r).model_dump(mode="json") for r in rows])


@router.get("/visibility")
async def visibility_trend(
    project_id: uuid.UUID,
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Project-level visibility score per day."""
    await get_project_or_404(db, project_id)
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    rows = (await db.execute(
        select(Ranking, Keyword)
        .join(Keyword, Keyword.id == Ranking.keyword_id)
        .where(Keyword.project_id == project_id, Keyword.tracked.is_(True),
               Ranking.checked_at >= since)
        .order_by(Ranking.checked_at.asc())
    )).all()

    by_day: Dict[str, List[Optional[int]]] = defaultdict(list)
    for ranking, _kw in rows:
        d = ranking.checked_at.date().isoformat()
        by_day[d].append(ranking.position)

    points: List[dict] = []
    for d, positions in sorted(by_day.items()):
        valid = [p for p in positions if p is not None]
        avg = round(sum(valid) / len(valid), 2) if valid else None
        points.append(VisibilityPoint(
            date=d, score=visibility_score(positions),
            keywords_tracked=len(positions), avg_position=avg,
        ).model_dump(mode="json"))
    return ok(points)


@router.get("/rankings/alerts")
async def alerts(
    project_id: uuid.UUID,
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Significant rank changes (|delta| > threshold) over the last N days."""
    await get_project_or_404(db, project_id)
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    keywords = (await db.execute(
        select(Keyword).where(Keyword.project_id == project_id, Keyword.tracked.is_(True))
    )).scalars().all()

    out: List[dict] = []
    for kw in keywords:
        rows = (await db.execute(
            select(Ranking).where(Ranking.keyword_id == kw.id, Ranking.checked_at >= since)
            .order_by(Ranking.checked_at.asc())
        )).scalars().all()
        prev = None
        for r in rows:
            if prev is not None and r.position is not None and prev.position is not None:
                delta = prev.position - r.position
                if abs(delta) > ALERT_DELTA_THRESHOLD:
                    out.append(RankingAlert(
                        keyword_id=kw.id, keyword=kw.keyword,
                        previous_position=prev.position, current_position=r.position,
                        delta=delta, direction="up" if delta > 0 else "down",
                        checked_at=r.checked_at,
                    ).model_dump(mode="json"))
            prev = r
    out.sort(key=lambda a: a["checked_at"], reverse=True)
    return ok(out)
