import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPkMixin


class AuditRun(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "audit_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    health_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pages_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    project: Mapped["Project"] = relationship("Project", back_populates="audit_runs")  # noqa: F821
    issues: Mapped[List["AuditIssue"]] = relationship(
        "AuditIssue", back_populates="run", cascade="all, delete-orphan"
    )
    pages: Mapped[List["AuditPage"]] = relationship(
        "AuditPage", back_populates="run", cascade="all, delete-orphan"
    )


class AuditIssue(UUIDPkMixin, Base):
    __tablename__ = "audit_issues"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # high|medium|low
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped[AuditRun] = relationship("AuditRun", back_populates="issues")


class AuditPage(UUIDPkMixin, Base):
    __tablename__ = "audit_pages"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    h1_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    load_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    canonical: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    is_https: Mapped[bool] = mapped_column(server_default="true", default=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped[AuditRun] = relationship("AuditRun", back_populates="pages")
