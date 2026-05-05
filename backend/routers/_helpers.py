"""Shared router utilities."""

import csv
import io
import uuid
from typing import Iterable, List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.project import Project


async def get_project_or_404(db: AsyncSession, project_id: uuid.UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


def to_csv(rows: Iterable[dict], columns: List[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow({c: r.get(c) for c in columns})
    return buf.getvalue()
