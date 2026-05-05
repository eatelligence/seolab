import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPkMixin


class AIVisibilityQuery(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "ai_visibility_queries"
    __table_args__ = (
        UniqueConstraint("project_id", "query", name="uq_ai_vis_queries_project_query"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(String(1024), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    checks: Mapped[List["AIVisibilityCheck"]] = relationship(
        "AIVisibilityCheck", back_populates="query", cascade="all, delete-orphan"
    )


class AIVisibilityCheck(UUIDPkMixin, Base):
    __tablename__ = "ai_visibility_checks"

    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_visibility_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="claude", server_default="claude")
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    brand_mentioned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    mention_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # positive|neutral|negative
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    competitors_mentioned: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    query: Mapped[AIVisibilityQuery] = relationship("AIVisibilityQuery", back_populates="checks")
