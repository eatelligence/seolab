import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.project import Project, ProjectTag
from schemas.common import ok
from schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectTagCreate,
    ProjectTagOut,
    ProjectTagUpdate,
    ProjectUpdate,
)

router = APIRouter(prefix="/api", tags=["projects"])


# ---------- Tags ----------

@router.get("/project-tags")
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProjectTag).order_by(ProjectTag.name))
    tags = result.scalars().all()
    return ok([ProjectTagOut.model_validate(t).model_dump(mode="json") for t in tags])


@router.post("/project-tags", status_code=status.HTTP_201_CREATED)
async def create_tag(payload: ProjectTagCreate, db: AsyncSession = Depends(get_db)):
    tag = ProjectTag(name=payload.name, color=payload.color)
    db.add(tag)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Tag name already exists")
    await db.refresh(tag)
    return ok(ProjectTagOut.model_validate(tag).model_dump(mode="json"))


@router.patch("/project-tags/{tag_id}")
async def update_tag(tag_id: uuid.UUID, payload: ProjectTagUpdate, db: AsyncSession = Depends(get_db)):
    tag = await db.get(ProjectTag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Tag name already exists")
    await db.refresh(tag)
    return ok(ProjectTagOut.model_validate(tag).model_dump(mode="json"))


@router.delete("/project-tags/{tag_id}", status_code=status.HTTP_200_OK)
async def delete_tag(tag_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    tag = await db.get(ProjectTag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")
    await db.delete(tag)
    await db.commit()
    return ok({"deleted": str(tag_id)})


# ---------- Projects ----------

async def _load_tags(db: AsyncSession, tag_ids: List[uuid.UUID]) -> List[ProjectTag]:
    if not tag_ids:
        return []
    result = await db.execute(select(ProjectTag).where(ProjectTag.id.in_(tag_ids)))
    tags = result.scalars().all()
    if len(tags) != len(set(tag_ids)):
        raise HTTPException(400, "One or more tag_ids are invalid")
    return list(tags)


@router.get("/projects")
async def list_projects(
    tag_id: Optional[uuid.UUID] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Project).options(selectinload(Project.tags)).order_by(Project.created_at.desc())
    if tag_id:
        stmt = stmt.join(Project.tags).where(ProjectTag.id == tag_id)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where((Project.name.ilike(like)) | (Project.domain.ilike(like)))
    result = await db.execute(stmt)
    projects = result.scalars().unique().all()
    return ok([ProjectOut.model_validate(p).model_dump(mode="json") for p in projects])


@router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(
        name=payload.name,
        domain=payload.domain,
        gsc_property=payload.gsc_property,
        competitors=payload.competitors,
        country=payload.country,
    )
    project.tags = await _load_tags(db, payload.tag_ids)
    db.add(project)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "A project with this domain already exists")
    await db.refresh(project, attribute_names=["tags"])
    return ok(ProjectOut.model_validate(project).model_dump(mode="json"))


@router.get("/projects/{project_id}")
async def get_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Project).options(selectinload(Project.tags)).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return ok(ProjectOut.model_validate(project).model_dump(mode="json"))


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: uuid.UUID, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).options(selectinload(Project.tags)).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    data = payload.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)
    for field, value in data.items():
        setattr(project, field, value)
    if tag_ids is not None:
        project.tags = await _load_tags(db, tag_ids)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Domain conflict")
    await db.refresh(project, attribute_names=["tags"])
    return ok(ProjectOut.model_validate(project).model_dump(mode="json"))


@router.delete("/projects/{project_id}")
async def delete_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    await db.delete(project)
    await db.commit()
    return ok({"deleted": str(project_id)})
