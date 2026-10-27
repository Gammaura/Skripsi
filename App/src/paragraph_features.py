"""
Ekstraksi fitur paragraf (teks + tipografi OpenXML) yang dipakai bersama oleh
Agent 1 (Inspector) dan skrip pembangun dataset, agar fitur latih = fitur inferensi.
"""

import re
from typing import Any, Dict, Tuple

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

TWIPS_PER_PT = 20.0
TWIPS_PER_LINE = 240.0
TWIPS_PER_CM = 567.0
DEFAULT_FONT_SIZE = 12.0
DEFAULT_LINE_SPACING = 1.15

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_WHITESPACE_RE = re.compile(r"\s+")
_ALIGNMENT_NAMES = {
    WD_ALIGN_PARAGRAPH.CENTER: "CENTER",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "JUSTIFY",
    WD_ALIGN_PARAGRAPH.RIGHT: "RIGHT",
    WD_ALIGN_PARAGRAPH.LEFT: "LEFT",
}


def clean_text(text: str) -> str:
    """Membersihkan karakter kontrol dan merapatkan spasi ganda."""
    if not text:
        return ""
    return _WHITESPACE_RE.sub(" ", _CONTROL_CHARS_RE.sub("", text)).strip()


def _first_text_run(p):
    return next((run for run in p.runs if run.text.strip()), None)


def get_font_info(p) -> Tuple[float, bool, bool]:
    """(ukuran pt, bold, italic) dari run berteks pertama; fallback ke style paragraf."""
    run = _first_text_run(p)
    if run is None:
        return DEFAULT_FONT_SIZE, False, False
    style_font = p.style.font if p.style and p.style.font else None
    size = run.font.size or (style_font.size if style_font else None)
    bold = run.font.bold if run.font.bold is not None else (style_font.bold if style_font else None)
    italic = run.font.italic if run.font.italic is not None else (style_font.italic if style_font else None)
    return (size.pt if size else DEFAULT_FONT_SIZE), bool(bold), bool(italic)


def get_font_name(p, default: str = "Times New Roman") -> str:
    """Nama font run berteks pertama; fallback ke style paragraf."""
    run = _first_text_run(p)
    if run is None:
        return default
    if run.font.name:
        return run.font.name
    if p.style and p.style.font and p.style.font.name:
        return p.style.font.name
    return default


def get_alignment_str(align) -> str:
    """Menerjemahkan enum perataan Word ke label kategori fitur."""
    return _ALIGNMENT_NAMES.get(align, "DEFAULT")


def read_spacing_and_indent(pPr) -> Tuple[float, float, float, float, float]:
    """(spasi sebelum pt, spasi sesudah pt, spasi baris, indentasi baris pertama cm, indentasi kiri cm)."""
    before, after, line = 0.0, 0.0, DEFAULT_LINE_SPACING
    first_line, left = 0.0, 0.0
    if pPr is None:
        return before, after, line, first_line, left

    spacing = pPr.find(qn("w:spacing"))
    if spacing is not None:
        attrs = spacing.attrib
        if qn("w:before") in attrs:
            before = float(attrs[qn("w:before")]) / TWIPS_PER_PT
        if qn("w:after") in attrs:
            after = float(attrs[qn("w:after")]) / TWIPS_PER_PT
        if qn("w:line") in attrs:
            line = float(attrs[qn("w:line")]) / TWIPS_PER_LINE

    ind = pPr.find(qn("w:ind"))
    if ind is not None:
        attrs = ind.attrib
        if qn("w:firstLine") in attrs:
            first_line = float(attrs[qn("w:firstLine")]) / TWIPS_PER_CM
        elif qn("w:hanging") in attrs:
            first_line = -float(attrs[qn("w:hanging")]) / TWIPS_PER_CM
        if qn("w:left") in attrs:
            left = float(attrs[qn("w:left")]) / TWIPS_PER_CM
    return before, after, line, first_line, left


def uppercase_ratio(text: str) -> float:
    return sum(1 for c in text if c.isupper()) / float(len(text)) if text else 0.0


def extract_paragraph_features(p, idx: int, total: int) -> Dict[str, Any]:
    """Fitur mentah satu paragraf; urutan key = urutan kolom dataset CSV."""
    text = clean_text(p.text)
    size, bold, italic = get_font_info(p)
    pPr = p._p.pPr
    before, after, line, first_line, left = read_spacing_and_indent(pPr)
    return {
        "para_id": idx,
        "text": text,
        "style": p.style.name if p.style else "Normal",
        "char_len": len(text),
        "word_count": len(text.split()),
        "font_size": size,
        "is_bold": bold,
        "is_italic": italic,
        "align": get_alignment_str(p.alignment),
        "has_num": bool(pPr is not None and pPr.numPr is not None),
        "has_img": bool(p._p.xpath(".//w:drawing | .//w:pict")),
        "has_pgbrk": bool(p._p.xpath('.//w:br[@w:type="page"]')),
        "space_before": round(before, 2),
        "space_after": round(after, 2),
        "line_spacing": round(line, 2),
        "first_line_indent": round(first_line, 2),
        "left_indent": round(left, 2),
        "uppercase_ratio": round(uppercase_ratio(text), 3),
        "doc_pos": round(idx / float(total), 4) if total > 0 else 0.0,
    }
