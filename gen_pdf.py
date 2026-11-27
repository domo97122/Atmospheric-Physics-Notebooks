# -*- coding: utf-8 -*-
"""Génère Fiche_revision_meteo_L3.pdf à partir de Fiche_revision_meteo_L3.md"""
import os, re, matplotlib
from fpdf import FPDF

FONT_DIR = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
SRC = "Fiche_revision_meteo_L3.md"
OUT = "Fiche_revision_meteo_L3.pdf"

# --- Nettoyage du texte pour la police DejaVu (pas d'emojis, indices en chiffres normaux) ---
EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\uFE0F\u200D]")
SUBS = {"₂": "2", "₄": "4", "ₓ": "x", "₃": "3", "₆": "6", "₈": "8", "₉": "9", "₁": "1", "₅": "5", "₇": "7", "₀": "0"}

def clean(s: str) -> str:
    s = EMOJI_RE.sub("", s)
    for k, v in SUBS.items():
        s = s.replace(k, v)
    s = re.sub(r"(?<!\*)\*(?!\*)", "", s)  # retire les marqueurs d'italique simples
    return s.strip()

class PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Fiche de révision — Météorologie L3 — page {self.page_no()}", align="C")

pdf = PDF(orientation="P", unit="mm", format="A4")
pdf.set_margins(15, 14, 15)
pdf.set_auto_page_break(True, margin=16)
pdf.add_font("DejaVu", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
pdf.add_font("DejaVu", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
pdf.add_font("DejaVu", "I", os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf"))
pdf.add_font("DejaVu", "BI", os.path.join(FONT_DIR, "DejaVuSans-BoldOblique.ttf"))
pdf.add_page()

PAGE_W = pdf.w - pdf.l_margin - pdf.r_margin  # largeur utile
BODY = 10
LINE_H = 5.2

def para(text, size=BODY, style="", indent=0, space_after=2.5):
    pdf.set_font("DejaVu", style, size)
    pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(PAGE_W - indent, LINE_H, text, markdown=True)
    pdf.ln(space_after)

def heading(text, size, space_before=5, space_after=3):
    pdf.ln(space_before)
    pdf.set_font("DejaVu", "B", size)
    pdf.multi_cell(PAGE_W, size * 0.45 + 2, text, markdown=True)
    pdf.ln(space_after)

def render_table(rows):
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    # largeurs proportionnelles au contenu
    maxlen = [max(len(r[c]) for r in rows) for c in range(ncols)]
    total = sum(maxlen) or 1
    widths = [max(18, PAGE_W * l / total) for l in maxlen]
    scale = PAGE_W / sum(widths)
    widths = [w * scale for w in widths]
    line_h = 4.6
    for ri, row in enumerate(rows):
        style = "B" if ri == 0 else ""
        pdf.set_font("DejaVu", style, 9)
        nlines = 1
        for c in range(ncols):
            n = pdf.multi_cell(widths[c], line_h, row[c], markdown=True, dry_run=True)
            nlines = max(nlines, n)
        row_h = nlines * line_h + 2.4
        if pdf.get_y() + row_h > pdf.h - 16:
            pdf.add_page()
        x0, y0 = pdf.l_margin, pdf.get_y()
        x = x0
        for c in range(ncols):
            if ri == 0:
                pdf.set_fill_color(225, 230, 240)
                pdf.rect(x, y0, widths[c], row_h, style="FD")
            else:
                pdf.rect(x, y0, widths[c], row_h, style="D")
            pdf.set_xy(x + 1.2, y0 + 1.2)
            pdf.set_font("DejaVu", style, 9)
            pdf.multi_cell(widths[c] - 2.4, line_h, row[c], markdown=True)
            x += widths[c]
        pdf.set_y(y0 + row_h)
    pdf.ln(4)

lines = open(SRC, encoding="utf-8").read().splitlines()
i = 0
while i < len(lines):
    raw = lines[i]
    line = clean(raw)
    if not line:
        i += 1
        continue
    if line.startswith("|"):
        rows = []
        while i < len(lines) and clean(lines[i]).startswith("|"):
            cells = [c.strip() for c in clean(lines[i]).strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):  # saute le séparateur |---|
                rows.append(cells)
            i += 1
        if rows:
            render_table(rows)
        continue
    if line == "---":
        pdf.ln(1)
        pdf.set_draw_color(160, 160, 160)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(4)
    elif line.startswith("# "):
        heading(line[2:], 17, space_before=0, space_after=2)
    elif line.startswith("## "):
        heading(line[3:], 13)
    elif line.startswith("### "):
        heading(line[4:], 11)
    elif line.startswith("- "):
        para("•  " + line[2:], indent=4)
    elif re.match(r"^\d+\.\s", line):
        para(line, indent=4)
    elif line.startswith("> "):
        para(line[2:], style="I", indent=8)
    else:
        para(line)
    i += 1

pdf.output(OUT)
print("OK ->", OUT, os.path.getsize(OUT), "octets")
