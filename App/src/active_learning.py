"""
MODUL ACTIVE LEARNING & AUTOMATED FEEDBACK LOOP
Multi-Agent Continuous Self-Improvement System.

Mekanisme:
1. Menangkap seluruh anomali / salah prediksi Agent 1 yang dikoreksi oleh Agent 2.
2. Menyimpan data paragraf beserta fitur OpenXML dan label kebenaran (ground truth) ke data/active_learning_feedback.csv.
3. Melakukan Continuous Retraining secara on-the-fly untuk meng-update model Machine Learning Agent 1.
4. Memberikan feedback langsung ke memori runtime InspectorAgent (hot-reload).
"""

import os
from typing import Any, Dict, List

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

from src.train import prepare_features, save_artifacts

IS_VERCEL = bool(os.environ.get("VERCEL"))
FEEDBACK_CSV = "/tmp/active_learning_feedback.csv" if IS_VERCEL else "data/active_learning_feedback.csv"
BASE_DATASET_CSV = "data/dataset_skripsi.csv"
FEEDBACK_WEIGHT = 3  # sampel koreksi disalin 3x agar model benar-benar belajar darinya

# Fitur mentah beserta nilai default bila tidak tersedia; urutan = kolom CSV.
_FEATURE_DEFAULTS = {
    "style": "Normal",
    "char_len": None,  # default: panjang teks
    "word_count": None,  # default: jumlah kata
    "font_size": 12.0,
    "is_bold": False,
    "is_italic": False,
    "align": "JUSTIFY",
    "has_num": False,
    "has_img": False,
    "has_pgbrk": False,
    "space_before": 0.0,
    "space_after": 0.0,
    "line_spacing": 1.15,
    "first_line_indent": 0.0,
    "left_indent": 0.0,
    "uppercase_ratio": 0.0,
    "doc_pos": 0.0,
}
FEEDBACK_COLUMNS = ["doc_id", "para_id", "text", *_FEATURE_DEFAULTS, "label"]


def _read_csv_or_empty(path: str) -> pd.DataFrame:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return pd.read_csv(path)
    return pd.DataFrame()


def _dedup_key(text: Any, label: Any) -> tuple:
    return str(text).strip().lower(), str(label)


def _feedback_row(doc_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
    raw = item.get("raw_features", {})
    text = item.get("text", "")
    computed = {"char_len": len(text), "word_count": len(text.split())}
    row = {"doc_id": f"FEEDBACK_{doc_name}", "para_id": item.get("para_id", 0), "text": text}
    for col, default in _FEATURE_DEFAULTS.items():
        row[col] = raw.get(col, computed.get(col, default))
    row["label"] = item.get("approved_label", "BODY_PARAGRAPH")
    return row


class ActiveLearningManager:
    """Mengelola siklus umpan balik (Feedback Loop) antara Agent 2 (Critic) dan Agent 1 (Inspector)."""

    def __init__(self, feedback_path: str = FEEDBACK_CSV, base_dataset_path: str = BASE_DATASET_CSV):
        self.feedback_path = feedback_path
        self.base_dataset_path = base_dataset_path
        os.makedirs(os.path.dirname(self.feedback_path), exist_ok=True)
        if not os.path.exists(self.feedback_path):
            pd.DataFrame(columns=FEEDBACK_COLUMNS).to_csv(self.feedback_path, index=False)

    def record_corrections(self, source_doc: str, corrected_items: List[Dict[str, Any]]) -> int:
        """Menyimpan paragraf terkoreksi ke pool feedback; pasangan (teks, label) yang sama tidak diduplikasi."""
        if not corrected_items:
            return 0

        df_existing = _read_csv_or_empty(self.feedback_path)
        existing_keys = set()
        if {"text", "label"}.issubset(df_existing.columns):
            existing_keys = {_dedup_key(t, lbl) for t, lbl in zip(df_existing["text"], df_existing["label"], strict=True)}

        doc_name = os.path.basename(source_doc)
        new_rows = []
        for item in corrected_items:
            row = _feedback_row(doc_name, item)
            key = _dedup_key(row["text"], row["label"])
            if key not in existing_keys:
                existing_keys.add(key)
                new_rows.append(row)

        if not new_rows:
            return 0
        df_new = pd.DataFrame(new_rows)
        df_all = df_new if df_existing.empty else pd.concat([df_existing, df_new], ignore_index=True)
        df_all.to_csv(self.feedback_path, index=False)
        print(f"[Active Learning] Berhasil menyimpan {len(new_rows)} sampel koreksi baru ke: {self.feedback_path}")
        return len(new_rows)

    def record_manual_correction(self, idx: int, text: str, correct_label: str) -> int:
        """Menyimpan koreksi label manual dari pengguna (endpoint /api/active-learning/feedback)."""
        item = {"para_id": idx, "text": text, "approved_label": correct_label}
        return self.record_corrections("MANUAL", [item])

    def get_stats(self) -> Dict[str, Any]:
        """Statistik sampel koreksi yang terkumpul di pool feedback."""
        df = _read_csv_or_empty(self.feedback_path)
        dist = df["label"].value_counts().to_dict() if "label" in df.columns else {}
        return {"total_feedback": len(df), "class_distribution": dist}

    def retrain_agent_1(self) -> Dict[str, Any]:
        """Melatih ulang model Agent 1 dengan dataset utama + seluruh sampel koreksi (berbobot)."""
        print("\n[Active Learning Retraining] Memulai proses Continuous Retraining untuk Agent 1...")
        df_base = pd.read_csv(self.base_dataset_path)
        df_fb = _read_csv_or_empty(self.feedback_path)

        if df_fb.empty:
            df_train_all = df_base
            print(f"[Active Learning] Melatih ulang pada {len(df_base)} sampel basis...")
        else:
            df_fb_weighted = pd.concat([df_fb] * FEEDBACK_WEIGHT, ignore_index=True)
            df_train_all = pd.concat([df_base, df_fb_weighted], ignore_index=True)
            print(f"[Active Learning] Menggabungkan {len(df_base)} sampel basis + {len(df_fb)} sampel feedback (weighted {FEEDBACK_WEIGHT}x = {len(df_fb_weighted)})")

        pipeline, X_train, X_test, y_train, y_test = prepare_features(df_train_all)
        clf = RandomForestClassifier(n_estimators=120, random_state=42, max_depth=16, class_weight="balanced")
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        new_acc = accuracy_score(y_test, y_pred)
        rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        save_artifacts(clf, pipeline)
        print(f"[Active Learning] Retraining SELESAI! Akurasi Model Baru: {new_acc * 100:.2f}%")

        return {
            "status": "success",
            "new_accuracy": round(new_acc * 100, 2),
            "macro_f1": round(rep["macro avg"]["f1-score"], 4),
            "weighted_f1": round(rep["weighted avg"]["f1-score"], 4),
            "total_training_samples": len(df_train_all),
            "feedback_samples_used": len(df_fb),
        }
