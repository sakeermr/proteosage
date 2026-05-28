"""
services/pdf_service.py
Beautiful PDF generation with proper tables, cover page, and charts.
"""
import io
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_pdf(markdown_text: str, uniprot_id: str) -> bytes:
    """Convert markdown report to beautiful PDF bytes."""
    try:
        from fpdf import FPDF
        return _generate_with_fpdf(markdown_text, uniprot_id)
    except ImportError:
        return markdown_text.encode("utf-8")


def _clean(text: str) -> str:
    """Clean markdown syntax and non-ASCII characters."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    return text.strip()


def _is_separator(cells):
    """Check if table row is a separator line like |---|---|"""
    return all(set(c.strip()) <= set("-:| ") for c in cells)


def _generate_with_fpdf(markdown_text: str, uniprot_id: str) -> bytes:
    from fpdf import FPDF

    # ── Colors ────────────────────────────────────────────────
    DARK_BLUE = (26, 58, 92)
    MED_BLUE = (44, 95, 138)
    LIGHT_BLUE = (58, 122, 191)
    PALE_BLUE = (232, 240, 254)
    PALE_GRAY = (245, 247, 250)
    MID_GRAY = (200, 210, 220)
    WHITE = (255, 255, 255)
    BLACK = (30, 30, 30)
    GREEN = (34, 139, 34)
    ORANGE = (200, 100, 0)

    class PDF(FPDF):
        def header(self):
            if self.page_no() == 1:
                return
            self.set_fill_color(*DARK_BLUE)
            self.rect(0, 0, 210, 12, "F")
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*WHITE)
            self.set_y(2)
            self.cell(0, 8, "ProteoSage  |  AI Protein Research Platform", align="C")
            self.set_y(13)
            self.set_text_color(*BLACK)

        def footer(self):
            if self.page_no() == 1:
                return
            self.set_y(-12)
            self.set_fill_color(*DARK_BLUE)
            self.rect(0, self.get_y(), 210, 15, "F")
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*WHITE)
            self.cell(0, 8,
                f"ProteoSage  |  Page {self.page_no()}  |  {datetime.utcnow().strftime('%Y-%m-%d')}",
                align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=18)

    # ── Cover Page ────────────────────────────────────────────
    pdf.add_page()

    # Background gradient effect
    for i in range(120):
        ratio = i / 120
        r = int(26 + (44 - 26) * ratio)
        g = int(58 + (95 - 58) * ratio)
        b = int(92 + (138 - 92) * ratio)
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, i * 2.5, 210, 2.5, "F")

    # Logo area
    pdf.set_y(35)
    pdf.set_font("Helvetica", "B", 42)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 20, "ProteoSage", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(180, 210, 240)
    pdf.cell(0, 10, "AI Protein Research Platform", align="C")
    pdf.ln(20)

    # White card for report info
    pdf.set_fill_color(*WHITE)
    pdf.set_draw_color(*WHITE)
    pdf.round_corner = True
    pdf.rect(25, pdf.get_y(), 160, 80, "F")

    pdf.set_y(pdf.get_y() + 8)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*DARK_BLUE)

    # Extract protein name from markdown
    protein_name = uniprot_id
    for line in markdown_text.split("\n")[:5]:
        if line.startswith("# "):
            protein_name = _clean(line[2:])
            break

    pdf.multi_cell(160, 10, protein_name, align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*MED_BLUE)
    pdf.cell(0, 8, f"UniProt ID: {uniprot_id}", align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 120, 140)
    pdf.cell(0, 6, f"Generated: {datetime.utcnow().strftime('%B %d, %Y  %H:%M UTC')}", align="C")
    pdf.ln(5)
    pdf.cell(0, 6, "8 Databases  |  AI Synthesis  |  Publication Quality", align="C")

    # Bottom info bar
    pdf.set_y(240)
    pdf.set_fill_color(*MED_BLUE)
    pdf.rect(0, 240, 210, 57, "F")

    pdf.set_y(248)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 8, "Data Sources", align="C")
    pdf.ln(8)

    dbs = ["UniProt", "PubMed", "ClinVar", "AlphaFold",
           "RCSB PDB", "STRING DB", "Reactome", "GTEx", "Open Targets"]
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(180, 210, 240)
    db_text = "  |  ".join(dbs)
    pdf.cell(0, 6, db_text, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 190, 220)
    pdf.cell(0, 6, "Confidential Research Report", align="C")

    # ── Content Pages ─────────────────────────────────────────
    pdf.add_page()
    pdf.set_margins(15, 18, 15)
    pdf.set_y(18)

    lines = markdown_text.split("\n")
    i = 0
    table_buffer = []
    in_table = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Collect table lines
        if stripped.startswith("|"):
            table_buffer.append(stripped)
            i += 1
            continue
        else:
            # Render buffered table
            if table_buffer:
                _render_table(pdf, table_buffer, DARK_BLUE, MED_BLUE,
                             PALE_BLUE, PALE_GRAY, MID_GRAY, WHITE, BLACK)
                table_buffer = []

        if not stripped:
            pdf.ln(2)
            i += 1
            continue

        clean = _clean(stripped)

        if stripped.startswith("# "):
            # Major title
            pdf.set_fill_color(*DARK_BLUE)
            pdf.rect(15, pdf.get_y(), 180, 12, "F")
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(*WHITE)
            pdf.multi_cell(180, 12, clean[2:].strip(), align="L")
            pdf.ln(3)

        elif stripped.startswith("## "):
            # Section header with accent bar
            pdf.ln(3)
            pdf.set_fill_color(*MED_BLUE)
            pdf.rect(15, pdf.get_y(), 4, 9, "F")
            pdf.set_x(21)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*DARK_BLUE)
            pdf.multi_cell(174, 9, clean[3:].strip())
            pdf.set_draw_color(*MID_GRAY)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)

        elif stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*LIGHT_BLUE)
            pdf.multi_cell(0, 7, clean[4:].strip())
            pdf.ln(1)

        elif stripped.startswith("> "):
            # Badge/highlight box
            pdf.set_fill_color(*PALE_BLUE)
            pdf.set_draw_color(*MED_BLUE)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*DARK_BLUE)
            pdf.multi_cell(0, 7, f"  {clean[2:].strip()}", fill=True)
            pdf.ln(2)

        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*BLACK)
            pdf.set_x(20)
            pdf.set_fill_color(*MED_BLUE)
            # Bullet dot
            x, y = pdf.get_x() - 5, pdf.get_y() + 2.5
            pdf.ellipse(x, y, 1.5, 1.5, "F")
            pdf.set_x(22)
            pdf.multi_cell(173, 5, clean[2:].strip())

        elif stripped in ("---", "***", "___"):
            pdf.set_draw_color(*MID_GRAY)
            pdf.line(15, pdf.get_y() + 1, 195, pdf.get_y() + 1)
            pdf.ln(4)

        elif re.match(r"^\d+\.", stripped):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*BLACK)
            pdf.set_x(20)
            pdf.multi_cell(175, 5, clean)

        elif stripped.startswith("**") and stripped.endswith("**"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*DARK_BLUE)
            pdf.multi_cell(0, 6, clean)

        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*BLACK)
            if clean:
                pdf.multi_cell(0, 5, clean)

        i += 1

    # Render any remaining table
    if table_buffer:
        _render_table(pdf, table_buffer, DARK_BLUE, MED_BLUE,
                     PALE_BLUE, PALE_GRAY, MID_GRAY, WHITE, BLACK)

    return bytes(pdf.output())


def _render_table(pdf, table_lines, DARK_BLUE, MED_BLUE,
                  PALE_BLUE, PALE_GRAY, MID_GRAY, WHITE, BLACK):
    """Render a beautiful formatted table."""
    from fpdf import FPDF

    rows = []
    for line in table_lines:
        cells = [_clean(c.strip()) for c in line.strip("|").split("|")]
        if _is_separator(cells):
            continue
        rows.append(cells)

    if not rows:
        return

    num_cols = max(len(r) for r in rows)
    # Normalize
    for row in rows:
        while len(row) < num_cols:
            row.append("")

    page_width = 180  # 210 - 30 margins
    col_width = page_width / num_cols

    pdf.ln(2)

    for row_idx, row in enumerate(rows):
        row_h = 6
        is_header = row_idx == 0

        # Check if content will overflow page
        if pdf.get_y() + row_h > pdf.h - 20:
            pdf.add_page()
            pdf.set_y(20)

        for col_idx, cell in enumerate(row):
            x = 15 + col_idx * col_width
            y = pdf.get_y()

            # Background
            if is_header:
                pdf.set_fill_color(*DARK_BLUE)
            elif row_idx % 2 == 0:
                pdf.set_fill_color(*PALE_GRAY)
            else:
                pdf.set_fill_color(*WHITE)

            pdf.rect(x, y, col_width, row_h, "F")

            # Border
            pdf.set_draw_color(*MID_GRAY)
            pdf.rect(x, y, col_width, row_h)

            # Text
            if is_header:
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*WHITE)
            else:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*BLACK)

            pdf.set_xy(x + 1, y + 1)
            pdf.cell(col_width - 2, row_h - 2, cell[:30], align="L")

        pdf.set_y(pdf.get_y() + row_h)

    pdf.ln(4)


def _generate_plain(markdown_text: str, uniprot_id: str) -> bytes:
    return markdown_text.encode("utf-8")
