"""
Generator 7 Master Datasets Skripsi (The 7-Pillar Architecture)
Sesuai Standar SK Rektor Universitas Esa Unggul (UEU) No. 5 Tahun 2018.

Dataset yang Dihasilkan:
1. data/datasets/dataset_1_cover_frontmatter.csv : Metadata Cover & Lembar Pengesahan, Abstrak
2. data/datasets/dataset_2_zoning.csv            : Segmentasi Zona Dokumen & Transisi Seksi
3. data/datasets/dataset_3_headings_vs_lists.csv: Heading 1, 2, 3 vs Rincian Poin (1., a., bullet)
4. data/datasets/dataset_4_figures.csv          : Gambar, Caption Bawah, dan Sumber Gambar
5. data/datasets/dataset_5_tables.csv           : Tabel, Caption Atas, Header, dan Sumber Tabel
6. data/datasets/dataset_6_code_formulas.csv    : Rumus Matematika, Persamaan, & Kode Program
7. data/datasets/dataset_7_body_bibliography.csv: Paragraf Isi, Kutipan Langsung, & Daftar Pustaka
"""

import csv
import os
import re
from itertools import pairwise
from typing import Any, Dict, List, Optional

from docx import Document

from src.paragraph_features import extract_paragraph_features, get_font_name

# Pola Regex Baku UEU 2018
BAB_PATTERN = re.compile(r'^(BAB\s+[IVX\d]+|BAB\s+\d+)(\s*[:\-\n\r]\s*|\s+|$)', re.IGNORECASE)
HEADING2_PATTERN = re.compile(r'^\d+\.\d+(\s+[A-Za-z].*|$)', re.IGNORECASE)
HEADING3_PATTERN = re.compile(r'^\d+\.\d+\.\d+(\s+[A-Za-z].*|$)', re.IGNORECASE)

LIST_NUMBER_PATTERN = re.compile(r'^\d+[\.\)]\s+', re.IGNORECASE)
LIST_ALPHA_PATTERN = re.compile(r'^[a-zA-Z][\.\)]\s+', re.IGNORECASE)
LIST_BULLET_PATTERN = re.compile(r'^[\-\•\*\–\⁃]\s+', re.IGNORECASE)

CAPTION_GAMBAR_PATTERN = re.compile(r'^(Gambar|Figure)\s+(\d+[\.\-]\d+|\.|\d+).*', re.IGNORECASE)
CAPTION_TABEL_PATTERN = re.compile(r'^(Tabel|Table)\s+(\d+[\.\-]\d+|\.|\d+).*', re.IGNORECASE)
SOURCE_PATTERN = re.compile(r'^\(?(Sumber|Source)\s*[:\-].*', re.IGNORECASE)
EQUATION_NUM_PATTERN = re.compile(r'.*\(\d+[\.\-]\d+\)\s*$', re.IGNORECASE)
NIM_PATTERN = re.compile(r'\b\d{9,12}\b')
COVER_YEAR_PATTERN = re.compile(r'^(20\d\d|JAKARTA.*20\d\d)$')

CANONICAL_CHAPTER_NAMES = [
    "PENDAHULUAN", "TINJAUAN PUSTAKA", "LANDASAN TEORI", "DASAR TEORI",
    "KAJIAN PUSTAKA", "METODE", "METODOLOGI", "METODE PENELITIAN",
    "METODOLOGI PENELITIAN", "GAMBARAN UMUM", "ANALISIS DAN PEMBAHASAN",
    "HASIL DAN PEMBAHASAN", "PEMBAHASAN", "IMPLEMENTASI",
    "KESIMPULAN DAN SARAN", "PENUTUP", "KESIMPULAN"
]
FRONTMATTER_ZONE_TRIGGERS = ("LEMBAR PENGESAHAN", "HALAMAN PENGESAHAN", "PERNYATAAN KEASLIAN", "KATA PENGANTAR")
FRONTMATTER_LIST_TITLES = ("DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR")
BIBLIOGRAPHY_TITLES = ("DAFTAR PUSTAKA", "DAFTAR REFERENSI")
FRONT_ZONES = ("COVER", "FRONTMATTER", "FRONTMATTER_LISTS")
MATH_SYMBOLS = ("∑", "√", "∫", "≈", "≤", "≥", "λ", "μ")
MAX_CAPTION_WORDS = 25

MONOSPACE_FONTS = {"consolas", "courier", "courier new", "lucida console", "monaco", "source code pro"}
CODE_KEYWORDS = {"def ", "select ", "from ", "where ", "public class ", "function(", "import ", "return ", "if (", "while ("}

OUT_DIR = "data/datasets"
GOLDEN_DOCUMENTS = [
    # HANYA MENGGUNAKAN 4 DOKUMEN GOLDEN DATASET BERSIH BUATAN USER: (path, doc_id, nama CSV modular)
    ("Dataset Asdoku/Dataset Asdoku 1.docx", "ASDOKU_1_TEMPLATE_UTUH", "dataset_asdoku_1_template_keseluruhan.csv"),
    ("Dataset Asdoku/Dataset Asdoku 2.docx", "ASDOKU_2_TOC_HEADINGS", "dataset_asdoku_2_headings_toc.csv"),
    ("Dataset Asdoku/Dataset Asdoku 3.docx", "ASDOKU_3_FIGURES_TOF", "dataset_asdoku_3_figures.csv"),
    ("Dataset Asdoku/Dataset Asdoku 4.docx", "ASDOKU_4_TABLES_TOT", "dataset_asdoku_4_tables.csv"),
]

# Kolom per dataset spesialis (urutan = urutan kolom CSV; 'label' selalu terakhir)
ZONING_COLUMNS = ("doc_id", "para_id", "text", "doc_pos", "is_bold", "has_pgbrk", "style")
COVER_COLUMNS = ("doc_id", "para_id", "text", "font_size", "is_bold", "align", "doc_pos")
FIGURE_COLUMNS = ("doc_id", "para_id", "text", "is_below_drawing", "align", "font_size")
TABLE_COLUMNS = ("doc_id", "para_id", "text", "is_above_table", "align", "font_size")
FORMULA_COLUMNS = ("doc_id", "para_id", "text", "is_monospace", "font_name", "font_size", "has_math")
HEADING_COLUMNS = ("doc_id", "para_id", "text", "font_size", "is_bold", "has_num", "word_count", "uppercase_ratio")
BODY_COLUMNS = ("doc_id", "para_id", "text", "first_line_indent", "left_indent", "line_spacing", "word_count")

DATASET_FILES = {
    "cover_frontmatter": "dataset_1_cover_frontmatter.csv",
    "zoning": "dataset_2_zoning.csv",
    "headings_vs_lists": "dataset_3_headings_vs_lists.csv",
    "figures": "dataset_4_figures.csv",
    "tables": "dataset_5_tables.csv",
    "code_formulas": "dataset_6_code_formulas.csv",
    "body_bibliography": "dataset_7_body_bibliography.csv",
}


def _tag(elem) -> str:
    return elem.tag.split('}')[-1]


def _paragraph_item(p, doc_id: str, elem_idx: int, para_id: int, total_elements: int,
                    is_above_table: bool, is_below_table: bool) -> Dict[str, Any]:
    f = extract_paragraph_features(p, elem_idx, total_elements)
    font_name = get_font_name(p)
    return {
        "elem_type": "paragraph",
        "doc_id": doc_id,
        "elem_idx": elem_idx,
        "para_id": para_id,
        "text": f["text"],
        "style": f["style"],
        "font_name": font_name,
        "font_size": f["font_size"],
        "is_bold": f["is_bold"],
        "is_italic": f["is_italic"],
        "align": f["align"],
        "has_num": f["has_num"],
        "has_img": f["has_img"],
        "has_pgbrk": f["has_pgbrk"],
        "has_math": "oMath" in p._p.xml,
        "is_above_table": is_above_table,
        "is_below_table": is_below_table,
        "is_below_drawing": False,  # dihitung di second-pass
        "space_before": f["space_before"],
        "space_after": f["space_after"],
        "line_spacing": f["line_spacing"],
        "first_line_indent": f["first_line_indent"],
        "left_indent": f["left_indent"],
        "char_len": f["char_len"],
        "word_count": f["word_count"],
        "uppercase_ratio": f["uppercase_ratio"],
        "is_monospace": font_name.lower() in MONOSPACE_FONTS,
        "has_code_keywords": any(kw in f["text"].lower() for kw in CODE_KEYWORDS),
        "doc_pos": f["doc_pos"],
    }


def _table_item(doc_id: str, elem_idx: int, total_elements: int) -> Dict[str, Any]:
    return {
        "elem_type": "table", "doc_id": doc_id, "elem_idx": elem_idx, "para_id": -1,
        "text": "[TABLE_CONTAINER]", "style": "Table", "font_name": "Times New Roman", "font_size": 10.0,
        "is_bold": False, "is_italic": False, "align": "CENTER",
        "has_num": False, "has_img": False, "has_pgbrk": False, "has_math": False,
        "is_above_table": False, "is_below_table": False, "is_below_drawing": False,
        "space_before": 0.0, "space_after": 0.0, "line_spacing": 1.0, "first_line_indent": 0.0, "left_indent": 0.0,
        "char_len": 0, "word_count": 0, "uppercase_ratio": 0.0, "is_monospace": False, "has_code_keywords": False,
        "doc_pos": round(elem_idx / float(total_elements), 4),
    }


def extract_document_elements(file_path: str, doc_id: str) -> List[Dict[str, Any]]:
    """
    Ekstraksi mendalam setiap elemen dokumen (w:p dan w:tbl)
    dengan penanda relasi spasial OpenXML (atas/bawah gambar & tabel).
    """
    doc = Document(file_path)
    body_elements = doc._body._element
    tags = [_tag(elem) for elem in body_elements]
    total = len(tags)
    paragraphs = iter(doc.paragraphs)  # urutan doc.paragraphs = urutan w:p di body

    items = []
    para_id = 0
    for idx, tag in enumerate(tags):
        if tag == "p":
            p = next(paragraphs)
            is_above_table = idx + 1 < total and tags[idx + 1] == "tbl"
            is_below_table = idx > 0 and tags[idx - 1] == "tbl"
            items.append(_paragraph_item(p, doc_id, idx, para_id, total, is_above_table, is_below_table))
            para_id += 1
        elif tag == "tbl":
            items.append(_table_item(doc_id, idx, total))

    # Second pass: paragraf tepat setelah elemen bergambar
    for prev, item in pairwise(items):
        if prev["has_img"] and item["elem_type"] == "paragraph":
            item["is_below_drawing"] = True
    return items


def _row(item: Dict[str, Any], columns, label: str, label_key: str = "label", **overrides) -> Dict[str, Any]:
    row = {col: overrides.get(col, item[col]) for col in columns}
    row[label_key] = label
    return row


def _next_zone(zone: str, text: str, upper: str, style_lower: str, is_bold: bool, in_sistematika: bool) -> str:
    if any(kw in upper for kw in FRONTMATTER_ZONE_TRIGGERS):
        return "FRONTMATTER"
    if upper in FRONTMATTER_LIST_TITLES:
        return "FRONTMATTER_LISTS"
    if (BAB_PATTERN.match(text) and is_bold) or ("heading 1" in style_lower and upper in CANONICAL_CHAPTER_NAMES):
        return zone if in_sistematika else "BODY_BAB"
    if upper in BIBLIOGRAPHY_TITLES:
        return "BIBLIOGRAPHY"
    if upper.startswith("LAMPIRAN") and (is_bold or "heading" in style_lower):
        return "APPENDIX"
    return zone


def _cover_label(item: Dict[str, Any], zone: str, upper: str, is_toc: bool) -> str:
    text = item["text"]
    if zone == "COVER" and item["doc_pos"] < 0.15:
        if item["word_count"] <= 15 and item["is_bold"] and upper == text and item["font_size"] >= 14:
            return "COVER_TITLE"
        if "SKRIPSI" in upper or "TUGAS AKHIR" in upper or "LAPORAN" in upper:
            return "COVER_TYPE"
        if any(k in upper for k in ("NIM", "NPM")) or NIM_PATTERN.search(text):
            return "COVER_AUTHOR_NIM"
        if any(k in upper for k in ("UNIVERSITAS", "FAKULTAS", "PROGRAM STUDI", "JURUSAN")):
            return "COVER_INSTITUTION"
        if COVER_YEAR_PATTERN.match(upper):
            return "COVER_YEAR"
        return "OTHER_FRONTMATTER"
    if any(k in upper for k in ("PEMBIMBING", "PENGUJI", "DEKAN", "KETUA PROGRAM STUDI", "TANDA TANGAN")):
        return "PENGESAHAN_METADATA"
    if upper in ("ABSTRAK", "ABSTRACT"):
        return "ABSTRAK_TITLE"
    if upper.startswith("KATA KUNCI") or upper.startswith("KEYWORDS"):
        return "ABSTRAK_KEYWORDS"
    if is_toc:
        return "TOC_ENTRY"
    return "OTHER_FRONTMATTER"


def _figure_table_rows(item: Dict[str, Any], prev_item: Optional[Dict[str, Any]]):
    """Baris dataset gambar/tabel untuk satu paragraf: ([(nama dataset, baris)], berhenti?).

    'berhenti' = True berarti paragraf tidak diproses lagi oleh dataset rumus, heading & body.
    """
    text, word_count = item["text"], item["word_count"]
    is_source = SOURCE_PATTERN.match(text)
    rows = []

    if CAPTION_GAMBAR_PATTERN.match(text) and word_count <= MAX_CAPTION_WORDS:
        return [("figures", _row(item, FIGURE_COLUMNS, "CAPTION_GAMBAR"))], True
    if item["has_img"]:
        # Gambar tetap lanjut diperiksa oleh pilar berikutnya
        rows.append(("figures", _row(item, FIGURE_COLUMNS, "FIGURE_IMAGE", text="[IMAGE_DRAWING]", is_below_drawing=False)))
    elif is_source and (item["is_below_drawing"] or (prev_item is not None and CAPTION_GAMBAR_PATTERN.match(prev_item["text"]))):
        return [("figures", _row(item, FIGURE_COLUMNS, "FIGURE_SOURCE", is_below_drawing=True))], True

    if CAPTION_TABEL_PATTERN.match(text) and word_count <= MAX_CAPTION_WORDS:
        return rows + [("tables", _row(item, TABLE_COLUMNS, "CAPTION_TABEL"))], True
    if is_source and item["is_below_table"]:
        return rows + [("tables", _row(item, TABLE_COLUMNS, "TABLE_SOURCE", is_above_table=False))], True
    return rows, False


def _formula_row(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    text = item["text"]
    if item["has_math"] or EQUATION_NUM_PATTERN.match(text) or (any(s in text for s in MATH_SYMBOLS) and item["word_count"] <= 15):
        return _row(item, FORMULA_COLUMNS, "EQUATION_FORMULA")
    if item["is_monospace"] or (item["has_code_keywords"] and ("{" in text or ";" in text or "=" in text)):
        return _row(item, FORMULA_COLUMNS, "CODE_SNIPPET", is_monospace=True, has_math=False)
    return None


def _heading_flags(item: Dict[str, Any], upper: str, style_lower: str):
    text, is_bold, word_count = item["text"], item["is_bold"], item["word_count"]
    no_period = not text.endswith(".")
    is_h1 = bool((BAB_PATTERN.match(text) and is_bold and word_count <= 10) or ("heading 1" in style_lower and upper in CANONICAL_CHAPTER_NAMES))
    is_h2 = bool(HEADING2_PATTERN.match(text) and (is_bold or "heading 2" in style_lower) and word_count <= 15 and no_period)
    is_h3 = bool(HEADING3_PATTERN.match(text) and (is_bold or "heading 3" in style_lower) and word_count <= 15 and no_period)
    return is_h1, is_h2, is_h3


def _heading_or_list_label(item: Dict[str, Any], is_h1: bool, is_h2: bool, is_h3: bool) -> Optional[str]:
    text = item["text"]
    if is_h1:
        return "HEADING_1"
    if is_h2:
        return "HEADING_2"
    if is_h3:
        return "HEADING_3"
    if LIST_NUMBER_PATTERN.match(text):
        return "LIST_NUMBERED"
    if LIST_ALPHA_PATTERN.match(text):
        return "LIST_ALPHABET"
    if LIST_BULLET_PATTERN.match(text) or item["has_num"]:
        return "LIST_BULLET"
    return None


def _body_label(item: Dict[str, Any], zone: str, upper: str, is_heading: bool) -> Optional[str]:
    if zone == "BIBLIOGRAPHY":
        return "BIBLIOGRAPHY_TITLE" if upper in BIBLIOGRAPHY_TITLES else "BIBLIOGRAPHY_ENTRY"
    if zone == "BODY_BAB" and not is_heading:
        # Kutipan langsung panjang (indent kiri besar & teks panjang)
        return "BLOCK_QUOTE" if item["left_indent"] >= 0.8 and item["char_len"] > 100 else "BODY_PARAGRAPH"
    return None


def classify_documents(all_docs_items: List[List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Mengklasifikasikan item ke dalam 7 Dataset Master Spesialis secara ketat."""
    datasets = {name: [] for name in DATASET_FILES}

    for doc_items in all_docs_items:
        zone = "COVER"
        in_sistematika = False

        for i, item in enumerate(doc_items):
            if item["elem_type"] == "table":
                datasets["tables"].append({**item, "label": "TABLE_CONTAINER"})
                continue
            if item["char_len"] == 0:
                continue

            text = item["text"]
            upper = text.upper()
            style_lower = item["style"].lower()
            is_bold = item["is_bold"]
            is_toc = "toc" in style_lower or "table of figures" in style_lower

            if not is_toc:
                zone = _next_zone(zone, text, upper, style_lower, is_bold, in_sistematika)
            datasets["zoning"].append(_row(item, ZONING_COLUMNS, zone, label_key="zone_label", text=text[:100]))

            # Sistematika Penulisan Shield
            if "SISTEMATIKA PENULISAN" in upper:
                in_sistematika = True
            elif in_sistematika and (BAB_PATTERN.match(text) or upper in CANONICAL_CHAPTER_NAMES) and is_bold:
                in_sistematika = False

            if zone in FRONT_ZONES:
                datasets["cover_frontmatter"].append(_row(item, COVER_COLUMNS, _cover_label(item, zone, upper, is_toc)))

            visual_rows, stop = _figure_table_rows(item, doc_items[i - 1] if i > 0 else None)
            for name, row in visual_rows:
                datasets[name].append(row)
            if stop:
                continue

            formula = _formula_row(item)
            if formula is not None:
                datasets["code_formulas"].append(formula)
                continue

            is_h1, is_h2, is_h3 = _heading_flags(item, upper, style_lower)
            heading_label = _heading_or_list_label(item, is_h1, is_h2, is_h3)
            if heading_label is not None:
                datasets["headings_vs_lists"].append(_row(item, HEADING_COLUMNS, heading_label))

            body_label = _body_label(item, zone, upper, is_h1 or is_h2 or is_h3)
            if body_label is not None:
                datasets["body_bibliography"].append(_row(item, BODY_COLUMNS, body_label))

    return datasets


def write_csv(filename: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print(f"[Warning] Dataset {filename} kosong!")
        return
    filepath = os.path.join(OUT_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f" Berhasil simpan: {filepath} ({len(rows)} baris)")


def main():
    all_docs_items = []
    for filepath, doc_id, _ in GOLDEN_DOCUMENTS:
        if os.path.exists(filepath):
            print(f"Ekstraksi elemen dari: {filepath}...")
            items = extract_document_elements(filepath, doc_id)
            print(f"  -> {len(items)} elemen diekstraksi.")
            all_docs_items.append(items)
        else:
            print(f"[Skip] File tidak ditemukan: {filepath}")

    datasets = classify_documents(all_docs_items)
    os.makedirs(OUT_DIR, exist_ok=True)

    print("\n=== MENYIMPAN 4 DATASET MODULAR ASDOKU (SESUAI DOKUMEN ASLI USER) ===")
    for _, doc_id, filename in GOLDEN_DOCUMENTS:
        write_csv(filename, [item for doc in all_docs_items for item in doc if item["doc_id"] == doc_id])

    print("\n=== MENYIMPAN 7 MASTER DATASETS SPESIALIS (MURNI DARI DATASET ASDOKU) ===")
    for name, filename in DATASET_FILES.items():
        write_csv(filename, datasets[name])
    print("========================================================================\n")


if __name__ == "__main__":
    main()
