"""
PDF Generation Service for Law Mithra Universal Complaint Analysis Report.
Generates a professional A4 legal report (1 to 2 pages maximum) using ReportLab.
Supports English and Indian-language Unicode text (Kannada, Hindi, Tamil, Telugu, etc.).
"""

import io
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


# ── Colour palette ─────────────────────────────────────────────────────────────
DARK_NAVY  = colors.HexColor('#1A2E4C')
STEEL_BLUE = colors.HexColor('#2C4C6E')
LIGHT_BLUE = colors.HexColor('#EBF1F8')
MID_BLUE   = colors.HexColor('#C8D8E9')
BORDER     = colors.HexColor('#B8C8DB')
WHITE      = colors.white
BLACK      = colors.HexColor('#111111')
GREY       = colors.HexColor('#4A5568')
LIGHT_GREY = colors.HexColor('#F8FAFD')
AMBER      = colors.HexColor('#991B1B')
ROW_EVEN   = colors.HexColor('#F8FAFD')
ROW_ODD    = colors.white


# ── Unicode Font Configuration ─────────────────────────────────────────────────
_FONT_INIT = False
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_ITALIC = 'Helvetica-Oblique'


def _init_fonts():
    """
    Register and set up Unicode TrueType fonts supporting Indian languages.
    Prioritizes Nirmala UI on Windows; falls back to standard Linux paths,
    then defaults to Helvetica.
    """
    global _FONT_INIT, FONT_REGULAR, FONT_BOLD, FONT_ITALIC
    if _FONT_INIT:
        return

    candidates = [
        # Windows Nirmala UI (full Indian scripts + English support)
        ("Nirmala", "C:/Windows/Fonts/Nirmala.ttf", "Nirmala-Bold", "C:/Windows/Fonts/NirmalaB.ttf"),
        # Standard Linux paths (Noto Sans, FreeSerif, DejaVu)
        ("NotoSans", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "NotoSans-Bold", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
        ("FreeSerif", "/usr/share/fonts/truetype/freefont/FreeSerif.ttf", "FreeSerif-Bold", "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"),
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]

    for r_name, r_path, b_name, b_path in candidates:
        if os.path.exists(r_path) and os.path.exists(b_path):
            try:
                pdfmetrics.registerFont(TTFont(r_name, r_path))
                pdfmetrics.registerFont(TTFont(b_name, b_path))
                FONT_REGULAR = r_name
                FONT_BOLD = b_name
                FONT_ITALIC = r_name
                _FONT_INIT = True
                return
            except Exception:
                continue
        elif os.path.exists(r_path):
            try:
                pdfmetrics.registerFont(TTFont(r_name, r_path))
                FONT_REGULAR = r_name
                FONT_BOLD = r_name
                FONT_ITALIC = r_name
                _FONT_INIT = True
                return
            except Exception:
                continue

    _FONT_INIT = True


def _style(name, **kwargs):
    """Create a named ParagraphStyle with given kwargs."""
    return ParagraphStyle(name=name, **kwargs)


def _truncate(text: str, max_chars: int = 500) -> str:
    """Safely truncate text to prevent overflowing page boundaries."""
    if not text or text in ('Not provided', 'Requires verification', 'Not Applicable'):
        return text or 'Not provided'
    text = str(text).strip()
    if len(text) > max_chars:
        return text[:max_chars - 3] + '...'
    return text


def _list_items(items: List[str], bullet: str = '•', max_items: int = 6) -> str:
    """Convert list of strings to clean HTML bullet lines for table cells."""
    if not items:
        return 'Not provided'
    shown = items[:max_items]
    result = '<br/>'.join(f'{bullet} {_truncate(i, 180)}' for i in shown if str(i).strip())
    if len(items) > max_items:
        result += f'<br/>... and {len(items) - max_items} more items'
    return result or 'Not provided'


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that dynamically calculates total page count and renders
    running headers (Page 2+) and running footers with 'Page X of Y'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        margin_l = 28.35  # 10 mm
        margin_r = 595.27 - 28.35
        page_h = 841.89

        # Running header on page 2 and later
        if self._pageNumber > 1:
            self.setFont(FONT_BOLD, 7)
            self.setFillColor(DARK_NAVY)
            self.drawString(margin_l, page_h - 22, "LAW MITHRA — UNIVERSAL COMPLAINT ANALYSIS REPORT")
            self.setFont(FONT_REGULAR, 7)
            self.setFillColor(GREY)
            report_id = getattr(self, '_report_id', '')
            if report_id:
                self.drawRightString(margin_r, page_h - 22, f"Ref: {report_id}")
            self.setStrokeColor(BORDER)
            self.setLineWidth(0.4)
            self.line(margin_l, page_h - 25, margin_r, page_h - 25)

        # Running footer on every page
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.4)
        self.line(margin_l, 28, margin_r, 28)

        self.setFont(FONT_REGULAR, 6.5)
        self.setFillColor(GREY)
        self.drawString(margin_l, 18, "CONFIDENTIAL — FOR LEGAL INFORMATION & ADVOCATE REVIEW ONLY")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(margin_r, 18, page_str)
        self.restoreState()


def make_numbered_canvas(report_id: str):
    """Factory to inject report_id into the NumberedCanvas instance."""
    class CustomNumberedCanvas(NumberedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._report_id = report_id
    return CustomNumberedCanvas


def generate_pdf(report_data: Dict[str, Any]) -> bytes:
    """
    Generate a professional A4 PDF for the Universal Complaint Analysis Report.
    Adheres strictly to the 1-2 page budget while preserving detailed legal analysis.
    Returns raw PDF bytes.
    """
    _init_fonts()

    buf = io.BytesIO()
    PAGE_W, PAGE_H = A4   # 595.27 x 841.89 points
    MARGIN = 10 * mm

    report_id = str(report_data.get('report_id', 'REPORT')).strip()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=11 * mm,
        bottomMargin=13 * mm,
        title=f"Law Mithra – {report_id}",
        author='Law Mithra AI Legal Assistant',
        subject='Universal Complaint Analysis Report',
    )

    CONTENT_W = PAGE_W - 2 * MARGIN

    # ── Styles ────────────────────────────────────────────────────────────────
    brand_style   = _style('Brand',    fontName=FONT_BOLD,    fontSize=13.0, textColor=DARK_NAVY,  alignment=TA_CENTER, spaceAfter=1)
    tagline_style = _style('Tagline',  fontName=FONT_REGULAR, fontSize=7.0,  textColor=STEEL_BLUE, alignment=TA_CENTER, spaceAfter=4, letterSpacing=0.4)

    sec_style   = _style('Sec',   fontName=FONT_BOLD,    fontSize=7.5, textColor=DARK_NAVY,  spaceAfter=1.5, spaceBefore=3)
    hdr_style   = _style('Hdr',   fontName=FONT_BOLD,    fontSize=6.8, textColor=DARK_NAVY,  spaceAfter=0, leading=8.5)
    cell_style  = _style('Cell',  fontName=FONT_REGULAR, fontSize=6.8, textColor=BLACK,      spaceAfter=0, leading=9.0)
    italic_cell = _style('Ital',  fontName=FONT_ITALIC,  fontSize=6.2, textColor=GREY,       spaceAfter=0, leading=8.0)
    body_style  = _style('Body',  fontName=FONT_REGULAR, fontSize=6.8, textColor=BLACK,      leading=9.2,  spaceAfter=0, alignment=TA_JUSTIFY)
    disc_style  = _style('Disc',  fontName=FONT_REGULAR, fontSize=6.0, textColor=AMBER,      leading=8.0,  spaceAfter=0, alignment=TA_JUSTIFY)

    story = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    story.append(Paragraph('LAW MITHRA', brand_style))
    story.append(Paragraph('YOUR SMART LEGAL ASSISTANT &nbsp;|&nbsp; UNIVERSAL COMPLAINT ANALYSIS REPORT', tagline_style))

    def section_label(number: str, title: str):
        """Clean section heading."""
        return Paragraph(f'<b>{number}. {title}</b>', sec_style)

    def mini_table(headers: List[str], rows: List[List[str]], col_w: List[float]):
        """Build a compact, bordered table with header row and alternating backgrounds."""
        data = [[Paragraph(h, hdr_style) for h in headers]]
        for i, row in enumerate(rows):
            st = italic_cell if any(v in ('Not provided', 'Requires verification', 'Not Applicable') for v in row) else cell_style
            data.append([Paragraph(str(v), st) for v in row])

        ts = TableStyle([
            ('BACKGROUND',    (0,0), (-1,0),  LIGHT_BLUE),
            ('TEXTCOLOR',     (0,0), (-1,0),  DARK_NAVY),
            ('FONTNAME',      (0,0), (-1,0),  FONT_BOLD),
            ('FONTSIZE',      (0,0), (-1,-1), 6.8),
            *[('BACKGROUND', (0,i), (-1,i), ROW_EVEN if i % 2 == 0 else ROW_ODD)
              for i in range(1, len(data))],
            ('GRID',          (0,0), (-1,-1), 0.4, BORDER),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ])
        return Table(data, colWidths=col_w, style=ts, repeatRows=1)

    # ── TOP IDENTITY ROW ──────────────────────────────────────────────────────
    id_data = [
        [Paragraph('REPORT ID', hdr_style),
         Paragraph('CASE / COMPLAINT NO.', hdr_style),
         Paragraph('GENERATED DATE', hdr_style),
         Paragraph('STATUS', hdr_style)],
        [Paragraph(report_id, cell_style),
         Paragraph(_truncate(report_data.get('case_complaint_no', 'Not provided'), 80), cell_style),
         Paragraph(str(report_data.get('generated_date', '')), cell_style),
         Paragraph(_truncate(report_data.get('status', 'Not provided'), 80), cell_style)],
    ]
    id_table = Table(
        id_data,
        colWidths=[CONTENT_W * 0.18, CONTENT_W * 0.30, CONTENT_W * 0.25, CONTENT_W * 0.27],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), LIGHT_BLUE),
            ('GRID',          (0,0), (-1,-1), 0.4, BORDER),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ])
    )
    story.append(id_table)
    story.append(Spacer(1, 2))

    # ── SECTION 1: CASE AT A GLANCE ──────────────────────────────────────────
    story.append(section_label('1', 'CASE AT A GLANCE'))
    glance_data = [
        [Paragraph('COMPLAINT TYPE / SUBJECT', hdr_style),
         Paragraph('PARTIES INVOLVED', hdr_style),
         Paragraph('DATE & PLACE OF INCIDENT', hdr_style)],
        [Paragraph(_truncate(report_data.get('complaint_type', 'Not provided'), 120), cell_style),
         Paragraph(_truncate(report_data.get('parties_involved', 'Not provided'), 200), cell_style),
         Paragraph(_truncate(report_data.get('incident_date_place', 'Not provided'), 120), cell_style)],
    ]
    glance_table = Table(
        glance_data,
        colWidths=[CONTENT_W * 0.28, CONTENT_W * 0.42, CONTENT_W * 0.30],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), LIGHT_BLUE),
            ('GRID',          (0,0), (-1,-1), 0.4, BORDER),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ])
    )
    story.append(glance_table)
    story.append(Spacer(1, 2))

    # ── SECTION 2: COMPLAINT SUMMARY ─────────────────────────────────────────
    story.append(section_label('2', 'COMPLAINT SUMMARY'))
    summary_text = _truncate(report_data.get('complaint_summary', 'Requires verification'), 650)
    summary_data = [
        [Paragraph('NEUTRAL CASE SUMMARY (SEPARATING CLAIMS FROM INDEPENDENTLY VERIFIED FACTS)', hdr_style)],
        [Paragraph(summary_text, body_style)],
    ]
    summary_table = Table(
        summary_data,
        colWidths=[CONTENT_W],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (0,0), LIGHT_BLUE),
            ('GRID',          (0,0), (-1,-1), 0.4, BORDER),
            ('LEFTPADDING',   (0,0), (-1,-1), 5),
            ('RIGHTPADDING',  (0,0), (-1,-1), 5),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ])
    )
    story.append(summary_table)
    story.append(Spacer(1, 2))

    # ── SECTION 3: POSSIBLE LEGAL PROVISIONS ─────────────────────────────────
    story.append(section_label('3', 'POSSIBLE LEGAL PROVISIONS'))
    prov_headers = ['ACT / SECTION', 'STATUTORY RELEVANCE & INGREDIENTS', 'VERIFICATION / CAVEAT']
    prov_col_w   = [CONTENT_W * 0.22, CONTENT_W * 0.42, CONTENT_W * 0.36]
    provisions   = report_data.get('legal_provisions', [])
    prov_rows    = []
    for p in provisions[:8]:   # up to 8 provisions within 1-2 page budget
        prov_rows.append([
            _truncate(p.get('act_section', 'Requires verification'), 90),
            _truncate(p.get('relevance',   'Requires verification'), 220),
            _truncate(p.get('caveat',      'Check ingredients, date, amendments and jurisdiction.'), 200),
        ])
    if not prov_rows:
        prov_rows = [['Requires verification', 'Requires verification',
                      'Check statutory ingredients, date applicability, amendments and jurisdiction. Do not treat a possible section as a final finding.']]
    story.append(mini_table(prov_headers, prov_rows, prov_col_w))
    story.append(Spacer(1, 2))

    # ── SECTION 4: KEY EVIDENCE & DOCUMENTS ──────────────────────────────────
    story.append(section_label('4', 'KEY EVIDENCE & DOCUMENTS'))
    avail_text   = _list_items(report_data.get('evidence_available', ['Not provided']), '✓', max_items=6)
    missing_text = _list_items(report_data.get('evidence_missing',   ['Requires verification']), '✗', max_items=6)
    evid_data = [
        [Paragraph('AVAILABLE MATERIAL (DOCUMENTARY & DIGITAL EVIDENCE)', hdr_style),
         Paragraph('MISSING MATERIAL (TO BE INDEPENDENTLY VERIFIED)', hdr_style)],
        [Paragraph(avail_text,   cell_style),
         Paragraph(missing_text, cell_style)],
    ]
    evid_table = Table(
        evid_data,
        colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), LIGHT_BLUE),
            ('GRID',          (0,0), (-1,-1), 0.4, BORDER),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ])
    )
    story.append(evid_table)
    story.append(Spacer(1, 2))

    # ── SECTION 5: BALANCED CASE VIEW ────────────────────────────────────────
    story.append(section_label('5', 'BALANCED CASE VIEW'))
    balanced_data = [
        [Paragraph('COMPLAINANT / APPLICANT SIDE (CLAIMS & REMEDIES)', hdr_style),
         Paragraph('RESPONDENT / ACCUSED SIDE (DEFENCES & RIGHTS)', hdr_style)],
        [Paragraph(_truncate(report_data.get('complainant_side', 'Requires verification'), 350), cell_style),
         Paragraph(_truncate(report_data.get('respondent_side',  'Requires verification'), 350), cell_style)],
    ]
    balanced_table = Table(
        balanced_data,
        colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), LIGHT_BLUE),
            ('GRID',          (0,0), (-1,-1), 0.4, BORDER),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ])
    )
    story.append(balanced_table)
    story.append(Spacer(1, 2))

    # ── SECTION 6: RIGHTS & NEXT STEPS ───────────────────────────────────────
    story.append(section_label('6', 'RIGHTS & NEXT STEPS'))
    rights_data = [
        [Paragraph("PERSON'S ROLE & FORUM", hdr_style),
         Paragraph('PRACTICAL NEXT STEPS, SAFEGUARDS & DEADLINES', hdr_style)],
        [Paragraph(_truncate(report_data.get('persons_role',      'Requires verification'), 140), cell_style),
         Paragraph(_truncate(report_data.get('rights_next_steps', 'Requires verification'), 400), cell_style)],
    ]
    rights_table = Table(
        rights_data,
        colWidths=[CONTENT_W * 0.28, CONTENT_W * 0.72],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), LIGHT_BLUE),
            ('GRID',          (0,0), (-1,-1), 0.4, BORDER),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ])
    )
    story.append(rights_table)
    story.append(Spacer(1, 2))

    # ── SECTION 7: ADVOCATE REVIEW / CASE STATUS ─────────────────────────────
    story.append(section_label('7', 'ADVOCATE REVIEW / CASE STATUS'))
    adv_data = [
        [Paragraph('QUESTIONS TO DISCUSS WITH ADVOCATE', hdr_style),
         Paragraph('CURRENT STAGE & ACTION', hdr_style),
         Paragraph('RECORD DATE & VERSION', hdr_style)],
        [Paragraph(_truncate(report_data.get('advocate_questions', 'Requires verification'), 300), cell_style),
         Paragraph(_truncate(report_data.get('current_stage', 'Requires verification'), 160), cell_style),
         Paragraph(
            f"Date: {_truncate(report_data.get('last_updated_date', 'Requires verification'), 60)}<br/>"
            f"Version: {report_data.get('version', 1)}",
            cell_style
         )],
    ]
    adv_table = Table(
        adv_data,
        colWidths=[CONTENT_W * 0.44, CONTENT_W * 0.34, CONTENT_W * 0.22],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), LIGHT_BLUE),
            ('GRID',          (0,0), (-1,-1), 0.4, BORDER),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('RIGHTPADDING',  (0,0), (-1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ])
    )
    story.append(adv_table)
    story.append(Spacer(1, 3))

    # ── DISCLAIMER & CONFIDENTIALITY ─────────────────────────────────────────
    story.append(HRFlowable(width=CONTENT_W, thickness=0.4, color=BORDER, spaceBefore=0, spaceAfter=2))
    disc_text = (
        '<b>IMPORTANT ADVOCATE VERIFICATION DISCLAIMER:</b> AI-assisted legal research guidance only under Indian law; '
        'not a police finding, judicial decree, or substitute for representation by an enrolled advocate. Unverified allegations '
        'are not established facts. All statutory provisions, limitation periods, and jurisdiction must be independently verified '
        'against authoritative, current bare Acts and official Gazettes before initiating or defending formal legal proceedings.'
    )
    story.append(Paragraph(disc_text, disc_style))

    canvas_class = make_numbered_canvas(report_id)
    doc.build(story, canvasmaker=canvas_class)
    return buf.getvalue()
