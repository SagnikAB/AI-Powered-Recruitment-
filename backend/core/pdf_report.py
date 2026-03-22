"""
Generates a styled PDF analysis report using reportlab.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime


# ── Color palette ─────────────────────────────────────────────────────────────
PURPLE      = colors.HexColor("#6366f1")
PURPLE_DARK = colors.HexColor("#4f46e5")
GREEN       = colors.HexColor("#22c55e")
AMBER       = colors.HexColor("#f59e0b")
RED         = colors.HexColor("#ef4444")
DARK        = colors.HexColor("#0f172a")
LIGHT_BG    = colors.HexColor("#f1f5f9")
MUTED       = colors.HexColor("#64748b")
WHITE       = colors.white


def _score_color(score: int):
    if score >= 70: return GREEN
    if score >= 50: return AMBER
    return RED


def generate_pdf_report(data: dict) -> bytes:
    """
    data keys:
        name, score, rank, matched (str), missing (str),
        recommendations (str), job_description (str), date (str)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
        title="AI Resume Analysis Report"
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "Title", parent=styles["Normal"],
        fontSize=22, fontName="Helvetica-Bold",
        textColor=PURPLE, alignment=TA_CENTER, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=10, textColor=MUTED, alignment=TA_CENTER, spaceAfter=16
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Normal"],
        fontSize=13, fontName="Helvetica-Bold",
        textColor=DARK, spaceBefore=16, spaceAfter=8
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=DARK, leading=16
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=styles["Normal"],
        fontSize=10, textColor=DARK, leading=16,
        leftIndent=14, bulletIndent=4
    )

    score      = data.get("score", 0)
    rank       = data.get("rank", "--")
    name       = data.get("name", "Resume")
    matched    = [s.strip() for s in (data.get("matched") or "").split(",") if s.strip()]
    missing    = [s.strip() for s in (data.get("missing") or "").split(",") if s.strip()]
    recs       = [s.strip() for s in (data.get("recommendations") or "").split(",") if s.strip()]
    job_desc   = data.get("job_description", "")
    date_str   = data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
    s_color    = _score_color(score)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("🤖 AI Resume Analyzer", title_style))
    story.append(Paragraph("Powered by AI Recruitment System", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE, spaceAfter=12))

    # ── Meta info table ───────────────────────────────────────────────────────
    meta = [
        ["File", name],
        ["Analyzed", date_str],
        ["Rank", rank],
    ]
    meta_table = Table(meta, colWidths=[3.5*cm, 13*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 10),
        ("TEXTCOLOR",   (0,0), (0,-1), MUTED),
        ("TEXTCOLOR",   (1,0), (1,-1), DARK),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # ── Score block ───────────────────────────────────────────────────────────
    score_data = [[
        Paragraph(f'<font size="36" color="{s_color.hexval()}">'
                  f'<b>{score}</b></font><br/>'
                  f'<font size="11" color="{MUTED.hexval()}">ATS Score / 100</font>',
                  ParagraphStyle("sc", alignment=TA_CENTER))
    ]]
    score_table = Table(score_data, colWidths=[16.5*cm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), LIGHT_BG),
        ("ROUNDEDCORNERS", (0,0), (-1,-1), [8,8,8,8]),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",  (0,0), (-1,-1), 16),
        ("BOTTOMPADDING",(0,0),(-1,-1), 16),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 16))

    # ── Job Description ───────────────────────────────────────────────────────
    if job_desc and job_desc.strip():
        story.append(Paragraph("🎯 Job Description Used", section_style))
        story.append(Paragraph(job_desc[:500], body_style))
        story.append(Spacer(1, 8))

    # ── Matched Keywords ──────────────────────────────────────────────────────
    if matched:
        story.append(Paragraph("✅ Matched Keywords", section_style))
        kw_data = [[
            Paragraph(f'<font color="{GREEN.hexval()}">● {kw}</font>', body_style)
            for kw in matched[i:i+3]
        ] for i in range(0, len(matched), 3)]
        kw_table = Table(kw_data, colWidths=[5.5*cm]*3)
        kw_table.setStyle(TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ]))
        story.append(kw_table)
        story.append(Spacer(1, 8))

    # ── Missing Keywords ──────────────────────────────────────────────────────
    if missing:
        story.append(Paragraph("❌ Missing Keywords", section_style))
        mk_data = [[
            Paragraph(f'<font color="{RED.hexval()}">● {kw}</font>', body_style)
            for kw in missing[i:i+3]
        ] for i in range(0, len(missing), 3)]
        mk_table = Table(mk_data, colWidths=[5.5*cm]*3)
        mk_table.setStyle(TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ]))
        story.append(mk_table)
        story.append(Spacer(1, 8))

    # ── Recommendations ───────────────────────────────────────────────────────
    if recs:
        story.append(Paragraph("💡 Recommendations", section_style))
        for rec in recs:
            story.append(Paragraph(f"• {rec}", bullet_style))
        story.append(Spacer(1, 8))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED, spaceAfter=8))
    story.append(Paragraph(
        "Generated by AI Resume Analyzer · © 2026 Sagnik Dam",
        ParagraphStyle("footer", parent=styles["Normal"],
                       fontSize=9, textColor=MUTED, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buffer.getvalue()