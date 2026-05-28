"""
services/pdf_service.py
Scientific journal-style PDF — Nature/Cell publication quality.
"""
import io, re, logging
from datetime import datetime
logger = logging.getLogger(__name__)

# ── Color Palette (Scientific) ────────────────────────────────
C = {
    "navy":       (15,  52,  86),
    "blue":       (30,  90, 150),
    "teal":       (0,  128, 128),
    "light_blue": (210, 230, 250),
    "pale_blue":  (235, 244, 252),
    "gold":       (180, 140,  30),
    "light_gold": (255, 248, 220),
    "gray_dark":  (60,  60,  70),
    "gray_mid":   (140, 145, 155),
    "gray_light": (220, 225, 232),
    "gray_pale":  (247, 248, 250),
    "white":      (255, 255, 255),
    "black":      (20,  20,  25),
    "green":      (34, 120,  60),
    "red":        (160,  30,  30),
    "purple":     (90,  40, 130),
}

def generate_pdf(markdown_text: str, uniprot_id: str) -> bytes:
    try:
        from fpdf import FPDF
        return _build(markdown_text, uniprot_id)
    except ImportError:
        return markdown_text.encode("utf-8")

def _c(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*",   r"\1", text)
    text = re.sub(r"`(.+?)`",     r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    return text.strip()

def _sep(cells):
    return all(set(c.strip()) <= set("-:| ") for c in cells)

def _build(md: str, uid: str) -> bytes:
    from fpdf import FPDF

    class PDF(FPDF):
        def header(self):
            if self.page_no() == 1:
                return
            # Top rule
            self.set_fill_color(*C["navy"])
            self.rect(0, 0, 210, 1.5, "F")
            # Left accent
            self.set_fill_color(*C["teal"])
            self.rect(0, 0, 3, 14, "F")
            # Header text
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(*C["navy"])
            self.set_xy(6, 4)
            self.cell(80, 5, "ProteoSage  ·  AI Protein Research Platform", align="L")
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*C["gray_mid"])
            self.set_xy(90, 4)
            self.cell(115, 5, f"UniProt: {uid}  ·  {datetime.utcnow().strftime('%Y-%m-%d')}", align="R")
            self.set_draw_color(*C["gray_light"])
            self.line(6, 12, 204, 12)
            self.set_y(16)

        def footer(self):
            if self.page_no() == 1:
                return
            self.set_y(-13)
            self.set_draw_color(*C["gray_light"])
            self.line(6, self.get_y(), 204, self.get_y())
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*C["gray_mid"])
            self.set_y(self.get_y() + 2)
            self.cell(95, 5, "Confidential Research Report  ·  ProteoSage v1.0", align="L")
            self.cell(0, 5, f"Page {self.page_no()}", align="R")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=16)

    # ═══════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════
    pdf.add_page()

    # Full navy background top band
    pdf.set_fill_color(*C["navy"])
    pdf.rect(0, 0, 210, 100, "F")

    # Teal accent stripe
    pdf.set_fill_color(*C["teal"])
    pdf.rect(0, 95, 210, 5, "F")

    # Institution / platform name
    pdf.set_xy(0, 18)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(160, 200, 235)
    pdf.cell(210, 8, "ProteoSage  ·  AI Protein Research Platform", align="C")

    # Main title
    pdf.set_xy(0, 30)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*C["white"])
    # Extract protein name
    pname = uid
    for ln in md.split("\n")[:6]:
        if ln.startswith("# "):
            pname = _c(ln[2:])
            break
    # Truncate if too long
    if len(pname) > 40:
        pname = pname[:38] + "..."
    pdf.multi_cell(210, 14, pname, align="C")

    # Subtitle
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(180, 215, 245)
    pdf.set_xy(0, pdf.get_y() + 4)
    pdf.cell(210, 8, "Comprehensive Protein Research Report", align="C")

    # Metadata box (white card)
    card_y = 108
    pdf.set_fill_color(*C["white"])
    pdf.set_draw_color(*C["gray_light"])
    pdf.rect(20, card_y, 170, 52, "FD")

    # Teal left border on card
    pdf.set_fill_color(*C["teal"])
    pdf.rect(20, card_y, 3, 52, "F")

    pdf.set_xy(28, card_y + 8)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*C["navy"])
    pdf.cell(0, 8, f"UniProt Accession: {uid}", align="L")

    # Extract gene name
    gene = "—"
    for ln in md.split("\n"):
        if "**Gene:**" in ln or "Gene |" in ln:
            m = re.search(r'Gene.*?[:\|]\s*`?([A-Z0-9]+)`?', ln)
            if m:
                gene = m.group(1)
                break

    pdf.set_xy(28, card_y + 18)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C["gray_dark"])
    pdf.cell(80, 7, f"Gene Symbol:  {gene}", align="L")
    pdf.cell(0, 7, "Organism:  Homo sapiens", align="L")

    pdf.set_xy(28, card_y + 28)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(80, 7, f"Report Date:  {datetime.utcnow().strftime('%B %d, %Y')}", align="L")
    pdf.cell(0, 7, f"Generated:  {datetime.utcnow().strftime('%H:%M UTC')}", align="L")

    pdf.set_xy(28, card_y + 38)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*C["teal"])
    pdf.cell(0, 7, "AI-synthesized from 8 biomedical databases", align="L")

    # Database badges row
    badge_y = 172
    databases = ["UniProt","PubMed","ClinVar","AlphaFold","PDB","STRING","Reactome","GTEx","Open Targets"]
    badge_w = 19
    badge_x = (210 - len(databases) * badge_w) / 2
    for i, db in enumerate(databases):
        x = badge_x + i * badge_w
        pdf.set_fill_color(*C["pale_blue"])
        pdf.set_draw_color(*C["blue"])
        pdf.rect(x, badge_y, badge_w - 1, 8, "FD")
        pdf.set_xy(x, badge_y + 1)
        pdf.set_font("Helvetica", "B", 5.5)
        pdf.set_text_color(*C["navy"])
        pdf.cell(badge_w - 1, 6, db, align="C")

    # Bottom disclaimer
    pdf.set_xy(0, 240)
    pdf.set_fill_color(*C["gray_pale"])
    pdf.rect(0, 240, 210, 57, "F")
    pdf.set_draw_color(*C["gray_light"])
    pdf.line(0, 240, 210, 240)

    pdf.set_xy(15, 248)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*C["navy"])
    pdf.cell(0, 6, "About This Report", align="L")

    pdf.set_xy(15, 256)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C["gray_dark"])
    pdf.multi_cell(180, 5,
        "This report was generated by ProteoSage, an AI-powered protein research platform. "
        "Data is aggregated from nine peer-reviewed databases including UniProt, PubMed, ClinVar, "
        "AlphaFold, RCSB PDB, STRING DB, Reactome, GTEx, and Open Targets. "
        "AI synthesis performed using OpenAI GPT-4o. For research use only.")

    # ═══════════════════════════════════════════════════════════
    # CONTENT PAGES
    # ═══════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.set_margins(15, 18, 15)
    pdf.set_y(18)

    lines = md.split("\n")
    i = 0
    tbuf = []
    section_num = 0

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        # Accumulate table lines
        if s.startswith("|"):
            tbuf.append(s)
            i += 1
            continue
        elif tbuf:
            _draw_table(pdf, tbuf)
            tbuf = []

        if not s:
            pdf.ln(2)
            i += 1
            continue

        cl = _c(s)

        # ── H1: protein title ─────────────────────────────────
        if s.startswith("# "):
            pdf.set_fill_color(*C["navy"])
            pdf.rect(15, pdf.get_y(), 180, 14, "F")
            pdf.set_fill_color(*C["teal"])
            pdf.rect(15, pdf.get_y(), 4, 14, "F")
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*C["white"])
            pdf.set_xy(22, pdf.get_y() + 3)
            pdf.cell(173, 8, cl[2:].strip()[:70], align="L")
            pdf.ln(16)

        # ── H2: section headers ───────────────────────────────
        elif s.startswith("## "):
            section_num += 1
            pdf.ln(4)
            sy = pdf.get_y()
            # Background
            pdf.set_fill_color(*C["pale_blue"])
            pdf.rect(15, sy, 180, 10, "F")
            # Left accent
            pdf.set_fill_color(*C["blue"])
            pdf.rect(15, sy, 4, 10, "F")
            # Number circle
            pdf.set_fill_color(*C["teal"])
            pdf.ellipse(19, sy + 1, 8, 8, "F")
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*C["white"])
            pdf.set_xy(19, sy + 2)
            pdf.cell(8, 6, str(section_num), align="C")
            # Title
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*C["navy"])
            pdf.set_xy(30, sy + 1)
            pdf.cell(165, 8, cl[3:].strip(), align="L")
            pdf.ln(12)

        # ── H3 ───────────────────────────────────────────────
        elif s.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*C["teal"])
            pdf.set_draw_color(*C["teal"])
            pdf.line(15, pdf.get_y() + 5, 25, pdf.get_y() + 5)
            pdf.set_x(27)
            pdf.cell(0, 7, cl[4:].strip(), align="L")
            pdf.ln(1)

        # ── Badge / blockquote ────────────────────────────────
        elif s.startswith("> "):
            pdf.ln(1)
            pdf.set_fill_color(*C["light_gold"])
            pdf.set_draw_color(*C["gold"])
            bx, by = 15, pdf.get_y()
            # Draw filled rect first
            pdf.rect(bx, by, 180, 9, "F")
            pdf.set_draw_color(*C["gold"])
            pdf.rect(bx, by, 180, 9, "D")
            # Gold left bar
            pdf.set_fill_color(*C["gold"])
            pdf.rect(bx, by, 3, 9, "F")
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C["navy"])
            pdf.set_xy(bx + 6, by + 1)
            pdf.multi_cell(172, 7, cl[2:].strip())
            pdf.ln(3)

        # ── Bullet ────────────────────────────────────────────
        elif s.startswith("- ") or s.startswith("* "):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*C["black"])
            bx = pdf.get_x()
            # Teal bullet
            pdf.set_fill_color(*C["teal"])
            pdf.ellipse(18, pdf.get_y() + 2, 2, 2, "F")
            pdf.set_x(22)
            pdf.multi_cell(173, 5, cl[2:].strip())

        # ── Numbered list ─────────────────────────────────────
        elif re.match(r"^\d+\.", s):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*C["black"])
            # Number in teal
            num_m = re.match(r"^(\d+)\.\s*(.*)", cl)
            if num_m:
                num, rest = num_m.group(1), num_m.group(2)
                pdf.set_fill_color(*C["pale_blue"])
                pdf.rect(16, pdf.get_y() + 0.5, 5, 5, "F")
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(*C["navy"])
                pdf.set_xy(16, pdf.get_y() + 0.5)
                pdf.cell(5, 5, num, align="C")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*C["black"])
                pdf.set_x(23)
                pdf.multi_cell(172, 5, rest)
            else:
                pdf.set_x(22)
                pdf.multi_cell(173, 5, cl)

        # ── Divider ───────────────────────────────────────────
        elif s in ("---", "***", "___"):
            pdf.set_draw_color(*C["gray_light"])
            pdf.line(15, pdf.get_y() + 1, 195, pdf.get_y() + 1)
            pdf.ln(4)

        # ── Body text ─────────────────────────────────────────
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*C["black"])
            if cl:
                pdf.multi_cell(0, 5.5, cl)

        i += 1

    if tbuf:
        _draw_table(pdf, tbuf)

    return bytes(pdf.output())


def _draw_table(pdf, lines):
    """Render a scientific-style data table."""
    rows = []
    for line in lines:
        cells = [_c(c.strip()) for c in line.strip("|").split("|")]
        if _sep(cells):
            continue
        rows.append(cells)
    if not rows:
        return

    num_cols = max(len(r) for r in rows)
    for row in rows:
        while len(row) < num_cols:
            row.append("")

    # Dynamic column widths
    page_w = 180
    col_w = page_w / num_cols

    # Minimum row height
    ROW_H = 7
    pdf.ln(2)

    for ri, row in enumerate(rows):
        # Page break check
        if pdf.get_y() + ROW_H > pdf.h - 18:
            pdf.add_page()
            pdf.set_y(20)
            ri = 0  # Redraw header on new page

        is_hdr = ri == 0

        for ci, cell in enumerate(row):
            x = 15 + ci * col_w
            y = pdf.get_y()

            # Cell background
            if is_hdr:
                pdf.set_fill_color(*C["navy"])
            elif ri % 2 == 1:
                pdf.set_fill_color(*C["pale_blue"])
            else:
                pdf.set_fill_color(*C["white"])

            pdf.rect(x, y, col_w, ROW_H, "F")

            # Cell border
            if is_hdr:
                pdf.set_draw_color(*C["navy"])
            else:
                pdf.set_draw_color(*C["gray_light"])
            pdf.rect(x, y, col_w, ROW_H, "D")

            # Cell text
            if is_hdr:
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*C["white"])
            else:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*C["black"])

            # Truncate long text
            display = cell[:28] + ".." if len(cell) > 30 else cell
            pdf.set_xy(x + 1.5, y + 1.5)
            pdf.cell(col_w - 3, ROW_H - 3, display, align="L")

        pdf.set_y(pdf.get_y() + ROW_H)

    # Bottom rule
    pdf.set_draw_color(*C["blue"])
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
