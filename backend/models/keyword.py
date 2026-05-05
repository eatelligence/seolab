import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPkMixin


class Keyword(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint("project_id", "keyword", "country", name="uq_keywords_project_kw_country"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="US", server_default="US")
    search_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    keyword_difficulty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intent: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tracked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    extra: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    project: Mapped["Project"] = relationship("Project", back_populates="keywords")  # noqa: F821
    rankings: Mapped[List["Ranking"]] = relationship(  # noqa: F821
        "Ranking", back_populates="keyword", cascade="all, delete-orphan"
    )


class KeywordList(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "keyword_lists"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_keyword_lists_project_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    items: Mapped[List["KeywordListItem"]] = relationship(
        "KeywordListItem", back_populates="keyword_list", cascade="all, delete-orphan"
    )


class KeywordListItem(Base):
    __tablename__ = "keyword_list_items"

    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keyword_lists.id", ondelete="CASCADE"), primary_key=True
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True
    )

    keyword_list: Mapped[KeywordList] = relationship("KeywordList", back_populates="items")
    keyword: Mapped[Keyword] = relationship("Keyword")
