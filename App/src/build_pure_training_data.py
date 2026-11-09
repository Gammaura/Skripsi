"""
Aturan pra-label paragraf (zona naskah + label berbasis aturan).
Dipakai tools/label_excel.py untuk mengisi tebakan awal label di Excel sebelum dikoreksi.
Standar Acuan: SK Rektor UEU No. 5 Tahun 2018.
"""

import re
from typing import Any, Dict


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
