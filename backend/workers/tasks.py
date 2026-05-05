"""Celery task entrypoints. Async work is driven via ``asyncio.run`` against a
worker-dedicated AsyncSession factory (engine separate from FastAPI's)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from workers.celery_app import celery

log = logging.getLogger(__name__)


def _make_session_factory():
    engine = create_async_engine(settings.async_db_url, pool_pre_ping=True, pool_size=5, max_overflow=5)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


_Session = None


def _session() -> async_sessionmaker:
    global _Session
    if _Session is None:
        _Session = _make_session_factory()
    return _Session


async def _all_project_ids() -> List[uuid.UUID]:
    from models.project import Project
    Session = _session()
    async with Session() as db:
        rows = (await db.execute(select(Project.id))).scalars().all()
        return list(rows)


# ---------------- Rank tracker ----------------

@celery.task(name="workers.tasks.run_rank_tracker_for_project")
def run_rank_tracker_for_project(project_id: str) -> dict:
    from services.rank_tracker import check_project

    async def _run():
        Session = _session()
        async with Session() as db:
            return await check_project(db, uuid.UUID(project_id))

    n = asyncio.run(_run())
    log.info("rank tracker for project=%s: checked=%s", project_id, n)
    return {"project_id": project_id, "checked": n}


@celery.task(name="workers.tasks.run_rank_tracker_for_all_projects")
def run_rank_tracker_for_all_projects() -> dict:
    project_ids = asyncio.run(_all_project_ids())
    for pid in project_ids:
        run_rank_tracker_for_project.delay(str(pid))
    log.info("rank tracker fanned out to %s projects", len(project_ids))
    return {"fanned_out": len(project_ids)}


# ---------------- Site audit ----------------

@celery.task(name="workers.tasks.run_site_audit_for_project")
def run_site_audit_for_project(project_id: str) -> dict:
    from services.audit import run_audit

    async def _run():
        Session = _session()
        async with Session() as db:
            run = await run_audit(db, uuid.UUID(project_id), run_pagespeed=True)
            return run.id

    run_id = asyncio.run(_run())
    log.info("audit completed for project=%s run=%s", project_id, run_id)
    return {"project_id": project_id, "run_id": str(run_id)}


@celery.task(name="workers.tasks.run_site_audit_for_all_projects")
def run_site_audit_for_all_projects() -> dict:
    project_ids = asyncio.run(_all_project_ids())
    for pid in project_ids:
        run_site_audit_for_project.delay(str(pid))
    return {"fanned_out": len(project_ids)}


# ---------------- Backlinks snapshot ----------------

@celery.task(name="workers.tasks.snapshot_backlinks_for_project")
def snapshot_backlinks_for_project(project_id: str) -> dict:
    from models.project import Project
    from services.backlinks import take_snapshot

    async def _run():
        Session = _session()
        async with Session() as db:
            project = await db.get(Project, uuid.UUID(project_id))
            if not project:
                return None
            snap = await take_snapshot(db, project)
            return snap.snapshot_date

    res = asyncio.run(_run())
    log.info("backlink snapshot project=%s -> %s", project_id, res)
    return {"project_id": project_id, "snapshot_date": str(res) if res else None}


@celery.task(name="workers.tasks.snapshot_backlinks_for_all_projects")
def snapshot_backlinks_for_all_projects() -> dict:
    project_ids = asyncio.run(_all_project_ids())
    for pid in project_ids:
        snapshot_backlinks_for_project.delay(str(pid))
    return {"fanned_out": len(project_ids)}


# ---------------- AI visibility ----------------

@celery.task(name="workers.tasks.run_ai_visibility_for_project")
def run_ai_visibility_for_project(project_id: str) -> dict:
    from services.ai_visibility import run_for_project

    async def _run():
        Session = _session()
        async with Session() as db:
            return await run_for_project(db, uuid.UUID(project_id))

    n = asyncio.run(_run())
    log.info("ai visibility project=%s checked=%s", project_id, n)
    return {"project_id": project_id, "checked": n}


@celery.task(name="workers.tasks.run_ai_visibility_for_all_projects")
def run_ai_visibility_for_all_projects() -> dict:
    project_ids = asyncio.run(_all_project_ids())
    for pid in project_ids:
        run_ai_visibility_for_project.delay(str(pid))
    return {"fanned_out": len(project_ids)}
