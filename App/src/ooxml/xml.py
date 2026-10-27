"""Pembangun elemen XML, manipulasi child element, dan styling run yang konsisten."""

from typing import Dict, Optional

from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.text.run import Run

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
VML_NS = "urn:schemas-microsoft-com:vml"
OFFICE_NS = "urn:schemas-microsoft-com:office:office"
NS = {"w": W_NS}

FONT_NAME = "Times New Roman"
BLACK = RGBColor(0, 0, 0)


def w_el(tag: str, attrs: Optional[Dict[str, str]] = None, inner: str = ""):
    """Membuat elemen `<w:tag>` dengan atribut ber-prefix `w:` (urutan atribut dipertahankan)."""
    attr_str = "".join(f' w:{name}="{value}"' for name, value in (attrs or {}).items())
    if inner:
        return parse_xml(f'<w:{tag} xmlns:w="{W_NS}"{attr_str}>{inner}</w:{tag}>')
    return parse_xml(f'<w:{tag} xmlns:w="{W_NS}"{attr_str}/>')


def spacing_el(before: int, after: int, line: Optional[int] = None):
    """Elemen `<w:spacing>`; jika `line` diisi, lineRule otomatis 'auto'."""
    attrs = {"before": str(before), "after": str(after)}
    if line is not None:
        attrs.update({"line": str(line), "lineRule": "auto"})
    return w_el("spacing", attrs)


def num_pr_el(ilvl: str, num_id: str):
    """Elemen `<w:numPr>` yang mengikat paragraf ke level multilevel list tertentu."""
    return w_el("numPr", inner=f'<w:ilvl w:val="{ilvl}"/><w:numId w:val="{num_id}"/>')


def remove_child(parent, tag: str) -> None:
    """Menghapus child pertama dengan tag `tag` (jika ada)."""
    child = parent.find(qn(tag))
    if child is not None:
        parent.remove(child)


def replace_child(parent, element) -> None:
    """Mengganti child pertama yang bertag sama dengan `element`.

    Bila `parent` adalah elemen oxml python-docx (mis. `w:pPr`), elemen disisipkan pada posisi
    sesuai urutan skema OOXML; selain itu ditambahkan di akhir.
    """
    existing = parent.find(element.tag)
    if existing is not None:
        parent.remove(existing)
    insert = getattr(parent, f"_insert_{element.tag.split('}')[-1]}", None)
    if insert is not None:
        insert(element)
    else:
        parent.append(element)


def upsert_val(parent, tag: str, value: str) -> None:
    """Menetapkan atribut `w:val` pada child `tag`; membuat child baru jika belum ada."""
    child = parent.find(qn(tag))
    if child is not None:
        child.set(qn("w:val"), value)
    else:
        parent.append(w_el(tag.split(":")[-1], {"val": value}))


def style_run(run, size_pt: float, *, bold: Optional[bool] = None, italic: Optional[bool] = None, black: bool = True) -> None:
    """Menerapkan tipografi baku UEU (Times New Roman) pada sebuah run."""
    run.font.name = FONT_NAME
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if black:
        run.font.color.rgb = BLACK


# Urutan anak w:pPr menurut skema OOXML (CT_PPr). Word diam-diam mengabaikan elemen yang
# salah urutan, mis. numPr setelah spacing membuat nomor sub-bab '1.1' tidak tampil.
_PPR_ORDER = {qn(f"w:{tag}"): idx for idx, tag in enumerate((
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
    "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
    "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
    "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle",
    "rPr", "sectPr", "pPrChange",
))}
_PPR_UNKNOWN_POS = _PPR_ORDER[qn("w:rPr")] - 0.5


def sort_ppr_children(root) -> None:
    """Mengurutkan ulang anak setiap w:pPr di bawah `root` sesuai skema OOXML (urutan stabil)."""
    for pPr in root.iter(qn("w:pPr")):
        children = list(pPr)
        ordered = sorted(children, key=lambda child: _PPR_ORDER.get(child.tag, _PPR_UNKNOWN_POS))
        if ordered != children:
            for child in ordered:
                pPr.append(child)


_THEME_FONT_ATTRS = tuple(qn(f"w:{name}") for name in ("asciiTheme", "hAnsiTheme", "cstheme", "eastAsiaTheme"))


def normalize_run_fonts(p_elem, size_pt: float, *, black: bool = True) -> None:
    """Menyeragamkan font & ukuran seluruh run paragraf (termasuk di hyperlink, sitasi Mendeley,
    dan field) tanpa membuang italic, bold, superscript, maupun footnote."""
    for r in p_elem.iter(qn("w:r")):
        run = Run(r, None)
        style_run(run, size_pt, black=black)
        r_fonts = r.rPr.find(qn("w:rFonts"))
        r_fonts.set(qn("w:cs"), FONT_NAME)
        for attr in _THEME_FONT_ATTRS:  # font tema mengalahkan w:ascii bila dibiarkan
            r_fonts.attrib.pop(attr, None)
        is_note_ref = r.find(qn("w:footnoteReference")) is not None or r.find(qn("w:endnoteReference")) is not None
        if is_note_ref and run.font.superscript is None:
            run.font.superscript = True
