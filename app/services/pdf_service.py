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
    # Minimal table colors
    "tbl_header_line": (40,  70, 110),   # dark underline beneath header
    "tbl_divider":     (210, 213, 218),  # ultra-light row separator
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
            self.set_fill_color(*C["navy"])
            self.rect(0, 0, 210, 1.5, "F")
            self.set_fill_color(*C["teal"])
            self.rect(0, 0, 3, 14, "F")
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(*C["navy"])
            self.set_xy(6, 4)
            self.cell(80, 5, "ProteoSage  .  AI Protein Research Platform", align="L")
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*C["gray_mid"])
            self.set_xy(90, 4)
            self.cell(115, 5, f"UniProt: {uid}  .  {datetime.utcnow().strftime('%Y-%m-%d')}", align="R")
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
            self.cell(95, 5, "Confidential Research Report  .  ProteoSage v1.0", align="L")
            self.cell(0, 5, f"Page {self.page_no()}", align="R")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=16)

    # ═══════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════
    pdf.add_page()

    pdf.set_fill_color(*C["navy"])
    pdf.rect(0, 0, 210, 100, "F")

    pdf.set_fill_color(*C["teal"])
    pdf.rect(0, 95, 210, 5, "F")

    pdf.set_xy(0, 18)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(160, 200, 235)
    pdf.cell(210, 8, "ProteoSage  .  AI Protein Research Platform", align="C")

    pdf.set_xy(0, 30)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*C["white"])
    pname = uid
    for ln in md.split("\n")[:6]:
        if ln.startswith("# "):
            pname = _c(ln[2:])
            break
    if len(pname) > 40:
        pname = pname[:38] + "..."
    pdf.multi_cell(210, 14, pname, align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(180, 215, 245)
    pdf.set_xy(0, pdf.get_y() + 4)
    pdf.cell(210, 8, "Comprehensive Protein Research Report", align="C")

    card_y = 108
    pdf.set_fill_color(*C["white"])
    pdf.set_draw_color(*C["gray_light"])
    pdf.rect(20, card_y, 170, 52, "FD")
    pdf.set_fill_color(*C["teal"])
    pdf.rect(20, card_y, 3, 52, "F")

    pdf.set_xy(28, card_y + 8)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*C["navy"])
    pdf.cell(0, 8, f"UniProt Accession: {uid}", align="L")

    gene = "-"
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

        elif s.startswith("## "):
            section_num += 1
            pdf.ln(4)
            sy = pdf.get_y()
            pdf.set_fill_color(*C["pale_blue"])
            pdf.rect(15, sy, 180, 10, "F")
            pdf.set_fill_color(*C["blue"])
            pdf.rect(15, sy, 4, 10, "F")
            pdf.set_fill_color(*C["teal"])
            pdf.ellipse(19, sy + 1, 8, 8, "F")
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*C["white"])
            pdf.set_xy(19, sy + 2)
            pdf.cell(8, 6, str(section_num), align="C")
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*C["navy"])
            pdf.set_xy(30, sy + 1)
            pdf.cell(165, 8, cl[3:].strip(), align="L")
            pdf.ln(12)

        elif s.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*C["teal"])
            pdf.set_draw_color(*C["teal"])
            pdf.line(15, pdf.get_y() + 5, 25, pdf.get_y() + 5)
            pdf.set_x(27)
            pdf.cell(0, 7, cl[4:].strip(), align="L")
            pdf.ln(1)

        elif s.startswith("> "):
            pdf.ln(1)
            pdf.set_fill_color(*C["light_gold"])
            bx, by = 15, pdf.get_y()
            pdf.rect(bx, by, 180, 9, "F")
            pdf.set_draw_color(*C["gold"])
            pdf.rect(bx, by, 180, 9, "D")
            pdf.set_fill_color(*C["gold"])
            pdf.rect(bx, by, 3, 9, "F")
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C["navy"])
            pdf.set_xy(bx + 6, by + 1)
            pdf.multi_cell(172, 7, cl[2:].strip())
            pdf.ln(3)

        elif s.startswith("- ") or s.startswith("* "):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*C["black"])
            pdf.set_fill_color(*C["teal"])
            pdf.ellipse(18, pdf.get_y() + 2, 2, 2, "F")
            pdf.set_x(22)
            pdf.multi_cell(173, 5, cl[2:].strip())

        elif re.match(r"^\d+\.", s):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*C["black"])
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

        elif s in ("---", "***", "___"):
            pdf.set_draw_color(*C["gray_light"])
            pdf.line(15, pdf.get_y() + 1, 195, pdf.get_y() + 1)
            pdf.ln(4)

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
    """
    Minimal / Borderless table style.

    Rules
    -----
    - No outer border, no cell boxes, no background fills on data rows.
    - Header row: bold dark text + a solid 0.5 pt underline beneath it.
    - Data rows: plain text separated by ultra-light hairline rules.
    - A final thin bottom rule closes the table visually.
    - Compact 6 pt row height; text never wraps (truncated with '..').
    """
    # ── Parse ────────────────────────────────────────────────────────────────
    rows = []
    for line in lines:
        cells = [_c(c.strip()) for c in line.strip("|").split("|")]
        if _sep(cells):
            continue
        rows.append(cells)
    if not rows:
        return

    num_cols  = max(len(r) for r in rows)
    for row in rows:
        while len(row) < num_cols:
            row.append("")

    # ── Constants ────────────────────────────────────────────────────────────
    TABLE_W   = 180
    ROW_H     = 6
    COL_PAD   = 2
    COL_W     = TABLE_W / num_cols
    LEFT_X    = 15
    MAX_CHARS = max(8, int(COL_W / 2.0))

    pdf.ln(3)

    for ri, row in enumerate(rows):
        if pdf.get_y() + ROW_H > pdf.h - 18:
            pdf.add_page()
            pdf.set_y(20)

        y      = pdf.get_y()
        is_hdr = (ri == 0)

        # ── Header underline (drawn before text so text sits on top) ─────────
        if is_hdr:
            pdf.set_draw_color(*C["tbl_header_line"])
            pdf.set_line_width(0.5)
            pdf.line(LEFT_X, y + ROW_H, LEFT_X + TABLE_W, y + ROW_H)
            pdf.set_line_width(0.2)   # reset
        else:
            # Ultra-light hairline between data rows
            pdf.set_draw_color(*C["tbl_divider"])
            pdf.set_line_width(0.2)
            pdf.line(LEFT_X, y, LEFT_X + TABLE_W, y)

        # ── Cell text ────────────────────────────────────────────────────────
        for ci, cell in enumerate(row):
            x       = LEFT_X + ci * COL_W
            display = cell if len(cell) <= MAX_CHARS else cell[:MAX_CHARS - 2] + ".."

            if is_hdr:
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*C["navy"])
            else:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*C["gray_dark"])

            pdf.set_xy(x + COL_PAD, y + 1)
            pdf.cell(COL_W - COL_PAD * 2, ROW_H - 1, display, align="L")

        pdf.set_y(y + ROW_H)

    # ── Final bottom rule ────────────────────────────────────────────────────
    pdf.set_draw_color(*C["tbl_header_line"])
    pdf.set_line_width(0.4)
    pdf.line(LEFT_X, pdf.get_y(), LEFT_X + TABLE_W, pdf.get_y())
    pdf.set_line_width(0.2)   # reset

    pdf.ln(5)
