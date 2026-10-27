"""Pembangun elemen XML, manipulasi child element, dan styling run yang konsisten."""

from typing import Dict, Optional

from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

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
    """Mengganti child pertama yang bertag sama dengan `element`, lalu menambahkannya di akhir."""
    existing = parent.find(element.tag)
    if existing is not None:
        parent.remove(existing)
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
