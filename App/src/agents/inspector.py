"""
AGENT 1: INSPECTOR (Detection & Classification Agent) - murni Machine Learning.

Tugas:
1. Membaca naskah Word (.docx) secara non-destruktif.
2. Mengekstraksi fitur teks NLP (TF-IDF) dan metadata tipografi OpenXML per paragraf.
3. Melakukan inferensi probabilistik dengan model Machine Learning terlatih, tanpa aturan buatan,
   sehingga kinerja ML dapat diukur terpisah dari validasi aturan Agent 2.
4. Menandai paragraf ambigu (confidence < 0.70) sebagai kandidat kueri Active Learning
   (uncertainty sampling) untuk dikonfirmasi pengguna.
"""

import os
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
from docx import Document

from src.academic_rules import LABEL_CHAPTER, LABEL_FIGURE_CAPTION, LABEL_SUBCHAPTER, LABEL_TABLE_CAPTION, SUBSUB_NUMBER_RE
from src.paragraph_features import extract_paragraph_features

DEFAULT_MODEL_PATH = "models/baseline_model.joblib"
DEFAULT_PIPELINE_PATH = "models/feature_pipeline.joblib"
AMBIGUITY_THRESHOLD = 0.70
SQA_CONFIDENCE = 0.999
PREVIEW_CHARS = 40


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
        # Dimuat ke variabel lokal lalu ditukar sekaligus: request yang sedang berjalan saat
        # hot-reload tetap memakai pasangan model & pipeline yang konsisten.
        model, pipeline = joblib.load(self.model_path), joblib.load(self.pipeline_path)
        self._artifacts = (model, pipeline, list(model.classes_))

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

        model, pipeline, classes = self._artifacts
        probas = model.predict_proba(pipeline.transform(pd.DataFrame(features)))

        blueprint = [self._build_record(item, probas[i], classes) for i, item in enumerate(features)]
        report = {"source_doc": docx_path, "total_paragraphs": total, **summarize_blueprint(blueprint), "paragraphs": blueprint}
        print(
            f"[Agent 1 - Inspector] Selesai! Terdeteksi {report['detected_chapters_count']} Bab, "
            f"{report['detected_subchapters_count']} Sub-Bab, {report['ambiguous_count']} Paragraf Ambigu."
        )
        return report

    @staticmethod
    def _build_record(item: Dict[str, Any], proba: np.ndarray, classes: List[str]) -> Dict[str, Any]:
        best = int(np.argmax(proba))
        confidence = float(proba[best])
        text = item["text"].strip()
        return {
            "para_id": item["para_id"],
            "text": item["text"],
            "predicted_label": classes[best],
            "confidence": round(confidence, 4),
            "is_ambiguous": confidence < AMBIGUITY_THRESHOLD,
            "probabilities": {cls: round(float(proba[i]), 4) for i, cls in enumerate(classes)},
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
        [SQA TIER 1 FEEDBACK LOOP] Menerapkan koreksi Agent 2 ke blueprint dan menghitung ulang ringkasannya.

        Model tidak dijalankan ulang: label terkoreksi diadopsi apa adanya. Iterasi audit berikutnya
        berfungsi sebagai uji konsistensi bahwa blueprint terkoreksi tidak memicu koreksi baru.
        """
        print(f"[Agent 1 - Inspector] Menerima {len(feedback_directives)} umpan balik dari Agent 2 (SQA). Menerapkan koreksi ke blueprint...")
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

        print("[Agent 1 - Inspector] Koreksi diterapkan; blueprint dikirim kembali ke Agent 2 untuk uji konsistensi.")
        return {
            "source_doc": current_report["source_doc"],
            "total_paragraphs": current_report["total_paragraphs"],
            **summarize_blueprint(paragraphs),
            "paragraphs": paragraphs,
            "sqa_iteration": current_report.get("sqa_iteration", 1) + 1,
        }
