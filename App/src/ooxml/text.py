"""Pembersihan teks judul dan konversi penomoran khas naskah akademik Indonesia."""

import re

BAB_PREFIX_RE = re.compile(r"^(BAB\s*(\d+|[IVXLCDM]+)[\s:\.\-]*)+", re.IGNORECASE)
SUBBAB_PREFIX_RE = re.compile(r"^((\d+|[A-Za-z])\.)+(\d+)*\s*")
NUMBER_PREFIX_RE = re.compile(r"^\d+(\.\d+)*\s*")
SUBSUB_NUMBER_RE = re.compile(r"^\d+\.\d+\.\d+")

_ROMAN_VALUES = (
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
)

_TITLE_SMALL_WORDS = {
    "dan", "atau", "yang", "di", "ke", "dari", "pada", "untuk", "dengan",
    "terhadap", "dalam", "tentang", "oleh", "sebagai", "atas",
}


def to_roman(n: int) -> str:
    """1 -> 'I', 4 -> 'IV'. Nilai non-positif dikembalikan apa adanya."""
    if not isinstance(n, int) or n <= 0:
        return str(n)
    result = ""
    for value, symbol in _ROMAN_VALUES:
        count, n = divmod(n, value)
        result += symbol * count
    return result


def to_title_case(text: str) -> str:
    """Title Case bahasa Indonesia: kata sambung kecil, kata ber-tanda hubung dikapitalisasi per bagian."""
    words = []
    for idx, word in enumerate(text.split()):
        if "-" in word:
            words.append("-".join(part.capitalize() for part in word.split("-")))
        elif idx > 0 and word.lower() in _TITLE_SMALL_WORDS:
            words.append(word.lower())
        else:
            words.append(word.capitalize())
    return " ".join(words)


def strip_bab_prefix(text: str) -> str:
    """'BAB II  LANDASAN TEORI' -> 'LANDASAN TEORI'."""
    return BAB_PREFIX_RE.sub("", text).strip()


def strip_subbab_number(text: str) -> str:
    """'2.1.3 Metode Penelitian' -> 'Metode Penelitian'."""
    without_outline = SUBBAB_PREFIX_RE.sub("", text).strip()
    return NUMBER_PREFIX_RE.sub("", without_outline).strip()
