"""AI Visibility tracker service.

For each tracked query, asks Claude as if it were a chat assistant, then runs a
second analysis pass to detect whether the project's brand/domain (or any
competitor) is mentioned, with sentiment.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ai_visibility import AIVisibilityCheck, AIVisibilityQuery
from models.project import Project
from services import claude_service

log = logging.getLogger(__name__)


def _brand_aliases(project: Project) -> List[str]:
    """Reasonable aliases the brand may be referred to by in an AI response."""
    parts = [project.name, project.domain]
    base = project.domain.split(".")[0]
    parts.extend([base, base.capitalize()])
    return list(dict.fromkeys([p for p in parts if p]))


async def run_check(db: AsyncSession, project: Project, query: AIVisibilityQuery) -> AIVisibilityCheck:
    response_text = await claude_service.ai_response(query.query)
    brand = project.name
    competitors = list(project.competitors or [])
    analysis = await claude_service.analyze_mention(response_text, brand, competitors)

    check = AIVisibilityCheck(
        query_id=query.id,
        provider="claude",
        response_text=response_text,
        brand_mentioned=bool(analysis.get("brand_mentioned")),
        mention_position=analysis.get("mention_position"),
        sentiment=analysis.get("sentiment"),
        sentiment_score=analysis.get("sentiment_score"),
        competitors_mentioned=analysis.get("competitors_mentioned") or [],
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check


async def run_for_project(db: AsyncSession, project_id: uuid.UUID) -> int:
    project = await db.get(Project, project_id)
    if not project:
        return 0
    queries = (await db.execute(
        select(AIVisibilityQuery)
        .where(AIVisibilityQuery.project_id == project_id, AIVisibilityQuery.enabled.is_(True))
    )).scalars().all()
    count = 0
    for q in queries:
        try:
            await run_check(db, project, q)
            count += 1
        except Exception as e:
            log.warning("AI visibility check failed for query=%s: %s", q.query, e)
    return count


async def overview(db: AsyncSession, project_id: uuid.UUID, days: int = 30) -> dict:
    """Aggregate metrics: mention rate, avg sentiment score, top competitors."""
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    rows = (await db.execute(
        select(AIVisibilityCheck, AIVisibilityQuery)
        .join(AIVisibilityQuery, AIVisibilityQuery.id == AIVisibilityCheck.query_id)
        .where(AIVisibilityQuery.project_id == project_id, AIVisibilityCheck.checked_at >= since)
    )).all()
    if not rows:
        return {
            "mention_rate": 0.0, "checks": 0, "avg_sentiment_score": None,
            "queries_tracked": 0, "competitor_share": [],
        }
    total = len(rows)
    mentions = sum(1 for c, _ in rows if c.brand_mentioned)
    sentiments = [c.sentiment_score for c, _ in rows if c.sentiment_score is not None]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None

    comp_counter: dict = {}
    for c, _ in rows:
        for comp in c.competitors_mentioned or []:
            comp_counter[comp] = comp_counter.get(comp, 0) + 1
    competitor_share = sorted(
        ({"competitor": k, "mentions": v, "share": round(v / total, 3)} for k, v in comp_counter.items()),
        key=lambda x: -x["mentions"],
    )[:10]

    queries_tracked = (await db.execute(
        select(func.count()).select_from(AIVisibilityQuery)
        .where(AIVisibilityQuery.project_id == project_id, AIVisibilityQuery.enabled.is_(True))
    )).scalar_one()

    return {
        "mention_rate": round(mentions / total, 3),
        "checks": total,
        "avg_sentiment_score": round(avg_sentiment, 3) if avg_sentiment is not None else None,
        "queries_tracked": queries_tracked,
        "competitor_share": competitor_share,
        "days": days,
    }


async def history(db: AsyncSession, project_id: uuid.UUID, days: int = 90) -> List[dict]:
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    rows = (await db.execute(
        select(AIVisibilityCheck.checked_at, AIVisibilityCheck.brand_mentioned, AIVisibilityCheck.sentiment_score)
        .join(AIVisibilityQuery, AIVisibilityQuery.id == AIVisibilityCheck.query_id)
        .where(AIVisibilityQuery.project_id == project_id, AIVisibilityCheck.checked_at >= since)
        .order_by(AIVisibilityCheck.checked_at.asc())
    )).all()

    by_day: dict = {}
    for checked_at, mentioned, sentiment in rows:
        d = checked_at.date().isoformat()
        bucket = by_day.setdefault(d, {"date": d, "checks": 0, "mentions": 0, "sentiment_sum": 0.0, "sentiment_n": 0})
        bucket["checks"] += 1
        if mentioned:
            bucket["mentions"] += 1
        if sentiment is not None:
            bucket["sentiment_sum"] += sentiment
            bucket["sentiment_n"] += 1

    out = []
    for d in sorted(by_day):
        b = by_day[d]
        out.append({
            "date": d,
            "checks": b["checks"],
            "mentions": b["mentions"],
            "mention_rate": round(b["mentions"] / b["checks"], 3) if b["checks"] else 0.0,
            "avg_sentiment_score": round(b["sentiment_sum"] / b["sentiment_n"], 3) if b["sentiment_n"] else None,
        })
    return out


async def suggestions(project: Project, recent_responses: List[str]) -> str:
    """Ask Claude to recommend actions to improve AI visibility."""
    blob = "\n---\n".join(r[:1500] for r in recent_responses[:10])
    system = (
        "You are an SEO and AI-search optimization expert. Output concise, actionable bullet points "
        "for improving brand visibility in AI-generated responses (LLM SEO / GEO)."
    )
    user = f"""Brand: {project.name}
Domain: {project.domain}
Competitors: {', '.join(project.competitors or []) or '(none)'}

Recent AI responses to tracked queries (truncated):
{blob}

Provide 5-8 specific, prioritized recommendations to increase the brand's mention rate
and sentiment in future AI responses. Focus on entity SEO, structured data, citations,
content moats, comparison pages, and digital PR. Output as a markdown list, nothing else."""
    return await claude_service._complete(system, user, max_tokens=1500)
