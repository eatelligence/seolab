"""keyword_research_runs table

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "keyword_research_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seed", sa.String(255), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("suggest_levels", sa.Integer, nullable=False, server_default="2"),
        sa.Column("total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_kw_research_runs_project_id", "keyword_research_runs", ["project_id"])
    op.create_index("ix_kw_research_runs_created_at", "keyword_research_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_kw_research_runs_created_at", table_name="keyword_research_runs")
    op.drop_index("ix_kw_research_runs_project_id", table_name="keyword_research_runs")
    op.drop_table("keyword_research_runs")
