"""Kosakata & pola baku naskah akademik UEU yang dipakai bersama oleh Agent 1 dan Agent 2."""

import re
from typing import Optional, Tuple

LABEL_COVER = "COVER_METADATA"
LABEL_FRONTMATTER = "FRONTMATTER_TITLE"
LABEL_CHAPTER = "JUDUL_BAB"
LABEL_SUBCHAPTER = "SUB_BAB"
LABEL_BODY = "BODY_PARAGRAPH"
LABEL_FIGURE_CAPTION = "CAPTION_GAMBAR"
LABEL_TABLE_CAPTION = "CAPTION_TABEL"
LABEL_OTHER = "LAINNYA"
LABEL_BIBLIOGRAPHY = "DAFTAR_PUSTAKA_ITEM"
STRUCTURAL_LABELS = (LABEL_SUBCHAPTER, LABEL_CHAPTER, LABEL_FRONTMATTER)
ALL_LABELS = (
    LABEL_COVER, LABEL_FRONTMATTER, LABEL_CHAPTER, LABEL_SUBCHAPTER, LABEL_BODY,
    LABEL_FIGURE_CAPTION, LABEL_TABLE_CAPTION, LABEL_BIBLIOGRAPHY, LABEL_OTHER,
)

HEADING2_STYLES = ("Heading 2", "Heading2")
HEADING3_STYLES = ("Heading 3", "Heading3")
SUBHEADING_STYLES = HEADING2_STYLES + HEADING3_STYLES

MAX_CAPTION_WORDS = 25

NARRATIVE_VERBS = frozenset({
    "memperlihatkan", "menunjukkan", "menyajikan", "menjelaskan", "terlihat", "tampak",
    "merupakan", "adalah", "berisi", "menegaskan", "menggambarkan",
})

_CAPTION_PREFIXES = {
    LABEL_FIGURE_CAPTION: "Gambar|Figure",
    LABEL_TABLE_CAPTION: "Tabel|Table",
}

# Kosakata baku UEU: satu sumber untuk rule prior, audit konteks Agent 2, dan uji SQA Tier 2.
CHAPTER_TITLES_BY_NUMBER = {
    1: ["PENDAHULUAN"],
    2: ["TINJAUAN PUSTAKA", "LANDASAN TEORI", "DASAR TEORI", "KAJIAN PUSTAKA", "STUDI TEORITIS"],
    3: ["GAMBARAN UMUM PERUSAHAAN", "GAMBARAN UMUM", "PROFIL PERUSAHAAN", "PELAKSANAAN KERJA PRAKTIK", "URAIAN MATERI", "URAIAN MATERI KERJA PRAKTIK", "METODE", "METODOLOGI", "METODE PENELITIAN", "METODOLOGI PENELITIAN", "PERANCANGAN SISTEM"],
    4: ["ANALISIS DAN PEMBAHASAN", "ANALISIS HASIL DAN PEMBAHASAN", "HASIL DAN PEMBAHASAN", "ANALISIS DAN PERANCANGAN", "HASIL", "PEMBAHASAN", "IMPLEMENTASI", "HASIL PENELITIAN",
        "RENCANA HASIL DAN PEMBAHASAN", "RENCANA HASIL"],  # panduan proposal fakultas: Bab IV berisi rencana hasil
    5: ["KESIMPULAN DAN SARAN", "PENUTUP", "KESIMPULAN"],
}
CHAPTER_TITLES = tuple(name for names in CHAPTER_TITLES_BY_NUMBER.values() for name in names)
FRONTMATTER_TITLES = (
    "ABSTRAK", "ABSTRACT", "KATA PENGANTAR", "PRAKATA",
    "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR", "DAFTAR SIMBOL",
    "DAFTAR LAMPIRAN", "DAFTAR PUSTAKA", "DAFTAR REFERENSI",
    "HALAMAN PERNYATAAN", "HALAMAN PENGESAHAN", "HALAMAN PERSETUJUAN",
    "HALAMAN PERSETUJUAN PUBLIKASI", "PERSETUJUAN PUBLIKASI",
    "LEMBAR PENGESAHAN", "LEMBAR PERNYATAAN", "PERNYATAAN KEASLIAN",
    "UNTUK KEPENTINGAN AKADEMIS", "LAMPIRAN",
)
BIBLIOGRAPHY_TITLES = ("DAFTAR PUSTAKA", "DAFTAR REFERENSI", "BIBLIOGRAPHY", "REFERENCES")
SUBCHAPTER_TITLES = (
    "LATAR BELAKANG", "IDENTIFIKASI MASALAH", "RUMUSAN MASALAH", "BATASAN MASALAH",
    "TUJUAN PENELITIAN", "TUJUAN MAGANG", "MAKSUD DAN TUJUAN", "MANFAAT PENELITIAN",
    "MANFAAT MAGANG", "MANFAAT TUGAS AKHIR", "TUJUAN TUGAS AKHIR", "MANFAAT", "TUJUAN",
    "RUANG LINGKUP", "LINGKUP TUGAS AKHIR", "LINGKUP", "KERANGKA BERPIKIR", "KERANGKA PEMIKIRAN",
    "SISTEMATIKA PENULISAN", "SISTEMATIKA PENULISAN LAPORAN", "SISTEMATIKA PENULISAN TUGAS AKHIR",
    "PROFIL PERUSAHAAN", "SEJARAH PERUSAHAAN", "SEJARAH PERUSAHAAN DAN PERKEMBANGANNYA",
    "VISI DAN MISI", "VISI PERUSAHAAN", "MISI PERUSAHAAN", "STRUKTUR ORGANISASI",
    "TEORI", "LANDASAN", "KAJIAN",
    "RENCANA PENELITIAN", "OBYEK PENELITIAN", "OBJEK PENELITIAN", "POPULASI DAN SAMPEL",
    "DEFINISI OPERASIONAL VARIABEL", "DEFINISI OPERASIONAL", "TEKNIK PENGUMPULAN DATA", "PENGUMPULAN DATA",
    "ANALISIS KEBUTUHAN", "ANALISIS KEBUTUHAN SISTEM", "DESKRIPSI PROBLEM DAN SOLUSI",
    "KEBUTUHAN FUNGSIONAL", "KEBUTUHAN NON FUNGSIONAL",
    "DATA HASIL PENELITIAN", "PEMBAHASAN HASIL PENELITIAN", "ANALISIS DATA", "PERBANDINGAN DENGAN PENELITIAN LAIN",
    "TAHAPAN IMPLEMENTASI METODE WATERFALL", "PEMODELAN DATABASE",
    "PEMODELAN BASIS DATA", "DIAGRAM ALUR KERJA", "USE CASE DIAGRAM",
    "FLOWCHART ALUR PENGGUNA", "ACTIVITY DIAGRAM PENGGUNA", "SEQUENCE DIAGRAM INTERAKSI PENGGUNA",
    "ANTARMUKA UI/UX", "HASIL PENGUJIAN FUNGSIONAL DAN NON FUNGSIONAL", "PENGUJIAN FUNGSIONAL",
    "KENDALA TEKNIS DAN SOLUSINYA", "KENDALA TEKNIS", "KESIMPULAN", "SARAN",
)

RULE_PRIOR_COVER_ZONE = 0.15  # 15% awal dokumen dianggap zona sampul
RULE_PRIOR_COVER_PHRASES = (
    "TUGAS AKHIR", "SKRIPSI", "LAPORAN KERJA PRAKTIK", "PROGRAM STUDI", "FAKULTAS",
    "UNIVERSITAS ESA UNGGUL", "TAHUN 202", "DIAJUKAN SEBAGAI", "NAMA :", "NIM :",
)
RULE_PRIOR_FORM_FIELDS = (
    "NAMA :", "NIM :", "NAME :", "STUDENT ID", "STUDY PROGRAM", "TANDA TANGAN", "TANGGAL :",
    "DIBUAT DI", "DITETAPKAN DI", "TIM PENGUJI", "PENGUJI I", "PENGUJI II", "TAHUN 202",
    "KATA KUNCI", "KEYWORDS",
)

SUBCHAPTER_NUMBER_RE = re.compile(r"^\d+\.\d+")
SUBSUB_NUMBER_RE = re.compile(r"^\d+\.\d+\.\d+")
BAB_LITERAL_RE = re.compile(r"^BAB\s+([IVX\d]+)\b")


def caption_kind(text: str) -> Optional[str]:
    """Label caption ('CAPTION_GAMBAR'/'CAPTION_TABEL') bila teks diawali pola caption bernomor."""
    for label, prefix in _CAPTION_PREFIXES.items():
        if re.match(rf"^({prefix})\s*[\.\d]", text, re.IGNORECASE):
            return label
    return None


def is_narrative_caption(text: str, label: str) -> bool:
    """True jika setelah 'Gambar 2.1' langsung diikuti kata kerja naratif (kalimat isi, bukan caption)."""
    rest = re.sub(rf"^({_CAPTION_PREFIXES[label]})\s*[\.\d\s:\-]+", "", text, flags=re.IGNORECASE).strip().lower()
    words = rest.split()
    return bool(words) and words[0] in NARRATIVE_VERBS


def rule_prior_label(features: dict) -> Optional[Tuple[str, str]]:
    """(label, alasan) dari aturan baku UEU berdasarkan fitur mentah satu paragraf, atau None
    bila tidak ada aturan yang berlaku (keputusan diserahkan ke rantai audit konteks Agent 2)."""
    text = features["text"].strip()
    upper = text.upper().rstrip(".:;")
    word_count = len(upper.split())

    if features["char_len"] == 0:
        if features["has_img"]:
            return LABEL_BODY, "Paragraf tanpa teks berisi gambar."
        return LABEL_OTHER, "Paragraf kosong."
    if features["doc_pos"] < RULE_PRIOR_COVER_ZONE and any(k in upper for k in RULE_PRIOR_COVER_PHRASES):
        return LABEL_COVER, "Frasa identitas sampul di zona awal dokumen."
    if any(k in upper for k in RULE_PRIOR_FORM_FIELDS):
        return LABEL_BODY, "Isian formulir (Nama/NIM/Kata Kunci/dll.) adalah teks biasa."
    if word_count <= 10 and upper.startswith(FRONTMATTER_TITLES):
        return LABEL_FRONTMATTER, "Judul halaman awal resmi UEU."
    if word_count <= 5 and (upper in CHAPTER_TITLES or upper.startswith("BAB ")):
        return LABEL_CHAPTER, "Pola judul Bab ('BAB X' atau nama bab kanonikal)."

    caption = caption_kind(text)
    if caption and word_count <= MAX_CAPTION_WORDS:
        if is_narrative_caption(text, caption):
            return LABEL_BODY, "Kalimat naratif yang diawali 'Gambar/Tabel X' (bukan caption)."
        return caption, "Pola caption bernomor 'Gambar/Tabel X.Y'."

    if word_count <= 8 and not text.endswith(".") and upper.startswith(SUBCHAPTER_TITLES):
        return LABEL_SUBCHAPTER, "Nama Sub-Bab baku UEU."
    if features["style"] in SUBHEADING_STYLES or re.match(r"^\d+\.\d+(\.\d+)*\b", text):
        return LABEL_SUBCHAPTER, "Style Heading 2/3 atau penomoran Sub-Bab."
    return None
