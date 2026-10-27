"""
Modul Pembuat Dataset Training Murni (Pure Ground-Truth)
Khusus Mengekstrak dari 4 Berkas Emas: Dataset Asdoku 1 s/d 4.
Standar Acuan: SK Rektor UEU No. 5 Tahun 2018.
"""

import csv
import os
import re
from collections import Counter
from typing import Any, Dict, List

from docx import Document

from src.paragraph_features import extract_paragraph_features

FRONTMATTER_TITLES = [
    "HALAMAN PERNYATAAN KEASLIAN", "PERNYATAAN KEASLIAN",
    "HALAMAN PENGESAHAN TUGAS AKHIR", "HALAMAN PENGESAHAN", "LEMBAR PENGESAHAN",
    "HALAMAN PERSETUJUAN PUBLIKASI KARYA ILMIAH", "PERSETUJUAN PUBLIKASI",
    "KATA PENGANTAR", "PRAKATA", "UCAPAN TERIMA KASIH",
    "ABSTRAK", "ABSTRACT",
    "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR", "DAFTAR SIMBOL", "DAFTAR LAMPIRAN",
    "DAFTAR REFERENSI", "DAFTAR PUSTAKA"
]

CHAPTER_NAMES = [
    "PENDAHULUAN", "TINJAUAN PUSTAKA", "LANDASAN TEORI", "METODE", "METODOLOGI",
    "METODE PENELITIAN", "HASIL DAN PEMBAHASAN", "KESIMPULAN DAN SARAN", "PENUTUP"
]

FRONTMATTER_ZONE_TRIGGERS = ("HALAMAN PERNYATAAN KEASLIAN", "HALAMAN PENGESAHAN TUGAS AKHIR", "KATA PENGANTAR")
BIBLIOGRAPHY_TITLES = ("DAFTAR REFERENSI", "DAFTAR PUSTAKA")
COVER_KEYWORDS = (
    "TUGAS AKHIR", "SKRIPSI", "ARDITYA ADJIE", "20230801274", "TEKNIK INFORMATIKA", "FAKULTAS ILMU KOMPUTER",
    "UNIVERSITAS ESA UNGGUL", "TAHUN 2024", "NAMA", "NIM", "DIAJUKAN SEBAGAI",
)

CAPTION_GAMBAR_RE = re.compile(r'^(Gambar|Figure)\s+(\d+[\.\-]\d+|\.|\d+).*', re.IGNORECASE)
CAPTION_TABEL_RE = re.compile(r'^(Tabel|Table)\s+(\d+[\.\-]\d+|\.|\d+).*', re.IGNORECASE)
BAB_RE = re.compile(r'^(BAB\s+[IVX\d]+|BAB\s+\d+)', re.IGNORECASE)
SUBCHAPTER_NUMBER_RE = re.compile(r'^\d+\.\d+(\.\d+)?\s+')

TARGET_FILES = [
    ("Dataset Asdoku/Dataset Asdoku 1.docx", "ASDOKU_1_TEMPLATE_UTUH"),
    ("Dataset Asdoku/Dataset Asdoku 2.docx", "ASDOKU_2_TOC_HEADINGS"),
    ("Dataset Asdoku/Dataset Asdoku 3.docx", "ASDOKU_3_FIGURES_TOF"),
    ("Dataset Asdoku/Dataset Asdoku 4.docx", "ASDOKU_4_TABLES_TOT"),
]
OUTPUT_CSV = "data/dataset_skripsi.csv"


def _next_zone(zone: str, upper: str) -> str:
    if upper in FRONTMATTER_ZONE_TRIGGERS:
        return "FRONTMATTER"
    if upper in CHAPTER_NAMES or upper.startswith("BAB "):
        return "BODY_BAB"
    if upper in BIBLIOGRAPHY_TITLES:
        return "BIBLIOGRAPHY"
    if upper.startswith("LAMPIRAN"):
        return "APPENDIX"
    return zone


def _label(f: Dict[str, Any], zone: str) -> str:
    """Label kebenaran berbasis aturan berprioritas untuk satu paragraf."""
    text, upper = f["text"], f["text"].upper()
    style_lower = f["style"].lower()
    word_count, size, bold = f["word_count"], f["font_size"], f["is_bold"]

    if f["char_len"] == 0:
        return "BODY_PARAGRAPH" if f["has_img"] else "LAINNYA"
    if CAPTION_GAMBAR_RE.match(text) and word_count <= 25:
        return "CAPTION_GAMBAR"
    if CAPTION_TABEL_RE.match(text) and word_count <= 25:
        return "CAPTION_TABEL"
    # Judul Bab Utama (Heading 1 di Zona Bab / Kanonikal)
    if (BAB_RE.match(text) and word_count <= 10) or (upper in CHAPTER_NAMES and ("heading 1" in style_lower or size >= 14 or bold)):
        return "JUDUL_BAB"
    # Sub-Bab (Heading 2 / Heading 3)
    if ("heading 2" in style_lower or "heading 3" in style_lower or SUBCHAPTER_NUMBER_RE.match(text)
            or (zone == "BODY_BAB" and word_count <= 12 and bold and not text.endswith(".") and size >= 12.0)):
        return "SUB_BAB"
    # Judul Frontmatter / Halaman Depan / Lampiran
    if upper in FRONTMATTER_TITLES or (upper.startswith("LAMPIRAN") and word_count <= 8):
        return "FRONTMATTER_TITLE"
    if zone == "COVER" and f["doc_pos"] < 0.15 and any(k in upper for k in COVER_KEYWORDS):
        return "COVER_METADATA"
    if zone == "BIBLIOGRAPHY" and word_count > 4 and upper not in BIBLIOGRAPHY_TITLES:
        return "DAFTAR_PUSTAKA_ITEM"
    # Paragraf isi, list rincian, code, math
    return "BODY_PARAGRAPH"


def extract_and_label_document(docx_path: str, doc_id: str) -> List[Dict[str, Any]]:
    paragraphs = Document(docx_path).paragraphs
    total = len(paragraphs)
    zone = "COVER"
    items = []
    for idx, p in enumerate(paragraphs):
        features = extract_paragraph_features(p, idx, total)
        zone = _next_zone(zone, features["text"].upper())
        items.append({"doc_id": doc_id, **features, "label": _label(features, zone)})
    return items


def main():
    all_samples = []
    for filepath, doc_id in TARGET_FILES:
        if os.path.exists(filepath):
            print(f"Mengekstrak berkas emas: {filepath}...")
            samples = extract_and_label_document(filepath, doc_id)
            print(f"  -> {len(samples)} baris diekstraksi.")
            all_samples.extend(samples)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_samples[0].keys()))
        writer.writeheader()
        writer.writerows(all_samples)
    print(f"\n[SUKSES] Dataset training murni berhasil disimpan ke: {OUTPUT_CSV} ({len(all_samples)} baris)")

    print("\n--- DISTRIBUSI KELAS TRAINING MURNI ASDOKU ---")
    for label, count in Counter(s["label"] for s in all_samples).most_common():
        print(f"  {label:22s}: {count:4d} baris")
    print("-----------------------------------------------\n")


if __name__ == "__main__":
    main()
