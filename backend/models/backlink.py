import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, UUIDPkMixin


class Backlink(UUIDPkMixin, Base):
    __tablename__ = "backlinks"
    __table_args__ = (
        UniqueConstraint("project_id", "source_url", "target_url", name="uq_backlinks_src_tgt"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    anchor_text: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    domain_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    page_traffic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_dofollow: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    toxic_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    lost_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class BacklinkSnapshot(UUIDPkMixin, Base):
    """Daily aggregate snapshot for charts (refdomains/backlinks count over time)."""

    __tablename__ = "backlink_snapshots"
    __table_args__ = (
        UniqueConstraint("project_id", "snapshot_date", name="uq_backlink_snapshots_project_date"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    total_backlinks: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    referring_domains: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    dofollow_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    nofollow_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    lost_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    domain_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
