"""
AGENT 1: INSPECTOR (Detection & Classification Agent).

Tugas:
1. Membaca naskah Word (.docx) secara non-destruktif.
2. Mengekstraksi fitur teks NLP dan metadata tipografi OpenXML per paragraf.
3. Melakukan inferensi probabilistik dengan model Machine Learning terlatih.
4. Menyelaraskan prediksi dengan aturan baku UEU dan menandai paragraf ambigu
   (confidence < 0.70) untuk diaudit Agent 2 (Critic).
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from docx import Document

from src.academic_rules import (
    LABEL_BODY,
    LABEL_CHAPTER,
    LABEL_COVER,
    LABEL_FIGURE_CAPTION,
    LABEL_FRONTMATTER,
    LABEL_OTHER,
    LABEL_SUBCHAPTER,
    LABEL_TABLE_CAPTION,
    MAX_CAPTION_WORDS,
    SUBHEADING_STYLES,
    SUBSUB_NUMBER_RE,
    caption_kind,
    is_narrative_caption,
)
from src.paragraph_features import extract_paragraph_features

DEFAULT_MODEL_PATH = "models/baseline_model.joblib"
DEFAULT_PIPELINE_PATH = "models/feature_pipeline.joblib"
AMBIGUITY_THRESHOLD = 0.70
RULE_CONFIDENCE = 0.99
NARRATIVE_CAPTION_CONFIDENCE = 0.95
SQA_CONFIDENCE = 0.999
PREVIEW_CHARS = 40
COVER_ZONE_LIMIT = 0.15

COVER_KEYWORDS = (
    "TUGAS AKHIR", "SKRIPSI", "LAPORAN KERJA PRAKTIK", "PROGRAM STUDI", "FAKULTAS",
    "UNIVERSITAS ESA UNGGUL", "TAHUN 202", "DIAJUKAN SEBAGAI", "NAMA :", "NIM :",
)
FORM_FIELD_KEYWORDS = (
    "NAMA :", "NIM :", "NAME :", "STUDENT ID", "STUDY PROGRAM", "TANDA TANGAN", "TANGGAL :",
    "DIBUAT DI", "DITETAPKAN DI", "TIM PENGUJI", "PENGUJI I", "PENGUJI II", "TAHUN 202",
    "KATA KUNCI", "KEYWORDS",
)
FRONTMATTER_TITLES = (
    "ABSTRAK", "ABSTRACT", "KATA PENGANTAR", "PRAKATA", "DAFTAR ISI", "DAFTAR TABEL",
    "DAFTAR GAMBAR", "DAFTAR SIMBOL", "DAFTAR LAMPIRAN", "HALAMAN PERNYATAAN",
    "HALAMAN PENGESAHAN", "HALAMAN PERSETUJUAN", "HALAMAN PERSETUJUAN PUBLIKASI",
    "PERSETUJUAN PUBLIKASI", "UNTUK KEPENTINGAN AKADEMIS", "DAFTAR REFERENSI", "DAFTAR PUSTAKA",
)
CANONICAL_CHAPTER_TITLES = (
    "PENDAHULUAN", "TINJAUAN PUSTAKA", "LANDASAN TEORI", "METODE", "METODOLOGI",
    "METODE PENELITIAN", "HASIL DAN PEMBAHASAN", "KESIMPULAN DAN SARAN",
)
STANDARD_SUBCHAPTER_TITLES = (
    "LATAR BELAKANG", "IDENTIFIKASI MASALAH", "RUMUSAN MASALAH", "BATASAN MASALAH",
    "TUJUAN", "MANFAAT", "RUANG LINGKUP", "LINGKUP", "KERANGKA BERPIKIR", "SISTEMATIKA PENULISAN",
    "PROFIL PERUSAHAAN", "VISI DAN MISI", "STRUKTUR ORGANISASI", "TEORI", "LANDASAN",
    "RENCANA PENELITIAN", "OBYEK PENELITIAN", "POPULASI DAN SAMPEL", "TEKNIK PENGUMPULAN DATA",
    "ANALISIS KEBUTUHAN", "KEBUTUHAN FUNGSIONAL", "DATA HASIL PENELITIAN", "PEMBAHASAN HASIL PENELITIAN",
    "ANALISIS DATA", "PERBANDINGAN DENGAN PENELITIAN LAIN", "KESIMPULAN", "SARAN",
)


def _rule_based_label(features: Dict[str, Any]) -> Optional[Tuple[str, float]]:
    """Label & confidence dari aturan baku UEU, atau None jika prediksi ML dipertahankan."""
    text = features["text"].strip()
    upper = text.upper().rstrip(".:;")
    word_count = len(upper.split())

    if features["char_len"] == 0:
        return (LABEL_BODY if features["has_img"] else LABEL_OTHER), RULE_CONFIDENCE
    if features["doc_pos"] < COVER_ZONE_LIMIT and any(k in upper for k in COVER_KEYWORDS):
        return LABEL_COVER, RULE_CONFIDENCE
    if any(k in upper for k in FORM_FIELD_KEYWORDS):
        return LABEL_BODY, RULE_CONFIDENCE
    if word_count <= 10 and upper.startswith(FRONTMATTER_TITLES):
        return LABEL_FRONTMATTER, RULE_CONFIDENCE
    if word_count <= 5 and (upper in CANONICAL_CHAPTER_TITLES or upper.startswith("BAB ")):
        return LABEL_CHAPTER, RULE_CONFIDENCE

    caption = caption_kind(text)
    if caption and word_count <= MAX_CAPTION_WORDS:
        if is_narrative_caption(text, caption):
            return LABEL_BODY, NARRATIVE_CAPTION_CONFIDENCE
        return caption, RULE_CONFIDENCE

    if word_count <= 8 and not text.endswith(".") and upper.startswith(STANDARD_SUBCHAPTER_TITLES):
        return LABEL_SUBCHAPTER, RULE_CONFIDENCE
    if features["style"] in SUBHEADING_STYLES or re.match(r"^\d+\.\d+(\.\d+)*\b", text):
        return LABEL_SUBCHAPTER, RULE_CONFIDENCE
    return None


def summarize_blueprint(paragraphs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Statistik ringkas blueprint: distribusi label, jumlah bab/sub-bab/caption, paragraf ambigu."""
    by_label: Dict[str, List[str]] = {LABEL_CHAPTER: [], LABEL_SUBCHAPTER: [], "CAPTION": []}
    for p in paragraphs:
        label = p["predicted_label"]
        key = "CAPTION" if label in (LABEL_FIGURE_CAPTION, LABEL_TABLE_CAPTION) else label
        if key in by_label:
            by_label[key].append(f"P[{p['para_id']}] {p['text'][:PREVIEW_CHARS]}")
    return {
        "ambiguous_count": sum(1 for p in paragraphs if p.get("is_ambiguous", False)),
        "label_summary": pd.Series([p["predicted_label"] for p in paragraphs]).value_counts().to_dict(),
        "detected_chapters_count": len(by_label[LABEL_CHAPTER]),
        "detected_subchapters_count": len(by_label[LABEL_SUBCHAPTER]),
        "detected_captions_count": len(by_label["CAPTION"]),
        "chapters_preview": by_label[LABEL_CHAPTER][:5],
    }


class InspectorAgent:
    """Agent 1: Detection & Classification Agent."""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH, pipeline_path: str = DEFAULT_PIPELINE_PATH):
        if not os.path.exists(model_path) or not os.path.exists(pipeline_path):
            raise FileNotFoundError("Model atau Pipeline ML belum ditemukan. Jalankan src/train.py terlebih dahulu.")
        self.model_path = model_path
        self.pipeline_path = pipeline_path
        self._load_artifacts()
        print("[Agent 1 - Inspector] Model & Feature Pipeline berhasil dimuat.")

    def _load_artifacts(self) -> None:
        self.model = joblib.load(self.model_path)
        self.pipeline = joblib.load(self.pipeline_path)
        self.classes = list(self.model.classes_)

    def reload_model(self) -> None:
        """Hot-reload model & pipeline setelah retraining Active Learning."""
        self._load_artifacts()
        print("[Agent 1 - Inspector] HOT-RELOAD: Model & Feature Pipeline berhasil diperbarui dari Active Learning!")

    def inspect(self, docx_path: str) -> Dict[str, Any]:
        """Menganalisis dokumen Word dan menerbitkan Draft Blueprint."""
        print(f"\n[Agent 1 - Inspector] Memulai inspeksi naskah: {docx_path}...")
        paragraphs = Document(docx_path).paragraphs
        total = len(paragraphs)
        features = [extract_paragraph_features(p, idx, total) for idx, p in enumerate(paragraphs)]

        X = self.pipeline.transform(pd.DataFrame(features))
        probas = self.model.predict_proba(X)
        predictions = self.model.predict(X)

        blueprint = [self._build_record(item, predictions[i], probas[i]) for i, item in enumerate(features)]
        report = {"source_doc": docx_path, "total_paragraphs": total, **summarize_blueprint(blueprint), "paragraphs": blueprint}
        print(
            f"[Agent 1 - Inspector] Selesai! Terdeteksi {report['detected_chapters_count']} Bab, "
            f"{report['detected_subchapters_count']} Sub-Bab, {report['ambiguous_count']} Paragraf Ambigu."
        )
        return report

    def _build_record(self, item: Dict[str, Any], ml_label: str, proba: np.ndarray) -> Dict[str, Any]:
        rule = _rule_based_label(item)
        if rule:
            label, confidence = rule
            is_ambiguous = False
        else:
            label, confidence = ml_label, float(np.max(proba))
            is_ambiguous = confidence < AMBIGUITY_THRESHOLD

        text = item["text"].strip()
        return {
            "para_id": item["para_id"],
            "text": item["text"],
            "predicted_label": label,
            "confidence": round(confidence, 4),
            "is_ambiguous": is_ambiguous,
            "probabilities": {cls: round(float(proba[i]), 4) for i, cls in enumerate(self.classes)},
            "raw_features": item,
            "metadata": {
                "style": item["style"],
                "is_subsub": bool(item["style"] in ("Heading 3", "Heading3") or SUBSUB_NUMBER_RE.match(text)),
                "font_size": item["font_size"],
                "is_bold": item["is_bold"],
                "align": item["align"],
                "has_num": item["has_num"],
                "has_img": item["has_img"],
                "has_pgbrk": item["has_pgbrk"],
                "doc_pos": item["doc_pos"],
            },
        }

    def re_inspect_with_feedback(self, current_report: Dict[str, Any], feedback_directives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        [SQA TIER 1 FEEDBACK LOOP] Menerapkan koreksi Agent 2 ke blueprint dan
        menghitung ulang ringkasannya.
        """
        print(f"[Agent 1 - Inspector] Menerima {len(feedback_directives)} umpan balik dari Agent 2 (SQA). Melakukan re-inspeksi & penyesuaian...")
        directives = {d["para_id"]: d for d in feedback_directives}
        paragraphs = current_report["paragraphs"]
        for p in paragraphs:
            directive = directives.get(p["para_id"])
            if directive is None:
                continue
            p["predicted_label"] = directive["corrected_label"]
            p["confidence"] = SQA_CONFIDENCE
            p["is_ambiguous"] = False
            p["metadata"]["sqa_corrected"] = True
            p["metadata"]["sqa_reason"] = directive.get("reason", "Direvisi berdasarkan audit SQA Agent 2")

        print("[Agent 1 - Inspector] Re-inspeksi selesai! Blueprint diperbarui dengan tingkat kepastian tinggi.")
        return {
            "source_doc": current_report["source_doc"],
            "total_paragraphs": current_report["total_paragraphs"],
            **summarize_blueprint(paragraphs),
            "paragraphs": paragraphs,
            "sqa_iteration": current_report.get("sqa_iteration", 1) + 1,
        }
