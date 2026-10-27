"""
Modul Pelatihan Machine Learning (Training Pipeline & Model Evaluation).

Tahap 3 Metodologi Skripsi:
Modul ini bertugas:
1. Membaca dataset dari data/dataset_skripsi.csv.
2. Mengekstraksi fitur gabungan (Hybrid):
   - Fitur Teks: TF-IDF (N-gram 1-2).
   - Fitur Metadata: Font size, bold, italic, uppercase ratio, alignment, numPr, drawing, page break, posisi dokumen.
3. Melatih model klasifikasi (Logistic Regression & Random Forest).
4. Menghasilkan metrik evaluasi lengkap (Precision, Recall, F1-Score, Confusion Matrix).
5. Mengekspor model terlatih ke models/baseline_model.joblib dan pipeline ke models/feature_pipeline.joblib.
"""

import os
from typing import Any, Dict

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from src.features import DocumentFeaturePipeline

MODEL_PATH = "models/baseline_model.joblib"
PIPELINE_PATH = "models/feature_pipeline.joblib"
REPORT_PATH = "output/eval_report_expanded.md"
MAX_TFIDF_FEATURES = 400
TEST_SIZE = 0.2
RANDOM_STATE = 42
_SUMMARY_ROWS = (("macro avg", "Rata-rata Macro"), ("weighted avg", "Rata-rata Weighted"))


def prepare_features(df: pd.DataFrame):
    """Fit pipeline fitur lalu bagi 80/20 (stratified bila tiap kelas >= 2 sampel).

    Returns: (pipeline, X_train, X_test, y_train, y_test)
    """
    y = df["label"].values
    pipeline = DocumentFeaturePipeline(max_tfidf_features=MAX_TFIDF_FEATURES)
    X = pipeline.fit_transform(df)
    can_stratify = df["label"].value_counts().min() >= 2
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y if can_stratify else None
    )
    return pipeline, X_train, X_test, y_train, y_test


def save_artifacts(model, pipeline: DocumentFeaturePipeline) -> None:
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(pipeline, PIPELINE_PATH)


def _markdown_report(name: str, acc: float, rep: Dict[str, Any]) -> str:
    """Tabel Markdown metrik per kelas untuk naskah skripsi (Bab 4)."""
    lines = [
        f"### Hasil Pengujian Model: {name}\n",
        f"**Akurasi Keseluruhan:** `{acc * 100:.2f}%`\n",
        "| Kelas Struktur Dokumen | Precision | Recall | F1-Score | Jumlah Data Uji (Support) |",
        "|---|---|---|---|---|",
    ]
    for label, m in rep.items():
        if label in ("accuracy", "macro avg", "weighted avg"):
            continue
        lines.append(f"| `{label:<20}` | {m['precision']:.4f} | {m['recall']:.4f} | **{m['f1-score']:.4f}** | {int(m['support'])} |")
    for key, title in _SUMMARY_ROWS:
        m = rep[key]
        lines.append(f"| **{title}** | {m['precision']:.4f} | {m['recall']:.4f} | **{m['f1-score']:.4f}** | {int(m['support'])} |")
    return "\n".join(lines) + "\n\n"


def train_and_evaluate(dataset_csv: str = "data/dataset_skripsi.csv"):
    print(f"=== MEMULAI PELATIHAN MODEL MACHINE LEARNING DARI: {dataset_csv} ===")
    df = pd.read_csv(dataset_csv)
    print(f"[*] Jumlah sampel data termuat: {len(df)} baris")

    pipeline, X_train, X_test, y_train, y_test = prepare_features(df)
    print(f"[*] Dimensi matriks fitur gabungan: {X_train.shape[0] + X_test.shape[0]} sampel x {X_train.shape[1]} fitur")
    print(f"[*] Pembagian data: {X_train.shape[0]} data latih (Train), {X_test.shape[0]} data uji (Test)\n")

    # Penanganan ketimpangan data: class_weight='balanced'
    models = {
        "Logistic Regression (Balanced)": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, C=1.0, class_weight="balanced"),
        "Random Forest (Balanced)": RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, max_depth=14, class_weight="balanced"),
    }

    best_name, best_acc, best_model = None, -1.0, None
    reports_md = []
    for name, clf in models.items():
        print(f"--- MELATIH MODEL: {name} ---")
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"-> Akurasi Keseluruhan: {acc * 100:.2f}%\n")
        print(classification_report(y_test, y_pred, zero_division=0))
        rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        reports_md.append(_markdown_report(name, acc, rep))
        if acc > best_acc:
            best_name, best_acc, best_model = name, acc, clf

    save_artifacts(best_model, pipeline)
    print(f"[SUKSES] Model terbaik ({best_name} - {best_acc * 100:.2f}%) tersimpan di: {MODEL_PATH}")
    print(f"[SUKSES] Pipeline fitur tersimpan di: {PIPELINE_PATH}")

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Laporan Evaluasi Model Klasifikasi Struktur Dokumen (Setelah Ekspansi Dataset)\n\n")
        f.write("**Tanggal Pengujian:** 13 Oktober 2026\n")
        f.write(f"**Jumlah Dataset:** {len(df)} Paragraf (4 Dokumen: 80% Train, 20% Test)\n")
        f.write("**Fitur:** TF-IDF (N-gram 1-2) + Tipografi OpenXML\n\n---\n\n")
        f.write("\n".join(reports_md))
    print(f"[SUKSES] Laporan evaluasi ilmiah Bab 4 tersimpan di: {REPORT_PATH}")


if __name__ == "__main__":
    train_and_evaluate()
