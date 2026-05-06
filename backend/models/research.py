import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, UUIDPkMixin


class KeywordResearchRun(UUIDPkMixin, Base):
    """Auto-saved keyword research output. Reload at any time without losing
    expensive Suggest+DataForSEO calls."""

    __tablename__ = "keyword_research_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seed: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    suggest_levels: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
