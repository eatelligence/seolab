"""Site-audit engine. Runs the crawler then applies 14 SEO checks.

Severity weights determine the health score: HIGH=5, MEDIUM=2, LOW=1. The score
starts at 100 and is decremented by ``min(40, total_penalty / pages_crawled * 10)``
so a small site with one issue isn't punished as harshly as a large one with the
same issue.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit import AuditIssue, AuditPage, AuditRun
from models.project import Project
from services import pagespeed
from services.crawler import CrawledPage, Crawler

log = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {"high": 5, "medium": 2, "low": 1}
THIN_CONTENT_WORDS = 300
MAX_DEPTH_OK = 4
LARGE_IMAGE_BYTES = 500 * 1024
SLOW_PAGE_MS = 3000
PSI_SAMPLE = 5  # how many pages to send to PageSpeed Insights


def _add(issues: List[dict], issue_type: str, severity: str, url: str, **details):
    issues.append({"issue_type": issue_type, "severity": severity, "url": url, "details": details})


def _check_duplicates(pages: List[CrawledPage], issues: List[dict]):
    titles: Dict[str, List[CrawledPage]] = defaultdict(list)
    metas: Dict[str, List[CrawledPage]] = defaultdict(list)
    for p in pages:
        if p.title:
            titles[p.title.strip().lower()].append(p)
        if p.meta_description:
            metas[p.meta_description.strip().lower()].append(p)
    for t, group in titles.items():
        if len(group) > 1:
            for p in group:
                _add(issues, "duplicate_title", "medium", p.final_url, title=p.title, occurrences=len(group))
    for m, group in metas.items():
        if len(group) > 1:
            for p in group:
                _add(issues, "duplicate_meta_description", "medium", p.final_url,
                     meta=p.meta_description, occurrences=len(group))


def _per_page_checks(pages: List[CrawledPage], broken_links, issues: List[dict]):
    for p in pages:
        if p.status_code is None or p.error == "fetch_failed":
            _add(issues, "fetch_failed", "high", p.url)
            continue
        if p.status_code >= 500:
            _add(issues, "server_error", "high", p.final_url, status=p.status_code)
            continue
        if p.status_code >= 400:
            _add(issues, "client_error", "high", p.final_url, status=p.status_code)
            continue

        if not p.title:
            _add(issues, "missing_title", "high", p.final_url)
        elif len(p.title) > 60:
            _add(issues, "long_title", "low", p.final_url, length=len(p.title))
        elif len(p.title) < 20:
            _add(issues, "short_title", "low", p.final_url, length=len(p.title))

        if not p.meta_description:
            _add(issues, "missing_meta_description", "medium", p.final_url)
        elif len(p.meta_description) > 160:
            _add(issues, "long_meta_description", "low", p.final_url, length=len(p.meta_description))

        if p.h1_count == 0:
            _add(issues, "missing_h1", "high", p.final_url)
        elif p.h1_count > 1:
            _add(issues, "multiple_h1", "medium", p.final_url, count=p.h1_count)

        if p.word_count < THIN_CONTENT_WORDS:
            _add(issues, "thin_content", "medium", p.final_url, words=p.word_count)

        if not p.canonical:
            _add(issues, "missing_canonical", "low", p.final_url)

        if not p.is_https:
            _add(issues, "not_https", "high", p.final_url)

        if not p.has_structured_data:
            _add(issues, "missing_structured_data", "low", p.final_url)

        if p.depth > MAX_DEPTH_OK:
            _add(issues, "deep_crawl_depth", "low", p.final_url, depth=p.depth)

        if len(p.redirect_chain) >= 2:
            _add(issues, "redirect_chain", "medium", p.url,
                 chain=p.redirect_chain + [p.final_url], length=len(p.redirect_chain) + 1)

        # Image checks
        for img in p.images:
            if not img.get("alt"):
                _add(issues, "image_missing_alt", "low", p.final_url, src=img["src"])
            if img.get("bytes") and img["bytes"] > LARGE_IMAGE_BYTES:
                _add(issues, "large_image", "medium", p.final_url,
                     src=img["src"], bytes=img["bytes"])

        if p.load_time_ms and p.load_time_ms > SLOW_PAGE_MS:
            _add(issues, "slow_page", "medium", p.final_url, load_time_ms=p.load_time_ms)

    for source, target, status in broken_links:
        _add(issues, "broken_internal_link", "high", source, target=target, status=status)


async def _run_pagespeed_sample(pages: List[CrawledPage], issues: List[dict]):
    """Sample N pages and run PSI to surface real Core Web Vitals failures."""
    sample = sorted(
        [p for p in pages if p.status_code == 200 and p.word_count >= 100],
        key=lambda p: -p.word_count,
    )[:PSI_SAMPLE]
    for page in sample:
        try:
            result = await pagespeed.analyze(page.final_url, strategy="mobile")
            lab = result.get("lab", {})
            field = result.get("field", {})
            lcp = field.get("lcp_ms") or lab.get("lcp_ms")
            cls = field.get("cls") or lab.get("cls")
            inp = field.get("inp_ms")
            score = result.get("performance_score")

            if score is not None and score < 50:
                _add(issues, "low_performance_score", "high", page.final_url, score=score)
            elif score is not None and score < 70:
                _add(issues, "mediocre_performance_score", "medium", page.final_url, score=score)

            if lcp and lcp > 2500:
                _add(issues, "cwv_lcp_fail", "high" if lcp > 4000 else "medium",
                     page.final_url, lcp_ms=int(lcp))
            if cls is not None and cls > 0.1:
                _add(issues, "cwv_cls_fail", "high" if cls > 0.25 else "medium",
                     page.final_url, cls=cls)
            if inp and inp > 200:
                _add(issues, "cwv_inp_fail", "high" if inp > 500 else "medium",
                     page.final_url, inp_ms=int(inp))
        except Exception as e:
            log.warning("PSI failed for %s: %s", page.final_url, e)


def _compute_health_score(issues: List[dict], pages_crawled: int) -> int:
    if pages_crawled <= 0:
        return 0
    penalty = sum(SEVERITY_WEIGHTS.get(i["severity"], 1) for i in issues)
    norm = min(70, (penalty / max(pages_crawled, 1)) * 8)
    return max(0, int(round(100 - norm)))


def _summary(issues: List[dict]) -> dict:
    by_type: Dict[str, int] = defaultdict(int)
    by_severity: Dict[str, int] = defaultdict(int)
    for i in issues:
        by_type[i["issue_type"]] += 1
        by_severity[i["severity"]] += 1
    return {"by_type": dict(by_type), "by_severity": dict(by_severity), "total": len(issues)}


async def start_audit_run(db: AsyncSession, project_id: uuid.UUID) -> uuid.UUID:
    """Create a pending AuditRun row and return its id. The actual crawl is
    performed by ``run_audit`` against this id.
    """
    run = AuditRun(project_id=project_id, status="pending")
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run.id


async def run_audit(
    db: AsyncSession,
    run_id: uuid.UUID,
    run_pagespeed: bool = True,
) -> AuditRun:
    """Drive an existing pending/running AuditRun row to completion in place.
    Single source of truth for the row — no duplicates."""
    run = await db.get(AuditRun, run_id)
    if not run:
        raise ValueError(f"AuditRun {run_id} not found")

    project = await db.get(Project, run.project_id)
    if not project:
        run.status = "failed"
        run.error = f"Project {run.project_id} not found"
        run.completed_at = dt.datetime.now(dt.timezone.utc)
        await db.commit()
        raise ValueError(f"Project {run.project_id} not found")

    run.status = "running"
    run.started_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()

    try:
        crawler = Crawler(root_url=project.domain)
        crawl = await crawler.run()
        pages = crawl.pages

        # Persist AuditPage rows
        for p in pages:
            db.add(AuditPage(
                run_id=run.id,
                url=p.final_url or p.url,
                status_code=p.status_code,
                title=p.title,
                meta_description=p.meta_description,
                h1_count=p.h1_count,
                word_count=p.word_count,
                depth=p.depth,
                load_time_ms=p.load_time_ms,
                canonical=p.canonical,
                is_https=p.is_https,
                data={
                    "redirect_chain": p.redirect_chain,
                    "links_internal_count": len(p.links_internal),
                    "links_external_count": len(p.links_external),
                    "images_count": len(p.images),
                    "has_structured_data": p.has_structured_data,
                    "error": p.error,
                },
            ))

        issues: List[dict] = []
        _check_duplicates(pages, issues)
        _per_page_checks(pages, crawl.broken_links, issues)
        if run_pagespeed:
            await _run_pagespeed_sample(pages, issues)

        for i in issues:
            db.add(AuditIssue(
                run_id=run.id,
                issue_type=i["issue_type"],
                severity=i["severity"],
                url=i["url"],
                details=i.get("details") or {},
            ))

        run.pages_crawled = len(pages)
        run.health_score = _compute_health_score(issues, len(pages))
        run.summary = _summary(issues)
        run.status = "completed"
        run.completed_at = dt.datetime.now(dt.timezone.utc)
        await db.commit()
        await db.refresh(run)
        return run
    except Exception as e:
        log.exception("audit failed for run=%s project=%s", run.id, run.project_id)
        run.status = "failed"
        run.error = str(e)[:1000]
        run.completed_at = dt.datetime.now(dt.timezone.utc)
        await db.commit()
        raise
