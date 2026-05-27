"""
services/pdf_service.py
Generates PDF using fpdf2 which is more reliable on Streamlit Cloud.
Falls back to simple text PDF if needed.
"""
import io
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_pdf(markdown_text: str, uniprot_id: str) -> bytes:
    """Convert markdown report to PDF bytes."""
    
    # Try fpdf2 first (lighter than reportlab)
    try:
        from fpdf import FPDF
        return _generate_with_fpdf(markdown_text, uniprot_id)
    except ImportError:
        pass
    
    # Try reportlab
    try:
        import reportlab
        return _generate_with_reportlab(markdown_text, uniprot_id)
    except ImportError:
        pass

    # Final fallback: plain text PDF-like bytes
    return _generate_plain(markdown_text, uniprot_id)


def _generate_with_fpdf(markdown_text: str, uniprot_id: str) -> bytes:
    """Generate PDF using fpdf2."""
    from fpdf import FPDF

    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(26, 58, 92)
            self.cell(0, 8, "ProteoSage - AI Protein Research Platform", align="C")
            self.ln(4)
            self.set_draw_color(44, 95, 138)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"ProteoSage | Page {self.page_no()} | {datetime.utcnow().strftime('%Y-%m-%d')}", align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    lines = markdown_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            pdf.ln(2)
            continue

        # Clean markdown
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
        clean = re.sub(r"\*(.+?)\*", r"\1", clean)
        clean = re.sub(r"`(.+?)`", r"\1", clean)
        clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)
        clean = re.sub(r"[^\x00-\x7F]+", "", clean)  # Remove non-ASCII

        if stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(26, 58, 92)
            pdf.multi_cell(0, 8, clean[2:].strip())
            pdf.ln(2)
        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(44, 95, 138)
            pdf.multi_cell(0, 7, clean[3:].strip())
            pdf.ln(1)
        elif stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(58, 122, 191)
            pdf.multi_cell(0, 6, clean[4:].strip())
        elif stripped.startswith("> "):
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(26, 58, 92)
            pdf.set_fill_color(232, 240, 254)
            pdf.multi_cell(0, 6, clean[2:].strip(), fill=True)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, f"  - {clean[2:].strip()}")
        elif stripped.startswith("|"):
            # Simple table row
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(50, 50, 50)
            cells = [c.strip() for c in clean.strip("|").split("|")]
            if not all(set(c.strip()) <= set("-:| ") for c in cells):
                row_text = " | ".join(cells)
                pdf.multi_cell(0, 5, row_text)
        elif stripped in ("---", "***"):
            pdf.set_draw_color(200, 200, 200)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)
        elif re.match(r"^\d+\.", stripped):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, f"  {clean}")
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(0, 0, 0)
            if clean:
                pdf.multi_cell(0, 5, clean)

    return bytes(pdf.output())


def _generate_with_reportlab(markdown_text: str, uniprot_id: str) -> bytes:
    """Generate PDF using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    lines = markdown_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.2*cm))
            continue
        clean = re.sub(r"[^\x00-\x7F]+", "", stripped)
        clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", clean)
        clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)
        if stripped.startswith("# "):
            story.append(Paragraph(clean[2:], styles["Title"]))
        elif stripped.startswith("## "):
            story.append(Paragraph(clean[3:], styles["Heading1"]))
        elif stripped.startswith("- "):
            story.append(Paragraph(f"• {clean[2:]}", styles["Normal"]))
        else:
            story.append(Paragraph(clean, styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()


def _generate_plain(markdown_text: str, uniprot_id: str) -> bytes:
    """Fallback: return markdown as downloadable text file."""
    return markdown_text.encode("utf-8")