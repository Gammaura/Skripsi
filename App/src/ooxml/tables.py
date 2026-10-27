"""Format tabel: standar APA 7 termodifikasi dan kotak materai Halaman Pernyataan."""

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

from src.ooxml.xml import replace_child, style_run, w_el

_THICK = 'w:val="single" w:sz="8" w:space="0" w:color="000000"'
_THIN = 'w:val="single" w:sz="4" w:space="0" w:color="000000"'

_APA7_TABLE_BORDERS = (
    f"<w:top {_THICK}/><w:bottom {_THICK}/>"
    '<w:left w:val="none"/><w:right w:val="none"/>'
    f'<w:insideH {_THIN}/><w:insideV w:val="none"/>'
)
_HEADER_CELL_BORDERS = f'<w:top {_THICK}/><w:bottom {_THICK}/><w:left w:val="none"/><w:right w:val="none"/>'
_NO_TOP_SIDES = '<w:top w:val="none"/><w:left w:val="none"/><w:right w:val="none"/>'
_LAST_ROW_CELL_BORDERS = f"{_NO_TOP_SIDES}<w:bottom {_THICK}/>"
_BODY_ROW_CELL_BORDERS = f"{_NO_TOP_SIDES}<w:bottom {_THIN}/>"

_MATERAI_WIDTH_DXA = "2835"   # ~5.0 cm
_MATERAI_INDENT_DXA = "4076"  # ~7.19 cm, sejajar kanan titik dua
_MATERAI_BORDERS = (
    f"<w:top {_THIN}/><w:left {_THIN}/><w:bottom {_THIN}/><w:right {_THIN}/>"
    '<w:insideH w:val="none"/><w:insideV w:val="none"/>'
)


def _format_cell_paragraphs(cell, *, bold=None, center=False, padding_pt=None) -> None:
    for p in cell.paragraphs:
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if padding_pt is None:
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
        else:
            p.paragraph_format.space_before = Pt(padding_pt)
            p.paragraph_format.space_after = Pt(padding_pt)
            p.paragraph_format.line_spacing = 1.0
        for run in p.runs:
            style_run(run, 10, bold=bold)


def format_materai_box(table) -> None:
    """Kotak materai berbingkai 4 sisi di sebelah kanan titik dua (template resmi UEU)."""
    tblPr = table._tbl.tblPr
    jc = tblPr.find(qn("w:jc"))
    if jc is not None:
        tblPr.remove(jc)  # tanpa perataan tengah agar tblInd berlaku
    replace_child(tblPr, w_el("tblW", {"w": _MATERAI_WIDTH_DXA, "type": "dxa"}))
    replace_child(tblPr, w_el("tblInd", {"w": _MATERAI_INDENT_DXA, "type": "dxa"}))
    replace_child(tblPr, w_el("tblBorders", inner=_MATERAI_BORDERS))

    for row in table.rows:
        for cell in row.cells:
            replace_child(cell._tc.get_or_add_tcPr(), w_el("tcW", {"w": _MATERAI_WIDTH_DXA, "type": "dxa"}))
            _format_cell_paragraphs(cell, center=True)


def format_table_apa7(table) -> None:
    """Garis horizontal saja (tanpa garis vertikal), header abu-abu, TNR 10 pt spasi 1.0."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    replace_child(table._tbl.tblPr, w_el("tblBorders", inner=_APA7_TABLE_BORDERS))

    rows = table.rows
    if len(rows) == 0:
        return

    for cell in rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        replace_child(tcPr, w_el("shd", {"val": "clear", "color": "auto", "fill": "D9D9D9"}))
        replace_child(tcPr, w_el("tcBorders", inner=_HEADER_CELL_BORDERS))
        _format_cell_paragraphs(cell, bold=True, center=True, padding_pt=2)

    last_idx = len(rows) - 1
    for r_idx in range(1, len(rows)):
        borders = _LAST_ROW_CELL_BORDERS if r_idx == last_idx else _BODY_ROW_CELL_BORDERS
        for cell in rows[r_idx].cells:
            replace_child(cell._tc.get_or_add_tcPr(), w_el("tcBorders", inner=borders))
            _format_cell_paragraphs(cell, padding_pt=2)

    # Baris tidak terbelah antar halaman; header berulang di setiap halaman
    for r_idx, row in enumerate(rows):
        trPr = row._tr.get_or_add_trPr()
        if trPr.find(qn("w:cantSplit")) is None:
            trPr.append(w_el("cantSplit"))
        if r_idx == 0 and trPr.find(qn("w:tblHeader")) is None:
            trPr.append(w_el("tblHeader"))


def format_table(table) -> None:
    """Memilih format kotak materai atau APA 7 berdasarkan isi tabel."""
    table_text = " ".join(cell.text.strip().lower() for row in table.rows for cell in row.cells)
    if "materai" in table_text:
        format_materai_box(table)
    else:
        format_table_apa7(table)
