"""
Modul Pipeline Ekstraksi Fitur Dokumen (Feature Engineering).
Dibuat mandiri agar dapat di-pickle dan di-load secara universal di semua agen.
"""

import re

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer

# (kolom, nilai default, pembagi normalisasi) — urutan = urutan kolom fitur.
_NUMERIC_FEATURES = (
    ("char_len", 0, 400.0),
    ("word_count", 0, 80.0),
    ("uppercase_ratio", 0.0, 1.0),
    ("font_size", 12.0, 14.0),
)
_BINARY_FEATURES = ("is_bold", "is_italic", "has_num", "has_img", "has_pgbrk")
_LAYOUT_FEATURES = (
    ("space_before", 0.0, 24.0),
    ("space_after", 0.0, 12.0),
    ("line_spacing", 1.15, 1.5),
    ("first_line_indent", 0.0, 1.27),
    ("left_indent", 0.0, 2.0),
    ("doc_pos", 0.0, 1.0),
)


# Petunjuk gaya Word (nama style, huruf kecil) -> fitur biner.
_STYLE_FEATURES = (
    lambda s: s == "heading 1",
    lambda s: s == "heading 2",
    lambda s: re.match(r"heading [3-9]", s) is not None,
    lambda s: s.startswith("toc") or s == "table of figures",  # baris Daftar Isi/Tabel/Gambar
    lambda s: s == "caption",
    lambda s: "list" in s,
    lambda s: s in ("title", "subtitle"),
)
# Pola teks khas struktur naskah -> fitur biner.
_TEXT_PATTERNS = (
    re.compile(r"^BAB\s+([IVX]+|\d+)\b", re.I),                       # BAB I / BAB 1
    re.compile(r"^\d+(\.\d+)+\.?\s+\S"),                                # 2.1 / 2.1.3 Judul
    re.compile(r"^(Gambar|Figure)\s+\d", re.I),                         # Gambar 2.1
    re.compile(r"^(Tabel|Table)\s+\d", re.I),                           # Tabel 3.2
    re.compile(r"(\s|\.)([ivxlc]+|\d{1,3})$", re.I),                    # nomor halaman di ujung (daftar isi)
    re.compile(r"^[A-Z][\w'’\-]+,?\s+([A-Z]\.\s?)+.*\((\d{4}|n\.d\.)[a-z]?\)"),  # Nama, A. (2021).
    re.compile(r"\((19|20)\d{2}[a-z]?\)"),                               # (2021)
    re.compile(r"^[A-Za-z][A-Za-z /]{1,30}\s:\s?"),                       # isian formulir "Nama : ..."
    re.compile(r"^([A-Za-z]|\d{1,2})[\.\)]\s+\S"),                       # poin "1. " / "a) "
    re.compile(r"[\.:;]$"),                                               # diakhiri tanda baca
)


class DocumentFeaturePipeline:
    """Pipeline ekstraksi fitur gabungan (TF-IDF Teks + Metadata Tipografi OpenXML + gaya Word + pola teks)."""

    def __init__(self, max_tfidf_features: int = 400):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=max_tfidf_features, lowercase=True)
        self.align_categories = ["CENTER", "JUSTIFY", "LEFT", "RIGHT", "DEFAULT"]

    def _row_features(self, row: pd.Series) -> list:
        def scaled(spec):
            return [float(row.get(col, default)) / scale for col, default, scale in spec]

        align = str(row.get("align", "DEFAULT"))
        style = str(row.get("style", "") or "").lower()
        text = str(row.get("text", "") or "").strip()
        return (
            scaled(_NUMERIC_FEATURES)
            + [1.0 if row.get(col, False) else 0.0 for col in _BINARY_FEATURES]
            + scaled(_LAYOUT_FEATURES)
            + [1.0 if align == cat else 0.0 for cat in self.align_categories]
            + [1.0 if is_style(style) else 0.0 for is_style in _STYLE_FEATURES]
            + [1.0 if pattern.search(text) else 0.0 for pattern in _TEXT_PATTERNS]
        )

    def _extract_meta_features(self, df: pd.DataFrame) -> np.ndarray:
        return np.array([self._row_features(row) for _, row in df.iterrows()], dtype=np.float32)

    @staticmethod
    def _texts(df: pd.DataFrame) -> list:
        return df["text"].fillna("").astype(str).tolist()

    def _combine(self, X_tfidf, df: pd.DataFrame) -> csr_matrix:
        return hstack([X_tfidf, csr_matrix(self._extract_meta_features(df))]).tocsr()

    def fit_transform(self, df: pd.DataFrame) -> csr_matrix:
        return self._combine(self.vectorizer.fit_transform(self._texts(df)), df)

    def transform(self, df: pd.DataFrame) -> csr_matrix:
        return self._combine(self.vectorizer.transform(self._texts(df)), df)
