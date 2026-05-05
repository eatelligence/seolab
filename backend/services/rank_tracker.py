"""Rank tracker core logic. Used both by API endpoints (immediate check) and by
the Celery scheduled task (daily check)."""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.keyword import Keyword
from models.project import Project
from models.ranking import Ranking
from services import dataforseo

log = logging.getLogger(__name__)

ALERT_DELTA_THRESHOLD = 5  # |delta| > 5 spots triggers an alert


async def check_keyword(db: AsyncSession, project: Project, keyword: Keyword) -> Ranking:
    """Run a SERP query, persist a Ranking row, return it."""
    competitors = list(project.competitors or [])
    serp = await dataforseo.serp_organic(
        keyword=keyword.keyword,
        country=keyword.country,
        target_domain=project.domain,
    )
    target_position = serp.get("target_position")
    target_url = serp.get("target_url")
    serp_features = serp.get("serp_features") or []
    items = serp.get("items") or []

    competitor_positions: dict = {}
    for c in competitors:
        c_norm = c.lower().lstrip(".")
        for it in items:
            domain = (it.get("domain") or "").lower()
            if domain == c_norm or domain.endswith("." + c_norm):
                competitor_positions[c_norm] = it.get("rank_absolute") or it.get("rank_group")
                break

    ranking = Ranking(
        keyword_id=keyword.id,
        position=target_position,
        url=target_url,
        serp_features=serp_features,
        competitor_positions=competitor_positions,
    )
    db.add(ranking)
    await db.commit()
    await db.refresh(ranking)
    return ranking


async def check_project(db: AsyncSession, project_id: uuid.UUID) -> int:
    """Check rankings for all tracked keywords of a project. Returns count checked."""
    project = await db.get(Project, project_id)
    if not project:
        log.warning("project %s not found", project_id)
        return 0
    rows = (await db.execute(
        select(Keyword).where(Keyword.project_id == project_id, Keyword.tracked.is_(True))
    )).scalars().all()
    count = 0
    for kw in rows:
        try:
            await check_keyword(db, project, kw)
            count += 1
        except Exception as e:
            log.warning("rank check failed for kw=%s: %s", kw.keyword, e)
    return count


def visibility_score(positions: List[Optional[int]]) -> float:
    """SEMrush-style visibility: average CTR from a position-CTR curve, scaled 0-100."""
    # Approximate curve.
    ctr = {1: 0.30, 2: 0.18, 3: 0.12, 4: 0.08, 5: 0.06, 6: 0.04, 7: 0.03, 8: 0.025,
           9: 0.02, 10: 0.018}
    total = 0.0
    n = 0
    for p in positions:
        n += 1
        if p is None:
            continue
        if p <= 10:
            total += ctr.get(p, 0.018)
        elif p <= 20:
            total += 0.005
        elif p <= 50:
            total += 0.001
    if n == 0:
        return 0.0
    return round((total / n) * 100, 2)
