"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False, unique=True),
        sa.Column("gsc_property", sa.String(255), nullable=True),
        sa.Column("competitors", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("country", sa.String(2), nullable=False, server_default="US"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_projects_domain", "projects", ["domain"])

    # project_tags
    op.create_table(
        "project_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("color", sa.String(16), nullable=False, server_default="#6b7280"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", name="uq_project_tags_name"),
    )

    # project_tag_links
    op.create_table(
        "project_tag_links",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_tags.id", ondelete="CASCADE"), primary_key=True),
    )

    # keywords
    op.create_table(
        "keywords",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword", sa.String(512), nullable=False),
        sa.Column("country", sa.String(2), nullable=False, server_default="US"),
        sa.Column("search_volume", sa.Integer, nullable=True),
        sa.Column("keyword_difficulty", sa.Float, nullable=True),
        sa.Column("cpc", sa.Float, nullable=True),
        sa.Column("intent", sa.String(32), nullable=True),
        sa.Column("tracked", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "keyword", "country", name="uq_keywords_project_kw_country"),
    )
    op.create_index("ix_keywords_project_id", "keywords", ["project_id"])
    op.create_index("ix_keywords_keyword", "keywords", ["keyword"])

    # keyword_lists
    op.create_table(
        "keyword_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "name", name="uq_keyword_lists_project_name"),
    )
    op.create_index("ix_keyword_lists_project_id", "keyword_lists", ["project_id"])

    op.create_table(
        "keyword_list_items",
        sa.Column("list_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("keyword_lists.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("keyword_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True),
    )

    # rankings
    op.create_table(
        "rankings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("keyword_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer, nullable=True),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("serp_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("competitor_positions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rankings_keyword_id", "rankings", ["keyword_id"])
    op.create_index("ix_rankings_checked_at", "rankings", ["checked_at"])

    # audit_runs
    op.create_table(
        "audit_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("health_score", sa.Integer, nullable=True),
        sa.Column("pages_crawled", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_runs_project_id", "audit_runs", ["project_id"])

    op.create_table(
        "audit_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_issues_run_id", "audit_issues", ["run_id"])
    op.create_index("ix_audit_issues_issue_type", "audit_issues", ["issue_type"])
    op.create_index("ix_audit_issues_severity", "audit_issues", ["severity"])

    op.create_table(
        "audit_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("title", sa.String(1024), nullable=True),
        sa.Column("meta_description", sa.Text, nullable=True),
        sa.Column("h1_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("word_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("depth", sa.Integer, nullable=False, server_default="0"),
        sa.Column("load_time_ms", sa.Integer, nullable=True),
        sa.Column("canonical", sa.String(2048), nullable=True),
        sa.Column("is_https", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("crawled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_pages_run_id", "audit_pages", ["run_id"])
    op.create_index("ix_audit_pages_url", "audit_pages", ["url"])

    # backlinks
    op.create_table(
        "backlinks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("source_domain", sa.String(255), nullable=False),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("anchor_text", sa.String(1024), nullable=True),
        sa.Column("domain_rating", sa.Float, nullable=True),
        sa.Column("page_traffic", sa.Integer, nullable=True),
        sa.Column("is_dofollow", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("toxic_score", sa.Float, nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("lost_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", "source_url", "target_url", name="uq_backlinks_src_tgt"),
    )
    op.create_index("ix_backlinks_project_id", "backlinks", ["project_id"])
    op.create_index("ix_backlinks_source_domain", "backlinks", ["source_domain"])
    op.create_index("ix_backlinks_last_seen", "backlinks", ["last_seen"])

    op.create_table(
        "backlink_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_backlinks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("referring_domains", sa.Integer, nullable=False, server_default="0"),
        sa.Column("dofollow_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("nofollow_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("new_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("lost_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("domain_rating", sa.Float, nullable=True),
        sa.UniqueConstraint("project_id", "snapshot_date", name="uq_backlink_snapshots_project_date"),
    )
    op.create_index("ix_backlink_snapshots_project_id", "backlink_snapshots", ["project_id"])
    op.create_index("ix_backlink_snapshots_date", "backlink_snapshots", ["snapshot_date"])

    # ai visibility
    op.create_table(
        "ai_visibility_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.String(1024), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "query", name="uq_ai_vis_queries_project_query"),
    )
    op.create_index("ix_ai_vis_queries_project_id", "ai_visibility_queries", ["project_id"])

    op.create_table(
        "ai_visibility_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("query_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_visibility_queries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default="claude"),
        sa.Column("response_text", sa.Text, nullable=False),
        sa.Column("brand_mentioned", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("mention_position", sa.Integer, nullable=True),
        sa.Column("sentiment", sa.String(16), nullable=True),
        sa.Column("sentiment_score", sa.Float, nullable=True),
        sa.Column("competitors_mentioned", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_vis_checks_query_id", "ai_visibility_checks", ["query_id"])
    op.create_index("ix_ai_vis_checks_checked_at", "ai_visibility_checks", ["checked_at"])

    # gsc_tokens
    op.create_table(
        "gsc_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token", sa.Text, nullable=False),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", name="uq_gsc_tokens_project"),
    )


def downgrade() -> None:
    op.drop_table("gsc_tokens")
    op.drop_index("ix_ai_vis_checks_checked_at", table_name="ai_visibility_checks")
    op.drop_index("ix_ai_vis_checks_query_id", table_name="ai_visibility_checks")
    op.drop_table("ai_visibility_checks")
    op.drop_index("ix_ai_vis_queries_project_id", table_name="ai_visibility_queries")
    op.drop_table("ai_visibility_queries")
    op.drop_index("ix_backlink_snapshots_date", table_name="backlink_snapshots")
    op.drop_index("ix_backlink_snapshots_project_id", table_name="backlink_snapshots")
    op.drop_table("backlink_snapshots")
    op.drop_index("ix_backlinks_last_seen", table_name="backlinks")
    op.drop_index("ix_backlinks_source_domain", table_name="backlinks")
    op.drop_index("ix_backlinks_project_id", table_name="backlinks")
    op.drop_table("backlinks")
    op.drop_index("ix_audit_pages_url", table_name="audit_pages")
    op.drop_index("ix_audit_pages_run_id", table_name="audit_pages")
    op.drop_table("audit_pages")
    op.drop_index("ix_audit_issues_severity", table_name="audit_issues")
    op.drop_index("ix_audit_issues_issue_type", table_name="audit_issues")
    op.drop_index("ix_audit_issues_run_id", table_name="audit_issues")
    op.drop_table("audit_issues")
    op.drop_index("ix_audit_runs_project_id", table_name="audit_runs")
    op.drop_table("audit_runs")
    op.drop_index("ix_rankings_checked_at", table_name="rankings")
    op.drop_index("ix_rankings_keyword_id", table_name="rankings")
    op.drop_table("rankings")
    op.drop_table("keyword_list_items")
    op.drop_index("ix_keyword_lists_project_id", table_name="keyword_lists")
    op.drop_table("keyword_lists")
    op.drop_index("ix_keywords_keyword", table_name="keywords")
    op.drop_index("ix_keywords_project_id", table_name="keywords")
    op.drop_table("keywords")
    op.drop_table("project_tag_links")
    op.drop_table("project_tags")
    op.drop_index("ix_projects_domain", table_name="projects")
    op.drop_table("projects")
