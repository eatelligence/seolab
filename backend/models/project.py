import uuid
from typing import List, Optional

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPkMixin


project_tag_links = Table(
    "project_tag_links",
    Base.metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("project_tags.id", ondelete="CASCADE"), primary_key=True),
)


class Project(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    gsc_property: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    competitors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="US", server_default="US")

    tags: Mapped[List["ProjectTag"]] = relationship(
        "ProjectTag", secondary=project_tag_links, back_populates="projects", lazy="selectin"
    )
    keywords: Mapped[List["Keyword"]] = relationship(  # noqa: F821
        "Keyword", back_populates="project", cascade="all, delete-orphan"
    )
    audit_runs: Mapped[List["AuditRun"]] = relationship(  # noqa: F821
        "AuditRun", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectTag(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "project_tags"
    __table_args__ = (UniqueConstraint("name", name="uq_project_tags_name"),)

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#6b7280", server_default="#6b7280")

    projects: Mapped[List[Project]] = relationship(
        "Project", secondary=project_tag_links, back_populates="tags"
    )
