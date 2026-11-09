"""
MODUL ACTIVE LEARNING & AUTOMATED FEEDBACK LOOP
Multi-Agent Continuous Self-Improvement System.

Dua sumber label masuk ke pool feedback (data/active_learning_feedback.csv):
1. Weak supervision (AGENT2_RULE): prediksi Agent 1 yang dikoreksi aturan Agent 2. Label berasal dari
   aturan, bukan manusia, sehingga diberi bobot rendah.
2. Active Learning (MANUAL): paragraf yang membuat Agent 1 paling ragu (uncertainty sampling,
   least-confidence) dan tidak dapat dipastikan aturan Agent 2, dikonfirmasi labelnya oleh pengguna.

Retraining memakai uji non-regresi: kandidat model (basis + label manual, dan basis + label manual + weak)
dibandingkan dengan model basis pada split uji data basis yang sama. Kandidat terbaik disimpan
hanya bila macro-F1-nya tidak turun; weak label yang justru merusak kinerja otomatis tidak terpakai.
"""

import os
import threading
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from src.academic_rules import ALL_LABELS
from src.classifiers import MODEL_RF, candidate_models
from src.features import DocumentFeaturePipeline
from src.train import MAX_TFIDF_FEATURES, MODEL_PATH, RANDOM_STATE, TEST_SIZE, save_artifacts

IS_VERCEL = bool(os.environ.get("VERCEL"))
FEEDBACK_CSV = "/tmp/active_learning_feedback.csv" if IS_VERCEL else "data/active_learning_feedback.csv"
# Basis = korpus naskah TA berlabel (Fase 1). Korpus berisi data pribadi sehingga tidak ikut repo/deploy;
# bila tidak ada (mis. di Vercel), feedback tetap dikumpulkan tetapi retraining dilewati.
BASE_DATASET_CSV = "data/corpus/dataset_latih.csv"
SOURCE_WEAK = "AGENT2_RULE"
SOURCE_MANUAL = "MANUAL"
# Replikasi sampel saat retraining: label manusia lebih dipercaya daripada label aturan.
SOURCE_WEIGHTS = {SOURCE_WEAK: 1, SOURCE_MANUAL: 3}
NON_REGRESSION_TOLERANCE = 0.005  # toleransi penurunan macro-F1 pada data uji basis
_RETRAIN_LOCK = threading.Lock()

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
FEEDBACK_COLUMNS = ["doc_id", "para_id", "text", *_FEATURE_DEFAULTS, "label", "label_source"]


def _read_csv_or_empty(path: str) -> pd.DataFrame:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return pd.read_csv(path)
    return pd.DataFrame()


def _dedup_key(text: Any, label: Any) -> tuple:
    return str(text).strip().lower(), str(label)


def _production_model_template():
    """Klon tak terlatih dari model produksi (jenis & hyperparameter hasil seleksi train.py)."""
    if os.path.exists(MODEL_PATH):
        return clone(joblib.load(MODEL_PATH))
    return candidate_models()[MODEL_RF]


def _label_sources(df: pd.DataFrame) -> pd.Series:
    """Sumber label per baris; baris lama tanpa kolom label_source diturunkan dari doc_id."""
    inferred = df["doc_id"].astype(str).eq("FEEDBACK_MANUAL").map({True: SOURCE_MANUAL, False: SOURCE_WEAK})
    if "label_source" not in df.columns:
        return inferred
    return df["label_source"].fillna(inferred)


def _weighted_feedback(df_fb: pd.DataFrame, include_sources) -> pd.DataFrame:
    sources = _label_sources(df_fb)
    parts = [pd.concat([df_fb[sources == src]] * SOURCE_WEIGHTS[src], ignore_index=True) for src in include_sources]
    return pd.concat(parts, ignore_index=True)


def _candidate_feedback_sets(df_fb: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Kombinasi sumber label yang diuji; label manual selalu ikut bila ada."""
    available = set(_label_sources(df_fb))
    candidates = {}
    if SOURCE_MANUAL in available:
        candidates["manual"] = _weighted_feedback(df_fb, [SOURCE_MANUAL])
    if SOURCE_WEAK in available:
        candidates["manual+weak"] = _weighted_feedback(df_fb, [s for s in (SOURCE_MANUAL, SOURCE_WEAK) if s in available])
    return candidates


def _fit(df_train: pd.DataFrame):
    pipeline = DocumentFeaturePipeline(max_tfidf_features=MAX_TFIDF_FEATURES)
    model = _production_model_template().fit(pipeline.fit_transform(df_train), df_train["label"].values)
    return model, pipeline


def _score(model, pipeline, df_test: pd.DataFrame) -> Dict[str, float]:
    y_pred = model.predict(pipeline.transform(df_test))
    y_true = df_test["label"].values
    return {"accuracy": accuracy_score(y_true, y_pred), "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0)}


def _feedback_row(doc_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
    raw = item.get("raw_features", {})
    text = item.get("text", "")
    computed = {"char_len": len(text), "word_count": len(text.split())}
    row = {"doc_id": f"FEEDBACK_{doc_name}", "para_id": item.get("para_id", 0), "text": text}
    for col, default in _FEATURE_DEFAULTS.items():
        row[col] = raw.get(col, computed.get(col, default))
    row["label"] = item.get("approved_label", "BODY_PARAGRAPH")
    row["label_source"] = item.get("label_source", SOURCE_WEAK)
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

    def record_manual_correction(self, idx: int, text: str, correct_label: str,
                                 raw_features: Optional[Dict[str, Any]] = None) -> int:
        """Menyimpan jawaban pengguna atas kueri Active Learning (endpoint /api/active-learning/feedback).

        `raw_features` (fitur tipografi asli paragraf) dipakai bila tersedia; tanpa itu hanya teks
        yang diketahui dan fitur tipografi diisi nilai default.
        """
        if correct_label not in ALL_LABELS:
            raise ValueError(f"Label '{correct_label}' tidak dikenal.")
        item = {"para_id": idx, "text": text, "approved_label": correct_label,
                "raw_features": raw_features or {}, "label_source": SOURCE_MANUAL}
        return self.record_corrections("MANUAL", [item])

    def get_stats(self) -> Dict[str, Any]:
        """Statistik sampel koreksi yang terkumpul di pool feedback."""
        df = _read_csv_or_empty(self.feedback_path)
        dist = df["label"].value_counts().to_dict() if "label" in df.columns else {}
        sources = _label_sources(df).value_counts().to_dict() if not df.empty else {}
        return {"total_feedback": len(df), "class_distribution": dist, "label_sources": sources}

    def retrain_agent_1(self) -> Dict[str, Any]:
        """Melatih ulang model Agent 1 (basis + feedback berbobot) dengan uji non-regresi.

        Model pembanding (basis saja) dan model kandidat (basis + feedback) dilatih pada split latih
        data basis yang sama lalu diuji pada split uji basis. Catatan: label data basis = pra-label aturan
        yang dikoreksi (tools/label_excel.py), verifikasi manual penulis belum selesai. Kandidat dilatih ulang
        pada seluruh data dan disimpan hanya bila macro-F1-nya tidak lebih rendah dari pembanding.
        Pemanggilan bersamaan dilewati agar dua retraining tidak menulis model secara bersamaan.
        """
        if not _RETRAIN_LOCK.acquire(blocking=False):
            print("[Active Learning] Retraining lain sedang berjalan; permintaan ini dilewati.")
            return {"status": "skipped", "accepted": False, "reason": "Retraining lain sedang berjalan."}
        try:
            return self._retrain_with_gate()
        finally:
            _RETRAIN_LOCK.release()

    def _retrain_with_gate(self) -> Dict[str, Any]:
        print("\n[Active Learning Retraining] Memulai retraining Agent 1 dengan uji non-regresi...")
        if not os.path.exists(self.base_dataset_path):
            return {"status": "skipped", "accepted": False,
                    "reason": f"Dataset basis {self.base_dataset_path} tidak tersedia (korpus tidak ikut deploy)."}
        df_base = pd.read_csv(self.base_dataset_path)
        df_fb = _read_csv_or_empty(self.feedback_path)
        if df_fb.empty:
            return {"status": "skipped", "accepted": False, "reason": "Pool feedback masih kosong."}

        stratify = df_base["label"] if df_base["label"].value_counts().min() >= 2 else None
        base_train, base_test = train_test_split(df_base, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=stratify)

        baseline = _score(*_fit(base_train), base_test)
        print(f"[Active Learning] Uji non-regresi pada data uji basis (n={len(base_test)}): macro-F1 basis={baseline['macro_f1']:.4f}")
        scores = {}
        for name, feedback in _candidate_feedback_sets(df_fb).items():
            scores[name] = _score(*_fit(pd.concat([base_train, feedback], ignore_index=True)), base_test)
            print(f"[Active Learning]   kandidat basis+{name}: macro-F1={scores[name]['macro_f1']:.4f}")

        passing = {n: sc for n, sc in scores.items() if sc["macro_f1"] >= baseline["macro_f1"] - NON_REGRESSION_TOLERANCE}
        chosen = max(passing, key=lambda n: passing[n]["macro_f1"]) if passing else None
        if chosen:
            df_train_all = pd.concat([df_base, _candidate_feedback_sets(df_fb)[chosen]], ignore_index=True)
            save_artifacts(*_fit(df_train_all))
            print(f"[Active Learning] DITERIMA: kandidat basis+{chosen} disimpan ({len(df_train_all)} sampel latih).")
        else:
            print("[Active Learning] DITOLAK: seluruh kandidat menurunkan kinerja; model lama dipertahankan.")

        return {
            "status": "success",
            "accepted": chosen is not None,
            "chosen_candidate": chosen,
            "baseline_macro_f1": round(baseline["macro_f1"], 4),
            "candidate_macro_f1": {n: round(sc["macro_f1"], 4) for n, sc in scores.items()},
            "new_accuracy": round(passing[chosen]["accuracy"] * 100, 2) if chosen else None,
            "macro_f1": round(passing[chosen]["macro_f1"], 4) if chosen else None,
            "feedback_samples_used": len(df_fb),
            "feedback_by_source": _label_sources(df_fb).value_counts().to_dict(),
        }
