"""On-page SEO checker — single-URL deep audit. Reuses the crawler's HTML
extractor + PageSpeed CWV in one shot."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers._helpers import get_project_or_404
from schemas.common import ok
from services import onpage

router = APIRouter(prefix="/api/projects/{project_id}/onpage", tags=["onpage"])
log = logging.getLogger(__name__)


@router.get("")
async def onpage_check(
    project_id: uuid.UUID,
    url: str = Query(min_length=4, max_length=2048),
    pagespeed: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    try:
        return ok(await onpage.analyze_url(url, run_pagespeed=pagespeed))
    except Exception as e:
        log.exception("on-page failed for %s", url)
        raise HTTPException(400, f"On-page analysis failed: {e}")
