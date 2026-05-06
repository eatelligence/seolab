"""content_outputs table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_content_outputs_project_id", "content_outputs", ["project_id"])
    op.create_index("ix_content_outputs_tool_type", "content_outputs", ["tool_type"])
    op.create_index("ix_content_outputs_created_at", "content_outputs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_content_outputs_created_at", table_name="content_outputs")
    op.drop_index("ix_content_outputs_tool_type", table_name="content_outputs")
    op.drop_index("ix_content_outputs_project_id", table_name="content_outputs")
    op.drop_table("content_outputs")
