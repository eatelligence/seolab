"""PDF report generator for an AuditRun (reportlab)."""

from __future__ import annotations

import io
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models.audit import AuditIssue, AuditRun
from models.project import Project

SEVERITY_COLORS = {
    "high": colors.HexColor("#dc2626"),
    "medium": colors.HexColor("#f59e0b"),
    "low": colors.HexColor("#3b82f6"),
}


def render(project: Project, run: AuditRun, issues: Iterable[AuditIssue]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        title=f"SEOLab Audit — {project.domain}",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#1a1f2e"), fontSize=22)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#ff642d"))
    body = styles["BodyText"]

    story = []
    story.append(Paragraph("SEOLab — Site Audit Report", h1))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f"<b>Project:</b> {project.name}", body))
    story.append(Paragraph(f"<b>Domain:</b> {project.domain}", body))
    story.append(Paragraph(
        f"<b>Run completed:</b> {run.completed_at.strftime('%Y-%m-%d %H:%M UTC') if run.completed_at else '—'}",
        body,
    ))
    story.append(Paragraph(f"<b>Pages crawled:</b> {run.pages_crawled}", body))
    story.append(Paragraph(
        f"<b>Health score:</b> <font size=18 color='#ff642d'><b>{run.health_score or 0}/100</b></font>",
        body,
    ))
    story.append(Spacer(1, 0.5 * cm))

    summary = run.summary or {}
    by_sev = summary.get("by_severity") or {}
    sev_table = [
        ["Severity", "Count"],
        ["High", by_sev.get("high", 0)],
        ["Medium", by_sev.get("medium", 0)],
        ["Low", by_sev.get("low", 0)],
        ["Total", summary.get("total", 0)],
    ]
    t = Table(sev_table, hAlign="LEFT", colWidths=[6 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1f2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))

    by_type = summary.get("by_type") or {}
    if by_type:
        story.append(Paragraph("Issues by type", h2))
        type_rows = [["Issue", "Count"]] + [
            [k.replace("_", " ").title(), v]
            for k, v in sorted(by_type.items(), key=lambda x: -x[1])
        ]
        tt = Table(type_rows, hAlign="LEFT", colWidths=[10 * cm, 3 * cm])
        tt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1f2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ]))
        story.append(tt)

    story.append(PageBreak())
    story.append(Paragraph("Issue details", h2))
    issues = sorted(issues, key=lambda i: ({"high": 0, "medium": 1, "low": 2}.get(i.severity, 3), i.issue_type))
    rows = [["Severity", "Issue", "URL"]]
    for i in issues[:500]:  # cap pages in PDF
        rows.append([i.severity.upper(), i.issue_type.replace("_", " "), i.url[:90]])
    detail = Table(rows, hAlign="LEFT", colWidths=[2 * cm, 5 * cm, 11 * cm], repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1f2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
    ])
    for idx, row in enumerate(rows[1:], start=1):
        sev = row[0].lower()
        if sev in SEVERITY_COLORS:
            style.add("TEXTCOLOR", (0, idx), (0, idx), SEVERITY_COLORS[sev])
            style.add("FONTNAME", (0, idx), (0, idx), "Helvetica-Bold")
    detail.setStyle(style)
    story.append(detail)

    doc.build(story)
    return buf.getvalue()
