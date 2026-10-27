"""
Modul Generator Dataset Skripsi (Data Ingestion & Auto-Labeling) - Versi 2.

Penyempurnaan Berdasarkan Temuan Empiris:
1. Mencegah TOC items (style 'toc') memicu transisi zona prematur.
2. Mendeteksi Judul Bab otomatis tanpa kata 'BAB' (Heading 1 + numPr + kata baku seperti PENDAHULUAN).
3. Mendeteksi Sub-Bab otomatis (Heading 2 + numPr).
4. Mendeteksi Caption Gambar (Gambar 1-1, Gambar 1.1) dan Tabel (Tabel 2-1, Tabel 2.1) secara presisi.
"""

import csv
import os
import re
from typing import Any, Dict, List

from docx import Document

from src.paragraph_features import extract_paragraph_features

# Daftar istilah baku bagian awal (Frontmatter)
FRONTMATTER_KEYWORDS = [
    "LEMBAR PENGESAHAN", "HALAMAN PENGESAHAN", "PENGESAHAN",
    "HALAMAN PERNYATAAN KEASLIAN", "PERNYATAAN KEASLIAN",
    "KATA PENGANTAR", "UCAPAN TERIMA KASIH",
    "ABSTRAK", "ABSTRACT",
    "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR",
    "DAFTAR LAMPIRAN", "DAFTAR SIMBOL", "DAFTAR RUMUS"
]
FRONTMATTER_ZONE_TRIGGERS = ("LEMBAR PENGESAHAN", "HALAMAN PENGESAHAN", "PERNYATAAN KEASLIAN", "KATA PENGANTAR")
BIBLIOGRAPHY_TITLES = ("DAFTAR PUSTAKA", "DAFTAR REFERENSI")

# Kata kunci judul bab standar akademik UEU
BAB_STANDARD_TITLES = [
    "PENDAHULUAN", "TINJAUAN PUSTAKA", "LANDASAN TEORI", "METODE",
    "METODOLOGI", "METODE PENELITIAN", "HASIL", "PEMBAHASAN",
    "HASIL DAN PEMBAHASAN", "KESIMPULAN", "SARAN", "KESIMPULAN DAN SARAN",
    "PENUTUP"
]

BAB_PATTERN = re.compile(r'^(BAB\s+[IVX\d]+|BAB\s+\d+)(\s*[:\-\n\r]\s*|\s+|$)', re.IGNORECASE)
SUB_BAB_NUM_PATTERN = re.compile(r'^\d+(\.\d+)+(\s+.*|$)', re.IGNORECASE)

# Pattern Caption Gambar & Tabel (mendukung format 1.1 maupun 1-1 khas UEU)
CAPTION_GAMBAR_PATTERN = re.compile(r'^(Gambar|Figure)\s+\d+[\.\-]\d+.*', re.IGNORECASE)
CAPTION_TABEL_PATTERN = re.compile(r'^(Tabel|Table)\s+\d+[\.\-]\d+.*', re.IGNORECASE)
MAX_CAPTION_WORDS = 25


def extract_raw_paragraphs(file_path: str, doc_id: str) -> List[Dict[str, Any]]:
    """Membaca paragraf dan mengekstrak sinyal mentah OpenXML."""
    paragraphs = Document(file_path).paragraphs
    total = len(paragraphs)
    return [{"doc_id": doc_id, **extract_paragraph_features(p, idx, total)} for idx, p in enumerate(paragraphs)]


def _is_chapter_start(text: str, upper: str, style_lower: str, is_bold: bool) -> bool:
    return bool(BAB_PATTERN.match(text) and is_bold) or ("heading 1" in style_lower and upper in BAB_STANDARD_TITLES)


def _next_zone(zone: str, text: str, upper: str, style_lower: str, is_bold: bool, in_sistematika: bool) -> str:
    """Transisi zona dokumen; pemicu yang lebih akhir menimpa yang lebih awal."""
    if any(kw in upper for kw in FRONTMATTER_ZONE_TRIGGERS):
        zone = "FRONTMATTER"
    # Zona BODY: teks 'BAB I' tebal, ATAU Heading 1 dengan judul bab baku (misal PENDAHULUAN di template UEU)
    if not in_sistematika and _is_chapter_start(text, upper, style_lower, is_bold):
        zone = "BODY"
    if upper in BIBLIOGRAPHY_TITLES:
        zone = "BIBLIOGRAPHY"
    if upper.startswith("LAMPIRAN") and (is_bold or "heading" in style_lower):
        zone = "APPENDIX"
    return zone


def _body_label(item: Dict[str, Any], text: str, upper: str, style_lower: str, in_sistematika: bool) -> str:
    is_bold, word_count = item["is_bold"], item["word_count"]
    if CAPTION_GAMBAR_PATTERN.match(text) and word_count <= MAX_CAPTION_WORDS:
        return "CAPTION_GAMBAR"
    if CAPTION_TABEL_PATTERN.match(text) and word_count <= MAX_CAPTION_WORDS:
        return "CAPTION_TABEL"
    if in_sistematika:
        return "BODY_PARAGRAPH"
    if (BAB_PATTERN.match(text) and (is_bold or "heading 1" in style_lower or item["align"] == "CENTER") and word_count <= 10) \
            or ("heading 1" in style_lower and upper in BAB_STANDARD_TITLES):
        return "JUDUL_BAB"
    # Sub-Bab: pola desimal (1.1, 1.2.1) + bold/heading, ATAU Heading 2/3 pendek tanpa titik akhir
    if (SUB_BAB_NUM_PATTERN.match(text) and (is_bold or "heading" in style_lower) and word_count <= 15) \
            or (("heading 2" in style_lower or "heading 3" in style_lower) and word_count <= 12 and not text.endswith(".")):
        return "SUB_BAB"
    return "BODY_PARAGRAPH"


def auto_label_document(raw_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    State-Aware Rule-Assisted Labeler.
    Menerapkan pelacakan zona dokumen (State Machine) untuk mencegah False Positive.
    """
    zone = "COVER"
    in_sistematika = False
    labeled = []

    for item in raw_list:
        text = item["text"]
        upper = text.upper()
        style_lower = item["style"].lower()
        is_bold = item["is_bold"]

        if item["char_len"] == 0:
            labeled.append({**item, "label": "LAINNYA"})
            continue

        is_toc_item = "toc" in style_lower or "table of figures" in style_lower
        if not is_toc_item:  # item TOC tidak boleh memicu transisi zona
            zone = _next_zone(zone, text, upper, style_lower, is_bold, in_sistematika)

        if is_toc_item:
            label = "FRONTMATTER_TITLE"
        elif zone == "COVER" and item["doc_pos"] < 0.12:
            label = "COVER_METADATA"
        elif zone == "FRONTMATTER":
            is_title = any(upper == kw or upper.startswith(kw) for kw in FRONTMATTER_KEYWORDS)
            label = "FRONTMATTER_TITLE" if is_title and (is_bold or "heading" in style_lower) and item["word_count"] <= 6 else "BODY_PARAGRAPH"
        elif zone == "BIBLIOGRAPHY":
            label = "FRONTMATTER_TITLE" if upper in BIBLIOGRAPHY_TITLES else "DAFTAR_PUSTAKA_ITEM"
        elif zone == "APPENDIX":
            is_title = upper.startswith("LAMPIRAN") and (is_bold or item["word_count"] <= 8 or "heading" in style_lower)
            label = "FRONTMATTER_TITLE" if is_title else "BODY_PARAGRAPH"
        else:
            # Shield Sistematika Penulisan: keluar saat Bab baru resmi dimulai
            if "SISTEMATIKA PENULISAN" in upper:
                in_sistematika = True
            elif in_sistematika and ("heading 1" in style_lower or item["has_pgbrk"]) and (BAB_PATTERN.match(text) or upper in BAB_STANDARD_TITLES):
                in_sistematika = False
            label = _body_label(item, text, upper, style_lower, in_sistematika)

        labeled.append({**item, "label": label})
    return labeled


def generate_dataset(file_paths: List[Dict[str, str]], output_csv: str = "data/dataset_skripsi.csv"):
    """Menggabungkan ekstraksi dari beberapa dokumen menjadi 1 file dataset CSV."""
    all_rows = []
    print("=== MEMPROSES GENERASI DATASET SKRIPSI (V2) ===")
    for f in file_paths:
        print(f"[*] Mengekstraksi dokumen: {f['id']} ({f['path']})...")
        labeled = auto_label_document(extract_raw_paragraphs(f["path"], f["id"]))
        all_rows.extend(labeled)
        print(f"    -> Berhasil mengekstrak {len(labeled)} paragraf.")

    if not all_rows:
        return
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\n[SUKSES] Total {len(all_rows)} baris data tersimpan ke: {output_csv}")


if __name__ == "__main__":
    docs_to_process = [
        {"id": "DOC_TEMPLATE_BARU_2024", "path": "data/dokumen_uji/P1_Template_Resmi_UEU.docx"},
        {"id": "DOC_TEMPLATE_UEU", "path": "data/dokumen_uji/P5_Buku_TA_Landscape.docx"},
        {"id": "DOC_MHS_DHICKY", "path": "data/dokumen_uji/P2_Skripsi_Mbkm_Dhicky.docx"},
        {"id": "DOC_MHS_IDHAM", "path": "data/doc_idham.docx"},
        {"id": "DOC_MHS_CONTOH", "path": "data/dokumen_uji/P4_Laporan_Mbkm_Arditya.docx"}
    ]
    generate_dataset(docs_to_process)
