"""Kosakata & pola baku naskah akademik UEU yang dipakai bersama oleh Agent 1 dan Agent 2."""

import re
from typing import Optional

LABEL_COVER = "COVER_METADATA"
LABEL_FRONTMATTER = "FRONTMATTER_TITLE"
LABEL_CHAPTER = "JUDUL_BAB"
LABEL_SUBCHAPTER = "SUB_BAB"
LABEL_BODY = "BODY_PARAGRAPH"
LABEL_FIGURE_CAPTION = "CAPTION_GAMBAR"
LABEL_TABLE_CAPTION = "CAPTION_TABEL"
LABEL_OTHER = "LAINNYA"
STRUCTURAL_LABELS = (LABEL_SUBCHAPTER, LABEL_CHAPTER, LABEL_FRONTMATTER)

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
