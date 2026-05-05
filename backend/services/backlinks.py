"""Backlink service: orchestrates DataForSEO calls + persistence + toxic detection."""

from __future__ import annotations

import datetime as dt
import logging
import re
import uuid
from typing import Dict, List

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.backlink import Backlink, BacklinkSnapshot
from models.project import Project
from services import dataforseo, openpr

log = logging.getLogger(__name__)

SPAMMY_TOKENS = re.compile(
    r"\b(viagra|cialis|casino|porn|sex|loan|forex|crypto-?signals|escort|payday|bitcoin\s*doubler|free\s*download)\b",
    re.IGNORECASE,
)


def _toxic_score(domain_rating: float | None, anchor: str | None, dofollow: bool) -> float:
    score = 0.0
    if domain_rating is None or domain_rating < 10:
        score += 0.4
    elif domain_rating < 20:
        score += 0.2
    if anchor and SPAMMY_TOKENS.search(anchor):
        score += 0.5
    if not dofollow:
        score *= 0.7  # nofollow links matter less
    return min(round(score, 2), 1.0)


async def overview(target: str) -> dict:
    summary = await dataforseo.backlinks_summary(target)
    pr = await openpr.domain_authority([target])
    return {
        "target": target,
        "total_backlinks": summary.get("backlinks") or 0,
        "referring_domains": summary.get("referring_domains") or 0,
        "referring_main_domains": summary.get("referring_main_domains") or 0,
        "dofollow": summary.get("backlinks_dofollow") or 0,
        "nofollow": (summary.get("backlinks") or 0) - (summary.get("backlinks_dofollow") or 0),
        "broken_pages": summary.get("broken_pages") or 0,
        "broken_backlinks": summary.get("broken_backlinks") or 0,
        "rank": summary.get("rank"),
        "domain_authority": pr.get(target.lower(), 0.0),
    }


async def backlinks_list(target: str, limit: int = 100) -> List[dict]:
    items = await dataforseo.backlinks_list(target, limit=limit)
    out = []
    for it in items:
        out.append({
            "source_url": it.get("url_from"),
            "source_domain": it.get("domain_from"),
            "target_url": it.get("url_to"),
            "anchor": it.get("anchor"),
            "is_dofollow": (it.get("dofollow") is True),
            "first_seen": it.get("first_seen"),
            "last_seen": it.get("last_visited"),
            "rank": it.get("rank"),
            "page_traffic": (it.get("page_summary") or {}).get("page_keywords"),
        })
    return out


async def referring_domains(target: str, limit: int = 100) -> List[dict]:
    items = await dataforseo.referring_domains(target, limit=limit)
    out = []
    for it in items:
        out.append({
            "domain": it.get("domain"),
            "rank": it.get("rank"),
            "backlinks": it.get("backlinks"),
            "referring_pages": it.get("referring_pages"),
            "first_seen": it.get("first_seen"),
            "last_seen": it.get("last_visited"),
            "is_lost": it.get("is_lost", False),
        })
    return out


async def anchor_distribution(target: str, limit: int = 100) -> List[dict]:
    items = await dataforseo.anchor_distribution(target, limit=limit)
    out = []
    total = sum((i.get("backlinks") or 0) for i in items) or 1
    for it in items:
        bl = it.get("backlinks") or 0
        out.append({
            "anchor": it.get("anchor"),
            "backlinks": bl,
            "referring_domains": it.get("referring_domains"),
            "share": round(bl / total, 4),
        })
    return out


async def toxic_links(target: str, limit: int = 200) -> List[dict]:
    """Heuristic toxic detection. Scores each backlink and returns the worst."""
    items = await dataforseo.backlinks_list(target, limit=limit)
    domains = list({(it.get("domain_from") or "").lower() for it in items if it.get("domain_from")})
    pr = await openpr.domain_authority(domains) if domains else {}

    enriched = []
    for it in items:
        d = (it.get("domain_from") or "").lower()
        dr = pr.get(d, 0.0)
        anchor = it.get("anchor")
        dofollow = it.get("dofollow") is True
        score = _toxic_score(dr, anchor, dofollow)
        enriched.append({
            "source_url": it.get("url_from"),
            "source_domain": d,
            "target_url": it.get("url_to"),
            "anchor": anchor,
            "is_dofollow": dofollow,
            "domain_rating": dr,
            "toxic_score": score,
        })
    enriched.sort(key=lambda x: x["toxic_score"], reverse=True)
    return [e for e in enriched if e["toxic_score"] >= 0.4][:100]


async def take_snapshot(db: AsyncSession, project: Project) -> BacklinkSnapshot:
    """Pull current backlink overview and persist a daily snapshot row."""
    summary = await dataforseo.backlinks_summary(project.domain)
    pr = await openpr.domain_authority([project.domain])
    today = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    existing = (await db.execute(
        select(BacklinkSnapshot).where(
            BacklinkSnapshot.project_id == project.id,
            BacklinkSnapshot.snapshot_date == today,
        )
    )).scalar_one_or_none()

    # Compute new/lost from yesterday
    yesterday = today - dt.timedelta(days=1)
    prev = (await db.execute(
        select(BacklinkSnapshot).where(
            BacklinkSnapshot.project_id == project.id,
            BacklinkSnapshot.snapshot_date == yesterday,
        )
    )).scalar_one_or_none()
    total = summary.get("backlinks") or 0
    delta = total - (prev.total_backlinks if prev else total)
    new_count = max(delta, 0)
    lost_count = max(-delta, 0)

    snap = existing or BacklinkSnapshot(project_id=project.id, snapshot_date=today)
    snap.total_backlinks = total
    snap.referring_domains = summary.get("referring_domains") or 0
    snap.dofollow_count = summary.get("backlinks_dofollow") or 0
    snap.nofollow_count = total - snap.dofollow_count
    snap.new_count = new_count
    snap.lost_count = lost_count
    snap.domain_rating = pr.get(project.domain.lower(), 0.0)
    if existing is None:
        db.add(snap)
    await db.commit()
    await db.refresh(snap)
    return snap


async def history(db: AsyncSession, project_id: uuid.UUID, days: int = 90) -> List[dict]:
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    rows = (await db.execute(
        select(BacklinkSnapshot)
        .where(BacklinkSnapshot.project_id == project_id, BacklinkSnapshot.snapshot_date >= since)
        .order_by(BacklinkSnapshot.snapshot_date.asc())
    )).scalars().all()
    return [{
        "date": r.snapshot_date.date().isoformat(),
        "total_backlinks": r.total_backlinks,
        "referring_domains": r.referring_domains,
        "dofollow": r.dofollow_count,
        "nofollow": r.nofollow_count,
        "new": r.new_count,
        "lost": r.lost_count,
        "domain_rating": r.domain_rating,
    } for r in rows]
