"""Penyusunan otomatis Daftar Isi, Daftar Tabel, dan Daftar Gambar beserta estimasi nomor halaman."""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

from src.ooxml.fields import bookmark_pair
from src.ooxml.text import SUBSUB_NUMBER_RE, strip_bab_prefix, strip_subbab_number, to_roman
from src.ooxml.xml import remove_child, style_run, w_el

TOC_LABEL = "TOC_PARAGRAPH"
LINES_PER_PAGE = 26
WORDS_PER_LINE = 12
TOC_RIGHT_TAB_DXA = "7937"  # 14 cm

_ROMAN_PAGE_TITLES = (
    "PENGESAHAN", "PERSETUJUAN", "PUBLIKASI", "PERNYATAAN", "KATA PENGANTAR", "PRAKATA",
    "ABSTRAK", "ABSTRACT", "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR", "DAFTAR SIMBOL",
)
_FORM_FIELD_WORDS = ("NAMA", "NIM", "WAKTU", "TANDA TANGAN", "TANGGAL")
_LIST_BOUNDARY_TITLES = (
    "DAFTAR ISI", "DAFTAR GAMBAR", "DAFTAR TABEL", "BAB 1", "BAB 1 PENDAHULUAN", "BAB I PENDAHULUAN", "PENDAHULUAN",
)
_NATIVE_TOC_MARKERS = ("TABLE OF CONTENTS", "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR")
_CAPTION_KINDS = {
    "CAPTION_GAMBAR": ("Gambar", "Gambar|Figure"),
    "CAPTION_TABEL": ("Tabel", "Tabel|Table"),
}

# (judul, nomor halaman, nama bookmark, level indentasi)
TocEntry = Tuple[str, str, str, int]
TOC_BOOKMARK_ID_BASE = 800000


@dataclass
class _TocCollector:
    """Mengumpulkan entri daftar sambil mengestimasi nomor halaman dan memasang bookmark."""

    bookmark_counter: int = 100
    fm_page_count: int = 0
    body_page: int = 1
    accum_lines: int = 0
    current_bab: int = 0
    current_sub: int = 0
    current_subsub: int = 0
    caption_counts: dict = field(default_factory=lambda: {"CAPTION_GAMBAR": 0, "CAPTION_TABEL": 0})
    in_body: bool = False
    body_ended: bool = False
    toc_entries: List[TocEntry] = field(default_factory=list)
    caption_entries: dict = field(default_factory=lambda: {"CAPTION_GAMBAR": [], "CAPTION_TABEL": []})
    seen_captions: set = field(default_factory=set)

    def next_bookmark_name(self) -> str:
        name = f"_Toc{self.bookmark_counter}"
        self.bookmark_counter += 1
        return name

    def _bookmark(self, p) -> str:
        """bookmarkStart disisipkan setelah w:pPr: w:pPr wajib menjadi anak pertama w:p."""
        name = self.next_bookmark_name()
        # id di rentang terpisah: id kecil sudah dipakai bookmark naskah sumber yang ikut tersalin
        # (cross-reference _Ref), dan id ganda membuat Word membuang salah satu bookmark.
        start, end = bookmark_pair(TOC_BOOKMARK_ID_BASE + self.bookmark_counter, name)
        pPr = p._p.find(qn("w:pPr"))
        if pPr is not None:
            pPr.addnext(start)
        else:
            p._p.insert(0, start)
        p._p.append(end)
        return name

    def _add_lines(self, lines: int) -> None:
        self.accum_lines += lines
        while self.accum_lines >= LINES_PER_PAGE:
            self.body_page += 1
            self.accum_lines -= LINES_PER_PAGE

    def visit(self, p) -> None:
        label = p._p.get("approved_label")
        text = p.text.strip()
        if not text:
            return
        if label == "FRONTMATTER_TITLE" and not self.in_body and not self.body_ended:
            self._frontmatter_title(p, text)
        elif label == "JUDUL_BAB":
            self._chapter(p, text)
        elif label == "SUB_BAB" and self.in_body:
            self._subchapter(p, text)
        elif label == "FRONTMATTER_TITLE" and self.in_body:
            self._backmatter_title(p, text)
        elif label in _CAPTION_KINDS:
            self._caption(p, text, label)
        elif self.in_body and label == "BODY_PARAGRAPH":
            self._add_lines(max(1, (len(text.split()) + WORDS_PER_LINE - 1) // WORDS_PER_LINE) + 1)

    def _frontmatter_title(self, p, text: str) -> None:
        upper = text.upper()
        if not any(k in upper for k in _ROMAN_PAGE_TITLES) or any(k in upper for k in _FORM_FIELD_WORDS):
            return
        title = re.sub(r"^\d+(\.\d+)*\s*", "", strip_bab_prefix(text)).strip()
        if not title or title.upper() == "UNTUK KEPENTINGAN AKADEMIS":
            return
        self.fm_page_count += 1
        page = to_roman(self.fm_page_count).lower()
        self.toc_entries.append((title.split("\n")[0].strip().upper(), page, self._bookmark(p), 0))

    def _chapter(self, p, text: str) -> None:
        self.in_body = True
        self.current_bab += 1
        self.current_sub = self.current_subsub = 0
        self.caption_counts = {kind: 0 for kind in self.caption_counts}
        self.body_page = 1 if self.current_bab == 1 else self.body_page + 1
        self.accum_lines = 0
        title = f"BAB {to_roman(self.current_bab)} {strip_bab_prefix(text).upper()}"
        self.toc_entries.append((title, str(self.body_page), self._bookmark(p), 0))
        self.accum_lines += 3

    def _subchapter(self, p, text: str) -> None:
        is_subsub = bool(
            p._p.get("is_subsub") == "true" or SUBSUB_NUMBER_RE.match(text) or p.style.name in ("Heading 3", "Heading3")
        )
        clean = strip_subbab_number(text)
        if is_subsub:
            self.current_subsub += 1
            title = f"{self.current_bab}.{self.current_sub or 1}.{self.current_subsub} {clean}"
            level = 2
        else:
            self.current_sub += 1
            self.current_subsub = 0
            title = f"{self.current_bab}.{self.current_sub} {clean}"
            level = 1
        self.toc_entries.append((title, str(self.body_page), self._bookmark(p), level))
        self.accum_lines += 2
        if self.accum_lines >= LINES_PER_PAGE:
            self.body_page += 1
            self.accum_lines = 0

    def _backmatter_title(self, p, text: str) -> None:
        self.body_ended = True
        self.body_page += 1
        self.accum_lines = 0
        title = strip_bab_prefix(text).upper()
        self.toc_entries.append((title, str(self.body_page), self._bookmark(p), 0))

    def _caption(self, p, text: str, label: str) -> None:
        display_prefix, prefix_re = _CAPTION_KINDS[label]
        self.caption_counts[label] += 1
        clean = re.sub(rf"^({prefix_re})\s*([\d\.\-]+\s*[:\.]?|\.\s*[:\.]?|[:\.]\s*)", "", text, flags=re.IGNORECASE).strip()
        if not clean or clean == text.strip():
            clean = re.sub(rf"^({prefix_re})\s*(\.\s*)?", "", text, flags=re.IGNORECASE).strip()
        clean = re.sub(r"^\.\s*", "", clean).strip()
        clean = re.sub(r"\t\d+$", "", clean).strip()
        title = f"{display_prefix} {self.current_bab or 1}.{self.caption_counts[label]} {clean}"
        if title in self.seen_captions or len(clean.split()) > 25:
            return
        self.seen_captions.add(title)
        page = str(self.body_page if self.in_body else 1)
        self.caption_entries[label].append((title, page, self._bookmark(p), 0))


# (label SEQ caption Agent 3, petunjuk nama style/label caption pada instruksi TOC naskah sumber)
_CAPTION_LIST_TARGETS = (("Tabel", ("TBL", "TABEL", "TABLE")), ("Gambar", ("FIG", "GAMBAR", "FIGURE")))


def _caption_list_instruction(instruction: str):
    """Instruksi pengganti untuk Daftar Tabel/Gambar bawaan, atau None bila bukan daftar caption."""
    upper = instruction.upper()
    if not upper.strip().startswith("TOC") or "\\O" in upper or ("\\T" not in upper and "\\C" not in upper):
        return None
    for seq_label, hints in _CAPTION_LIST_TARGETS:
        if any(hint in upper for hint in hints):
            return f' TOC \\h \\z \\c "{seq_label}" '
    return None


def retarget_caption_list_fields(element) -> int:
    """Mengarahkan Daftar Tabel/Gambar bawaan naskah (mis. TOC \\t "TblCaption,1") ke caption
    SEQ Tabel/Gambar buatan Agent 3, agar daftar terisi saat field diperbarui di Word."""
    changed = 0
    for instr in element.iter(qn("w:instrText")):
        replacement = _caption_list_instruction(instr.text or "")
        if replacement:
            instr.text = replacement
            changed += 1
    for fld in element.iter(qn("w:fldSimple")):
        replacement = _caption_list_instruction(fld.get(qn("w:instr"), ""))
        if replacement:
            fld.set(qn("w:instr"), replacement)
            changed += 1
    return changed


# Elemen settings.xml yang menurut skema berada SETELAH w:updateFields.
_SETTINGS_AFTER_UPDATE_FIELDS = (
    "hdrShapeDefaults", "footnotePr", "endnotePr", "compat", "docVars", "rsids", "mathPr", "attachedSchema",
    "themeFontLang", "clrSchemeMapping", "doNotIncludeSubdocsInStats", "doNotAutoCompressPictures",
    "forceUpgrade", "captions", "readModeInkLockDown", "smartTagType", "schemaLibrary", "shapeDefaults",
    "doNotEmbedSmartTags", "decimalSymbol", "listSeparator",
)


def _enable_update_fields(doc) -> None:
    """Word menawarkan pembaruan field saat dokumen dibuka; disisipkan pada posisi sesuai skema."""
    settings = doc.settings.element
    if settings.find(qn("w:updateFields")) is not None:
        return
    element = w_el("updateFields", {"val": "true"})
    after = {qn(f"w:{name}") for name in _SETTINGS_AFTER_UPDATE_FIELDS}
    anchor = next((child for child in settings if child.tag in after), None)
    if anchor is None:
        settings.append(element)
    else:
        anchor.addprevious(element)


def _is_native_heading_toc(sdt) -> bool:
    """Blok Daftar Isi bawaan Word: galeri 'Table of Contents', field TOC \\o, atau judulnya di dalam blok."""
    gallery = sdt.find(f"{qn('w:sdtPr')}/{qn('w:docPartObj')}/{qn('w:docPartGallery')}")
    if gallery is not None and gallery.get(qn("w:val")) == "Table of Contents":
        return True
    for instr in sdt.iter(qn("w:instrText")):
        upper = (instr.text or "").strip().upper()
        if upper.startswith("TOC") and "\\O" in upper:
            return True
    sdt_text = "".join(sdt.itertext()).upper()
    return any(k in sdt_text for k in _NATIVE_TOC_MARKERS)


def _find_native_toc(doc):
    return next((sdt for sdt in doc._body._element.xpath(".//w:sdt") if _is_native_heading_toc(sdt)), None)


def _find_first_chapter(doc) -> Optional[Paragraph]:
    for p in doc.paragraphs:
        label = p._p.get("approved_label")
        if label == TOC_LABEL:
            continue
        if label == "JUDUL_BAB" or p.text.strip().upper().startswith(("BAB 1", "BAB I", "PENDAHULUAN")):
            return p
    return None


def _find_list_title(doc, title: str) -> Optional[Paragraph]:
    for p in doc.paragraphs:
        if p._p.get("approved_label") != TOC_LABEL and p.text.strip().upper() == title:
            return p
    return None


def _add_toc_item(doc, before_p, entry: TocEntry) -> Paragraph:
    """Menyisipkan satu baris daftar (teks + tab leader titik + nomor halaman) sebelum `before_p`."""
    text, page, _bookmark_name, indent_level = entry
    p = before_p.insert_paragraph_before()
    p._p.set("approved_label", TOC_LABEL)
    p.style = doc.styles["Normal"]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fmt = p.paragraph_format
    fmt.line_spacing = 1.15
    fmt.space_before = Pt(2)
    fmt.space_after = Pt(2)
    fmt.left_indent = Cm(0.5 * indent_level)
    fmt.right_indent = Cm(0)
    fmt.first_line_indent = Cm(0)

    pPr = p._p.get_or_add_pPr()
    remove_child(pPr, "w:numPr")
    remove_child(pPr, "w:outlineLvl")
    pPr.append(w_el("tabs", inner=f'<w:tab w:val="right" w:leader="dot" w:pos="{TOC_RIGHT_TAB_DXA}"/>'))

    style_run(p.add_run(text), 12, bold=False)
    p.add_run("\t")
    style_run(p.add_run(page), 12, bold=False)
    return p


# Instruksi field per daftar. Entri estimasi menjadi hasil tersimpan (cached result) field,
# sehingga daftar langsung tampil dan menjadi tepat begitu Word memperbarui field.
_LIST_FIELD_INSTRUCTIONS = {
    "DAFTAR ISI": ' TOC \\o "1-3" \\h \\z \\u ',
    "DAFTAR TABEL": ' TOC \\h \\z \\c "Tabel" ',
    "DAFTAR GAMBAR": ' TOC \\h \\z \\c "Gambar" ',
}


def _wrap_in_toc_field(paragraphs: List[Paragraph], instruction: str) -> None:
    """Membungkus paragraf entri dengan satu complex field TOC (begin di entri pertama, end di
    entri terakhir) agar daftar dapat diperbarui Word (F9 / Update Field)."""
    first, last = paragraphs[0]._p, paragraphs[-1]._p
    begin = [
        w_el("r", inner='<w:fldChar w:fldCharType="begin"/>'),
        w_el("r", inner=f'<w:instrText xml:space="preserve">{instruction}</w:instrText>'),
        w_el("r", inner='<w:fldChar w:fldCharType="separate"/>'),
    ]
    anchor = first.find(qn("w:pPr"))
    for run in begin:
        if anchor is None:
            first.insert(0, run)
        else:
            anchor.addnext(run)
        anchor = run
    last.append(w_el("r", inner='<w:fldChar w:fldCharType="end"/>'))


def _create_list_title(anchor_p, title: str) -> Paragraph:
    p = anchor_p.insert_paragraph_before()
    p._p.set("approved_label", "FRONTMATTER_TITLE")
    style_run(p.add_run(title), 14, bold=True)
    return p


def _style_list_title(doc, p, page_break: bool) -> None:
    """Heading 1 rata tengah mutlak (tanpa indentasi/penomoran) agar tampil di Navigation Pane."""
    p.style = doc.styles["Heading 1"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt = p.paragraph_format
    fmt.line_spacing = 1.0
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(12)
    fmt.page_break_before = page_break
    fmt.keep_with_next = True

    pPr = p._p.get_or_add_pPr()
    remove_child(pPr, "w:outlineLvl")
    pPr.append(w_el("outlineLvl", {"val": "0"}))
    remove_child(pPr, "w:jc")
    pPr.append(w_el("jc", {"val": "center"}))
    remove_child(pPr, "w:numPr")
    remove_child(pPr, "w:ind")
    pPr.append(w_el("ind", {"left": "0", "right": "0", "firstLine": "0"}))
    if not page_break:
        remove_child(pPr, "w:pageBreakBefore")
    elif pPr.find(qn("w:pageBreakBefore")) is None:
        pPr.append(w_el("pageBreakBefore"))
    if pPr.find(qn("w:keepNext")) is None:
        pPr.append(w_el("keepNext"))


def _clear_old_list_body(title_p) -> Optional[Paragraph]:
    """Menghapus isi daftar manual lama di bawah judul; mengembalikan heading pembatas berikutnya."""
    parent = title_p._p.getparent()
    siblings = list(parent.iterchildren(qn("w:p")))
    for elem in siblings[siblings.index(title_p._p) + 1:]:
        candidate = Paragraph(elem, title_p._parent)
        is_boundary = candidate._p.get("approved_label") != TOC_LABEL and (
            candidate.style.name in ("Heading 1", "Heading1")
            or candidate._p.get("approved_label") == "JUDUL_BAB"
            or candidate.text.strip().upper() in _LIST_BOUNDARY_TITLES
        )
        if is_boundary:
            return candidate
        if _is_old_list_entry(candidate):
            parent.remove(elem)  # teks lain (mis. petunjuk template) dipertahankan: tidak menghapus isi diam-diam
    return None


_PAGE_NUMBER_TAIL_RE = re.compile(r"(\t|[.…]{3,})\s*(\d{1,3}|[ivxlc]{1,6})\s*$", re.IGNORECASE)


def _is_old_list_entry(p: Paragraph) -> bool:
    """Baris daftar lama: kosong, bergaya TOC/Table of Figures, berisi field (PAGEREF/TOC), atau diakhiri tab+nomor halaman."""
    text = p.text
    if not text.strip() or p._p.get("approved_label") == TOC_LABEL:
        return True
    style = (p.style.name or "").lower() if p.style is not None else ""
    if style.startswith("toc") or style == "table of figures":
        return True
    if any(True for _ in p._p.iter(qn("w:instrText"))) or any(True for _ in p._p.iter(qn("w:fldSimple"))):
        return True
    return bool(_PAGE_NUMBER_TAIL_RE.search(text))


def _missing_list_entries(collector: _TocCollector) -> List[TocEntry]:
    """Entri DAFTAR ISI/TABEL/GAMBAR yang belum tercantum di Daftar Isi (halaman Romawi)."""
    existing = {entry[0] for entry in collector.toc_entries}
    candidates = [
        ("DAFTAR ISI", True),
        ("DAFTAR TABEL", bool(collector.caption_entries["CAPTION_TABEL"])),
        ("DAFTAR GAMBAR", bool(collector.caption_entries["CAPTION_GAMBAR"])),
    ]
    extra = []
    for title, needed in candidates:
        if needed and title not in existing:
            collector.fm_page_count += 1
            extra.append((title, to_roman(collector.fm_page_count).lower(), collector.next_bookmark_name(), 0))
    return extra


def generate_table_of_contents(doc, has_frontmatter: bool = True) -> None:
    """Membangun Daftar Isi/Tabel/Gambar; Daftar Isi native naskah (w:sdt) diganti Daftar Isi baru."""
    print("[Agent 3 - Formatter Actuator] Menyusun otomatis Daftar Isi, Daftar Tabel, dan Daftar Gambar dengan penomoran dinamis...")
    native = _find_native_toc(doc)
    if native is not None:
        # Daftar Isi bawaan naskah berisi struktur & penomoran lama (mis. 2.2.2.2, "BAB 1 ... PENDAHULUAN")
        # sehingga diganti Daftar Isi baru dari judul hasil format; isinya memang dibangun ulang (tidak ada
        # teks naskah yang hilang). Judul "DAFTAR ISI" dibuat di posisi blok lama bila ikut terhapus.
        print("[Agent 3 - Formatter Actuator] Daftar Isi bawaan naskah (w:sdt) diganti Daftar Isi baru.")
        if _find_list_title(doc, "DAFTAR ISI") is None:
            title = w_el("p")
            title.set("approved_label", "FRONTMATTER_TITLE")
            native.addprevious(title)
            style_run(Paragraph(title, doc._body).add_run("DAFTAR ISI"), 14, bold=True)
        native.getparent().remove(native)
    collector = _TocCollector()
    for p in doc.paragraphs:
        collector.visit(p)

    has_native_toc = False

    anchor_bab_p = _find_first_chapter(doc)
    toc_entries = collector.toc_entries
    first_bab_idx = next((i for i, e in enumerate(toc_entries) if e[0].startswith("BAB ")), len(toc_entries))
    toc_entries[first_bab_idx:first_bab_idx] = _missing_list_entries(collector)

    # Daftar Isi native dipertahankan; Daftar Tabel/Gambar manual di luar blok native tetap dibangun
    # ulang, karena baris lamanya merujuk bookmark caption sumber yang tidak ada lagi ("Error! Bookmark").
    targets = [] if has_native_toc else [("DAFTAR ISI", toc_entries)]
    for title, label in (("DAFTAR TABEL", "CAPTION_TABEL"), ("DAFTAR GAMBAR", "CAPTION_GAMBAR")):
        if collector.caption_entries[label]:
            targets.append((title, collector.caption_entries[label]))

    for title, entries in targets:
        title_p = _find_list_title(doc, title)
        was_created = title_p is None
        if was_created:
            if not entries or anchor_bab_p is None or has_native_toc:
                continue
            title_p = _create_list_title(anchor_bab_p, title)

        _style_list_title(doc, title_p, page_break=has_frontmatter or title != "DAFTAR ISI")

        insert_before = anchor_bab_p if was_created else _clear_old_list_body(title_p)
        if insert_before is not None and entries:
            items = [_add_toc_item(doc, insert_before, entry) for entry in entries]
            _wrap_in_toc_field(items, _LIST_FIELD_INSTRUCTIONS[title])

    # Nomor halaman entri adalah estimasi; updateFields membuat Word menawarkan pembaruan saat
    # dokumen dibuka sehingga Daftar Isi/Tabel/Gambar memakai nomor halaman sebenarnya.
    _enable_update_fields(doc)
