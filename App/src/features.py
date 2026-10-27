"""
Modul Pipeline Ekstraksi Fitur Dokumen (Feature Engineering).
Dibuat mandiri agar dapat di-pickle dan di-load secara universal di semua agen.
"""

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


class DocumentFeaturePipeline:
    """Pipeline ekstraksi fitur gabungan (TF-IDF Teks + Metadata Tipografi OpenXML)."""

    def __init__(self, max_tfidf_features: int = 400):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=max_tfidf_features, lowercase=True)
        self.align_categories = ["CENTER", "JUSTIFY", "LEFT", "RIGHT", "DEFAULT"]

    def _row_features(self, row: pd.Series) -> list:
        def scaled(spec):
            return [float(row.get(col, default)) / scale for col, default, scale in spec]

        align = str(row.get("align", "DEFAULT"))
        return (
            scaled(_NUMERIC_FEATURES)
            + [1.0 if row.get(col, False) else 0.0 for col in _BINARY_FEATURES]
            + scaled(_LAYOUT_FEATURES)
            + [1.0 if align == cat else 0.0 for cat in self.align_categories]
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
