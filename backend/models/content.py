import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, UUIDPkMixin


class ContentOutput(UUIDPkMixin, Base):
    """Persistent record of every Content/AI generation (brief, optimize, meta, calendar).

    The Claude calls cost money so we never want the user to lose them on a tab
    switch or browser refresh. Each generation is auto-saved here with the
    original input + the JSON output.
    """

    __tablename__ = "content_outputs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # brief|optimize|meta|calendar
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
