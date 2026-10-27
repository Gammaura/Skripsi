"""
AGENT 3: FORMATTING ACTUATOR (Penegak Format & Tata Letak OpenXML) - Template Resmi UEU 2018.

Metode Cloned Template Seed:
1. Konten naskah disuntikkan ke salinan `data/template_clean_ueu.docx` sesuai label Approved Blueprint.
2. Heading 1/2/3 terikat ke multilevel list native Word (BAB I, 1.1, 1.1.1) dan Navigation Pane.
3. Daftar Isi, Daftar Tabel, dan Daftar Gambar disusun otomatis dengan tab leader titik.
4. Penomoran halaman ganda: Romawi kecil di bagian awal, Latin mulai 1 di Bab Isi.
5. Tabel diformat standar APA 7 (tanpa garis vertikal); kotak materai dipertahankan.
6. Zero-loss: gambar, rumus, OLE, field, hyperlink, dan elemen tak dikenal di-deep-clone apa adanya.
"""

import copy
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.table import Table

from src.ooxml.cloning import (
    clone_body_element,
    clone_paragraph,
    clone_table,
    has_content_besides_ppr,
    has_drawing,
    has_rich_content,
)
from src.ooxml.fields import add_seq_caption_field, italicize_foreign_terms
from src.ooxml.numbering import (
    add_restarting_list_num,
    ensure_heading_multilevel_list,
    next_num_id,
    normalize_template_bab_level,
)
from src.ooxml.tables import format_table
from src.ooxml.text import SUBSUB_NUMBER_RE, strip_bab_prefix, strip_subbab_number, to_roman, to_title_case
from src.ooxml.toc import generate_table_of_contents
from src.ooxml.xml import num_pr_el, remove_child, replace_child, spacing_el, style_run, w_el

DEFAULT_OUTPUT_PATH = "output/hasil_skripsi_rapi.docx"
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "template_clean_ueu.docx")
HEADING_NUM_ID = "1"
FIRST_CHAPTER_PREFIXES = ("BAB 1", "BAB I", "PENDAHULUAN", "BAB 01")
KEYWORD_PREFIXES = ("kata kunci", "keywords")

# (teks label, regex prefiks, spasi sebelum, spasi sesudah) dalam dxa
_CAPTION_STYLES = {
    "CAPTION_GAMBAR": ("Gambar", r"^(Gambar|Figure)\s*[\.\d\s:\-]+", 60, 180),
    "CAPTION_TABEL": ("Tabel", r"^(Tabel|Table)\s*[\.\d\s:\-]+", 180, 60),
}


def _ind(**attrs) -> Any:
    return w_el("ind", {name.replace("first_line", "firstLine"): str(v) for name, v in attrs.items()})


def _jc(value: str) -> Any:
    return w_el("jc", {"val": value})


@dataclass
class _BuildState:
    """Status penyusunan dokumen output selama iterasi blueprint."""

    doc_src: Any
    doc_out: Any
    numbering: Any
    next_list_num_id: int
    tables_after_para: Dict[int, list]
    inserted_tables: set = field(default_factory=set)
    current_bab: int = 0
    caption_counts: Dict[str, int] = field(default_factory=lambda: {"CAPTION_GAMBAR": 0, "CAPTION_TABEL": 0})
    src_to_out_num_id: Dict[str, str] = field(default_factory=dict)

    @property
    def caption_bab(self) -> int:
        return self.current_bab or 1


class FormattingActuatorAgent:
    """Agent 3: membangun ulang naskah di atas template resmi UEU berdasarkan Approved Blueprint."""

    def __init__(self):
        self._renderers = {
            "FRONTMATTER_TITLE": self._render_frontmatter_title,
            "COVER_METADATA": self._render_cover_metadata,
            "JUDUL_BAB": self._render_chapter_title,
            "SUB_BAB": self._render_subchapter,
            "BODY_PARAGRAPH": self._render_body_paragraph,
            "CAPTION_GAMBAR": self._render_caption,
            "CAPTION_TABEL": self._render_caption,
            "DAFTAR_PUSTAKA_ITEM": self._render_bibliography_item,
        }
        print("[Agent 3 - Formatter Actuator] Diinisialisasi dengan Format Template Tugas Akhir UEU 2018.")

    # ------------------------------------------------------------------
    # Alur utama
    # ------------------------------------------------------------------
    def format_document(self, input_docx_path: str, approved_blueprint: Dict[str, Any], output_docx_path: str = DEFAULT_OUTPUT_PATH) -> str:
        """Menyusun dokumen rapi dari naskah mentah dan Approved Blueprint, lalu menyimpannya."""
        print(f"\n[Agent 3 - Formatter Actuator] Memulai kloning template resmi UEU untuk: {input_docx_path}...")
        template_path = TEMPLATE_PATH if os.path.exists(TEMPLATE_PATH) else "data/template_clean_ueu.docx"
        doc_src = Document(input_docx_path)
        doc_out = Document(template_path)

        numbering = doc_out.part.numbering_part.element
        ensure_heading_multilevel_list(numbering)
        normalize_template_bab_level(numbering)

        has_frontmatter = self._has_frontmatter(doc_src)
        frontmatter_sect_pr, body_sect_pr = self._capture_section_properties(doc_out)
        self._clear_template_body(doc_out)

        state = _BuildState(
            doc_src=doc_src,
            doc_out=doc_out,
            numbering=numbering,
            next_list_num_id=next_num_id(numbering),
            tables_after_para=self._map_tables_to_preceding_paragraph(doc_src),
        )
        for item in approved_blueprint.get("paragraphs", []):
            orig_idx = item.get("para_id", 0)
            p_src = doc_src.paragraphs[orig_idx] if orig_idx < len(doc_src.paragraphs) else None
            renderer = self._renderers.get(item["approved_label"], self._render_unknown)
            renderer(state, item, p_src)
            self._insert_tables_after_paragraph(state, orig_idx)

        self._copy_remaining_tables(state)
        self._copy_other_body_elements(doc_src, doc_out)
        generate_table_of_contents(doc_out, has_frontmatter=has_frontmatter)
        self._apply_section_properties(doc_out, frontmatter_sect_pr, body_sect_pr)
        for update_fields in doc_out.settings.element.findall(qn("w:updateFields")):
            doc_out.settings.element.remove(update_fields)

        self._report_content_audit(doc_src, doc_out)
        out_dir = os.path.dirname(output_docx_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        doc_out.save(output_docx_path)
        print(f"[Agent 3 - Formatter Actuator] Selesai! Berkas tersimpan dengan sempurna di: {output_docx_path}")
        return output_docx_path

    # ------------------------------------------------------------------
    # Persiapan template & struktur section
    # ------------------------------------------------------------------
    @staticmethod
    def _has_frontmatter(doc_src) -> bool:
        for idx, p in enumerate(doc_src.paragraphs):
            if p.text.strip().upper().startswith(FIRST_CHAPTER_PREFIXES) or p._p.get("approved_label") == "JUDUL_BAB":
                return idx > 0
        return False

    @staticmethod
    def _capture_section_properties(doc_out):
        """sectPr template: Section 1 (Romawi, bagian awal) dan Section 2 (Latin, Bab Isi)."""
        sections = doc_out.sections
        frontmatter = copy.deepcopy(sections[1]._sectPr) if len(sections) > 1 else None
        body = copy.deepcopy(sections[2]._sectPr if len(sections) > 2 else sections[-1]._sectPr)
        return frontmatter, body

    @staticmethod
    def _clear_template_body(doc_out) -> None:
        body = doc_out.element.body
        for child in list(body):
            if child.tag != qn("w:sectPr"):
                body.remove(child)

    @staticmethod
    def _map_tables_to_preceding_paragraph(doc_src) -> Dict[int, list]:
        """Memetakan setiap w:tbl ke indeks paragraf yang mendahuluinya (zero-loss)."""
        mapping: Dict[int, list] = {}
        para_count = 0
        for child in doc_src.element.body:
            if child.tag == qn("w:p"):
                para_count += 1
            elif child.tag == qn("w:tbl"):
                mapping.setdefault(max(0, para_count - 1), []).append(child)
        return mapping

    @staticmethod
    def _apply_section_properties(doc_out, frontmatter_sect_pr, body_sect_pr) -> None:
        """Memasang sectPr Romawi di paragraf terakhir sebelum Bab 1 dan sectPr Latin di akhir dokumen."""
        first_chapter = next((p for p in doc_out.paragraphs if p._p.get("approved_label") == "JUDUL_BAB"), None)
        if frontmatter_sect_pr is not None and first_chapter is not None:
            siblings = list(first_chapter._p.getparent())
            preceding = siblings[:siblings.index(first_chapter._p)]
            last_para = next((el for el in reversed(preceding) if el.tag == qn("w:p")), None)
            if last_para is not None:
                pPr = last_para.get_or_add_pPr()
                remove_child(pPr, "w:sectPr")
                pPr.append(copy.deepcopy(frontmatter_sect_pr))

        body = doc_out.element.body
        remove_child(body, "w:sectPr")
        body.append(copy.deepcopy(body_sect_pr))

    # ------------------------------------------------------------------
    # Renderer per label blueprint
    # ------------------------------------------------------------------
    @staticmethod
    def _new_paragraph(doc_out, label: str, style: Optional[str] = None):
        p = doc_out.add_paragraph()
        p._p.set("approved_label", label)
        if style:
            p.style = doc_out.styles[style]
        return p, p._p.get_or_add_pPr()

    def _render_frontmatter_title(self, state: _BuildState, item: Dict[str, Any], _p_src) -> None:
        doc_out = state.doc_out
        text = item.get("text", "").strip()
        p, pPr = self._new_paragraph(doc_out, "FRONTMATTER_TITLE", "Heading 1")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pPr.append(_jc("center"))
        if len(doc_out.paragraphs) > 1:
            pPr.append(w_el("pageBreakBefore"))
        pPr.append(w_el("keepNext"))
        pPr.append(spacing_el(480, 240, 240))
        pPr.append(w_el("outlineLvl", {"val": "0"}))
        title = strip_bab_prefix(text).upper()
        style_run(p.add_run(title or text.upper()), 14, bold=True)

    def _render_cover_metadata(self, state: _BuildState, item: Dict[str, Any], p_src) -> None:
        text = item.get("text", "").strip()
        if p_src is not None and has_rich_content(p_src._p):
            clone_paragraph(p_src._p, state.doc_src, state.doc_out, "COVER_METADATA")
        elif text:
            p, pPr = self._new_paragraph(state.doc_out, "COVER_METADATA")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pPr.append(_jc("center"))
            pPr.append(spacing_el(0, 120, 276))
            style_run(p.add_run(text), 14 if item.get("para_id", 0) == 0 else 12, bold=True)

    def _render_chapter_title(self, state: _BuildState, item: Dict[str, Any], _p_src) -> None:
        state.current_bab += 1
        state.caption_counts = {kind: 0 for kind in state.caption_counts}
        state.src_to_out_num_id.clear()

        title = strip_bab_prefix(item.get("text", "").strip())
        if not title:
            title = "PENDAHULUAN" if state.current_bab == 1 else f"BAB {to_roman(state.current_bab)}"

        p, pPr = self._new_paragraph(state.doc_out, "JUDUL_BAB", "Heading 1")
        pPr.append(num_pr_el("0", HEADING_NUM_ID))
        pPr.append(_jc("center"))
        if state.current_bab > 1:
            pPr.append(w_el("pageBreakBefore"))
        pPr.append(w_el("keepNext"))
        pPr.append(spacing_el(0, 240, 240))
        pPr.append(_ind(left=0, right=0, first_line=284))
        pPr.append(w_el("outlineLvl", {"val": "0"}))

        # Baris 'BAB I' berasal dari penomoran otomatis; judul ditulis di baris berikutnya
        line_break_run = p.add_run()
        line_break_run._r.append(w_el("br"))
        style_run(line_break_run, 14, bold=True, black=False)
        style_run(p.add_run(title.upper()), 14, bold=True)

    def _render_subchapter(self, state: _BuildState, item: Dict[str, Any], _p_src) -> None:
        state.src_to_out_num_id.clear()
        text = item.get("text", "").strip()
        is_subsub = bool(item.get("metadata", {}).get("is_subsub") or SUBSUB_NUMBER_RE.match(text))
        level, style, space_before = ("2", "Heading 3", 160) if is_subsub else ("1", "Heading 2", 240)

        p, pPr = self._new_paragraph(state.doc_out, "SUB_BAB")
        p._p.set("is_subsub", "true" if is_subsub else "false")
        p.style = state.doc_out.styles[style]
        pPr.append(spacing_el(space_before, 120, 240))
        pPr.append(_ind(left=720, hanging=720))
        pPr.append(w_el("tabs", inner='<w:tab w:val="left" w:pos="720"/>'))
        pPr.append(num_pr_el(level, HEADING_NUM_ID))
        pPr.append(w_el("keepNext"))
        pPr.append(w_el("outlineLvl", {"val": level}))
        style_run(p.add_run(to_title_case(strip_subbab_number(text))), 12, bold=True)

    def _render_body_paragraph(self, state: _BuildState, item: Dict[str, Any], p_src) -> None:
        text = item.get("text", "").strip()
        rich = p_src is not None and has_rich_content(p_src._p)

        if state.current_bab == 0:
            self._render_frontmatter_body(state, text, p_src, rich)
        elif (p_src is not None and has_drawing(p_src._p)) or item.get("metadata", {}).get("has_img"):
            clone_pPr = clone_paragraph(p_src._p, state.doc_src, state.doc_out, "BODY_PARAGRAPH").get_or_add_pPr()
            remove_child(clone_pPr, "w:numPr")
            replace_child(clone_pPr, _jc("center"))
            replace_child(clone_pPr, spacing_el(120, 60))
        elif rich and not text:
            print(f"[Agent 3 - Formatter] Zero-Loss: Deep-cloning paragraf kaya #{item.get('para_id', 0)} (rumus/OLE/field)")
            clone_paragraph(p_src._p, state.doc_src, state.doc_out, "BODY_PARAGRAPH")
        elif text and rich:
            clone_pPr = clone_paragraph(p_src._p, state.doc_src, state.doc_out, "BODY_PARAGRAPH").get_or_add_pPr()
            replace_child(clone_pPr, _jc("both"))
            replace_child(clone_pPr, spacing_el(0, 120, 276))
            replace_child(clone_pPr, _ind(left=0, right=0, first_line=720))
        elif text:
            self._render_chapter_body_text(state, text, p_src)
        elif p_src is not None and has_content_besides_ppr(p_src._p):
            clone_paragraph(p_src._p, state.doc_src, state.doc_out, "BODY_PARAGRAPH")

    def _render_frontmatter_body(self, state: _BuildState, text: str, p_src, rich: bool) -> None:
        if rich:
            clone_paragraph(p_src._p, state.doc_src, state.doc_out, "BODY_PARAGRAPH")
        elif text:
            p, pPr = self._new_paragraph(state.doc_out, "BODY_PARAGRAPH")
            pPr.append(_jc("both"))
            if text.lower().startswith(KEYWORD_PREFIXES) and ":" in text:
                pPr.append(spacing_el(120, 120, 276))
                label, keywords = text.split(":", 1)
                style_run(p.add_run(label.strip() + ": "), 12, bold=True, black=False)
                style_run(p.add_run(keywords.strip()), 12, italic=True, black=False)
            else:
                pPr.append(spacing_el(0, 120, 276))
                style_run(p.add_run(text), 12, black=False)
        elif p_src is not None and has_content_besides_ppr(p_src._p):
            clone_paragraph(p_src._p, state.doc_src, state.doc_out, "BODY_PARAGRAPH")

    def _render_chapter_body_text(self, state: _BuildState, text: str, p_src) -> None:
        p, pPr = self._new_paragraph(state.doc_out, "BODY_PARAGRAPH")
        src_pPr = p_src._p.find(qn("w:pPr")) if p_src is not None else None
        src_num_pr = src_pPr.find(qn("w:numPr")) if src_pPr is not None else None

        if src_num_pr is not None:
            pPr.append(num_pr_el(self._list_level(src_num_pr), self._output_list_num_id(state, src_num_pr)))
            pPr.append(_jc("both"))
            pPr.append(spacing_el(0, 60, 276))
            pPr.append(_ind(left=720, hanging=360))
        else:
            p.style = state.doc_out.styles["Normal"]
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pPr.append(_jc("both"))
            pPr.append(spacing_el(0, 120, 276))
            pPr.append(_ind(left=0, right=0, first_line=720))

        style_run(p.add_run(text), 12)
        italicize_foreign_terms(p)

    @staticmethod
    def _list_level(src_num_pr) -> str:
        ilvl = src_num_pr.find(qn("w:ilvl"))
        return ilvl.attrib.get(qn("w:val"), "0") if ilvl is not None else "0"

    @staticmethod
    def _output_list_num_id(state: _BuildState, src_num_pr) -> str:
        """numId output untuk list sumber; list baru dimulai dari 1 di setiap (sub-)bab."""
        src_num_id_el = src_num_pr.find(qn("w:numId"))
        src_num_id = src_num_id_el.attrib.get(qn("w:val"), "0") if src_num_id_el is not None else "0"
        if src_num_id not in state.src_to_out_num_id:
            new_num_id = str(state.next_list_num_id)
            state.next_list_num_id += 1
            add_restarting_list_num(state.numbering, new_num_id)
            state.src_to_out_num_id[src_num_id] = new_num_id
        return state.src_to_out_num_id[src_num_id]

    def _render_caption(self, state: _BuildState, item: Dict[str, Any], _p_src) -> None:
        label = item["approved_label"]
        display_prefix, prefix_re, space_before, space_after = _CAPTION_STYLES[label]
        state.caption_counts[label] += 1
        clean = re.sub(prefix_re, "", item.get("text", "").strip(), flags=re.IGNORECASE).strip()
        title = f" {to_title_case(clean)}" if clean else ""

        p, pPr = self._new_paragraph(state.doc_out, label, "Caption")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pPr.append(_jc("center"))
        pPr.append(spacing_el(space_before, space_after))
        style_run(p.add_run(f"{display_prefix} "), 12, bold=True)
        add_seq_caption_field(p, display_prefix, state.caption_bab, state.caption_counts[label], title)

    def _render_bibliography_item(self, state: _BuildState, item: Dict[str, Any], p_src) -> None:
        text = item.get("text", "").strip()
        has_links = p_src is not None and (p_src._p.findall(".//" + qn("w:hyperlink")) or p_src._p.findall(".//" + qn("w:fldSimple")))
        if has_links:
            clone_pPr = clone_paragraph(p_src._p, state.doc_src, state.doc_out, "DAFTAR_PUSTAKA_ITEM").get_or_add_pPr()
            replace_child(clone_pPr, _ind(left=720, hanging=720))
            replace_child(clone_pPr, spacing_el(0, 120, 276))
        elif text:
            p, pPr = self._new_paragraph(state.doc_out, "DAFTAR_PUSTAKA_ITEM")
            pPr.append(_jc("both"))
            pPr.append(spacing_el(0, 120, 276))
            pPr.append(_ind(left=720, hanging=720))
            style_run(p.add_run(text), 12)

    @staticmethod
    def _render_unknown(state: _BuildState, item: Dict[str, Any], p_src) -> None:
        """Zero-loss: label tak dikenal di-deep-clone apa adanya bila memiliki konten."""
        if p_src is None or not (p_src.text.strip() or has_rich_content(p_src._p)):
            return
        label = item["approved_label"]
        print(f"[Agent 3 - Formatter] Zero-Loss: Label '{label}' tidak dikenali, deep-clone paragraf #{item.get('para_id', 0)} apa adanya.")
        clone_paragraph(p_src._p, state.doc_src, state.doc_out, label)

    # ------------------------------------------------------------------
    # Tabel & elemen body lain (zero-loss)
    # ------------------------------------------------------------------
    @staticmethod
    def _clone_and_format_table(tbl_elem, state: _BuildState, after=None):
        cloned = clone_table(tbl_elem, state.doc_src, state.doc_out, after=after)
        try:
            format_table(Table(cloned, state.doc_out))
        except Exception as exc:  # tabel dengan struktur sel tidak lazim tetap disalin tanpa format
            print(f"[Agent 3 - Formatter] Peringatan: tabel disalin tanpa format ({exc})")
        state.inserted_tables.add(tbl_elem)
        return cloned

    def _insert_tables_after_paragraph(self, state: _BuildState, para_idx: int) -> None:
        tables = state.tables_after_para.get(para_idx)
        if not tables:
            return
        cursor = state.doc_out.paragraphs[-1]._p if state.doc_out.paragraphs else None
        for tbl_elem in tables:
            if tbl_elem not in state.inserted_tables:
                cursor = self._clone_and_format_table(tbl_elem, state, after=cursor)

    def _copy_remaining_tables(self, state: _BuildState) -> None:
        for src_table in state.doc_src.tables:
            if src_table._tbl not in state.inserted_tables:
                self._clone_and_format_table(src_table._tbl, state)

    @staticmethod
    def _copy_other_body_elements(doc_src, doc_out) -> None:
        """Menyalin elemen body selain paragraf/tabel/sectPr (mis. w:sdt) apa adanya."""
        skipped = {qn("w:p"), qn("w:tbl"), qn("w:sectPr")}
        for child in list(doc_src.element.body):
            if child.tag in skipped:
                continue
            clone_body_element(child, doc_src, doc_out)
            print(f"[Agent 3 - Formatter] Zero-Loss: Menyalin elemen body non-standar <{child.tag.split('}')[-1]}>")

    @staticmethod
    def _report_content_audit(doc_src, doc_out) -> None:
        src_tables, out_tables = len(doc_src.tables), len(doc_out.tables)
        print(f"\n[Agent 3 - Content Audit] Sumber: {len(doc_src.paragraphs)} paragraf, {src_tables} tabel")
        print(f"[Agent 3 - Content Audit] Output: {len(doc_out.paragraphs)} paragraf, {out_tables} tabel")
        if out_tables < src_tables:
            print(f"[Agent 3 - Content Audit] PERINGATAN: {src_tables - out_tables} tabel mungkin belum tersalin!")
