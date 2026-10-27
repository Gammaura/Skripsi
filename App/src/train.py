"""
Modul Pelatihan Machine Learning (Training Pipeline & Model Evaluation).

Tahap 3 Metodologi Skripsi:
Modul ini bertugas:
1. Membaca dataset dari data/dataset_skripsi.csv.
2. Mengekstraksi fitur gabungan (Hybrid):
   - Fitur Teks: TF-IDF (N-gram 1-2).
   - Fitur Metadata: Font size, bold, italic, uppercase ratio, alignment, numPr, drawing, page break, posisi dokumen.
3. Membandingkan 3 model klasifikasi (Logistic Regression, Random Forest, XGBoost) dengan 3 protokol evaluasi:
   A. Split acak 80/20 berulang (beberapa seed) -> rata-rata ± simpangan baku.
   B. Split acak 80/20 setelah deduplikasi teks+label -> tanpa kebocoran paragraf kembar.
   C. Leave-One-Document-Out (LODO) -> generalisasi ke dokumen yang belum pernah dilihat.
4. Menghasilkan metrik evaluasi lengkap (Precision, Recall, F1-Score per kelas) dalam laporan Markdown Bab 4.
5. Memilih model produksi berdasarkan macro-F1 LODO tertinggi, melatih ulang pada seluruh data, lalu
   mengekspor model ke models/baseline_model.joblib dan pipeline ke models/feature_pipeline.joblib.
"""

import os
from dataclasses import dataclass
from datetime import date
from typing import Dict, List

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

from src.classifiers import candidate_models
from src.features import DocumentFeaturePipeline

MODEL_PATH = "models/baseline_model.joblib"
PIPELINE_PATH = "models/feature_pipeline.joblib"
REPORT_PATH = "output/eval_report_expanded.md"
MAX_TFIDF_FEATURES = 400
TEST_SIZE = 0.2
RANDOM_STATE = 42
EVAL_SEEDS = range(10)

PROTOCOL_RANDOM = "A. Split Acak 80/20"
PROTOCOL_DEDUP = "B. Split Acak 80/20 (Deduplikasi)"
PROTOCOL_LODO = "C. Leave-One-Document-Out"


@dataclass
class FoldScore:
    protocol: str
    model: str
    fold: str
    accuracy: float
    macro_f1: float


def _stratify_target(df: pd.DataFrame):
    """Label untuk stratifikasi, atau None bila ada kelas dengan < 2 sampel."""
    return df["label"] if df["label"].value_counts().min() >= 2 else None


def prepare_features(df: pd.DataFrame, seed: int = RANDOM_STATE):
    """Split 80/20 lalu fit pipeline fitur HANYA pada data latih (tanpa kebocoran TF-IDF).

    Returns: (pipeline, X_train, X_test, y_train, y_test)
    """
    train_df, test_df = train_test_split(df, test_size=TEST_SIZE, random_state=seed, stratify=_stratify_target(df))
    pipeline = DocumentFeaturePipeline(max_tfidf_features=MAX_TFIDF_FEATURES)
    X_train = pipeline.fit_transform(train_df)
    X_test = pipeline.transform(test_df)
    return pipeline, X_train, X_test, train_df["label"].values, test_df["label"].values


def save_artifacts(model, pipeline: DocumentFeaturePipeline) -> None:
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(pipeline, PIPELINE_PATH)


def _deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Buang paragraf kembar (teks+label sama) dan kelas yang tinggal < 2 sampel."""
    unique = df.drop_duplicates(subset=["text", "label"])
    counts = unique["label"].value_counts()
    return unique[unique["label"].isin(counts[counts >= 2].index)]


def _evaluate_random_splits(df: pd.DataFrame, protocol: str) -> List[FoldScore]:
    scores = []
    for seed in EVAL_SEEDS:
        _, X_train, X_test, y_train, y_test = prepare_features(df, seed)
        for name, model in candidate_models(seed).items():
            y_pred = model.fit(X_train, y_train).predict(X_test)
            scores.append(FoldScore(protocol, name, f"seed={seed}", accuracy_score(y_test, y_pred),
                                    f1_score(y_test, y_pred, average="macro", zero_division=0)))
    return scores


def _evaluate_lodo(df: pd.DataFrame):
    """LODO: tiap dokumen bergiliran jadi data uji. Juga mengumpulkan prediksi gabungan per model."""
    scores, pooled = [], {name: ([], []) for name in candidate_models()}
    for doc_id in df["doc_id"].unique():
        train_df, test_df = df[df["doc_id"] != doc_id], df[df["doc_id"] == doc_id]
        pipeline = DocumentFeaturePipeline(max_tfidf_features=MAX_TFIDF_FEATURES)
        X_train, X_test = pipeline.fit_transform(train_df), pipeline.transform(test_df)
        y_test = test_df["label"].values
        for name, model in candidate_models(RANDOM_STATE).items():
            y_pred = model.fit(X_train, train_df["label"].values).predict(X_test)
            scores.append(FoldScore(PROTOCOL_LODO, name, doc_id, accuracy_score(y_test, y_pred),
                                    f1_score(y_test, y_pred, average="macro", zero_division=0)))
            pooled[name][0].extend(y_test)
            pooled[name][1].extend(y_pred)
    return scores, pooled


def _pct(mean: float, std: float) -> str:
    return f"{mean * 100:.2f} ± {std * 100:.2f}"


def _summary_table(scores: pd.DataFrame) -> str:
    lines = ["| Protokol | Model | Akurasi (%) | Macro-F1 (%) |", "|---|---|---|---|"]
    grouped = scores.groupby(["protocol", "model"], sort=False)
    for (protocol, model), g in grouped:
        lines.append(f"| {protocol} | {model} | {_pct(g.accuracy.mean(), g.accuracy.std())} | {_pct(g.macro_f1.mean(), g.macro_f1.std())} |")
    return "\n".join(lines)


def _lodo_table(scores: pd.DataFrame, models: List[str]) -> str:
    lodo = scores[scores["protocol"] == PROTOCOL_LODO]
    header = "| Dokumen Uji | " + " | ".join(f"{m} Acc / F1" for m in models) + " |"
    lines = [header, "|---|" + "---|" * len(models)]
    for doc_id, g in lodo.groupby("fold", sort=False):
        cells = [f"{r.accuracy * 100:.1f} / {r.macro_f1 * 100:.1f}" for m in models for r in g[g.model == m].itertuples()]
        lines.append(f"| `{doc_id}` | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _class_report_table(y_true, y_pred) -> str:
    rep = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    lines = ["| Kelas Struktur Dokumen | Precision | Recall | F1-Score | Support |", "|---|---|---|---|---|"]
    for label, m in rep.items():
        if isinstance(m, dict):
            name = {"macro avg": "**Rata-rata Macro**", "weighted avg": "**Rata-rata Weighted**"}.get(label, f"`{label}`")
            lines.append(f"| {name} | {m['precision']:.4f} | {m['recall']:.4f} | **{m['f1-score']:.4f}** | {int(m['support'])} |")
    return "\n".join(lines)


def _write_report(df: pd.DataFrame, n_unique: int, scores: pd.DataFrame, pooled: Dict, best: str) -> None:
    models = list(candidate_models())
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Laporan Evaluasi Model Klasifikasi Struktur Dokumen\n\n")
        f.write(f"**Tanggal Pengujian:** {date.today():%d-%m-%Y}\n")
        f.write(f"**Jumlah Dataset:** {len(df)} paragraf ({n_unique} unik) dari {df['doc_id'].nunique()} dokumen, "
                f"{df['label'].nunique()} kelas\n")
        f.write("**Fitur:** TF-IDF (N-gram 1-2) + Tipografi OpenXML\n")
        f.write(f"**Model:** {', '.join(models)}\n\n---\n\n")
        f.write("## 1. Ringkasan Perbandingan Model\n\n")
        f.write(f"Protokol A dan B diulang dengan {len(EVAL_SEEDS)} seed berbeda; nilai = rata-rata ± simpangan baku. "
                "Protokol C menguji setiap dokumen sebagai data uji secara bergiliran.\n\n")
        f.write(_summary_table(scores) + "\n\n")
        f.write("## 2. Generalisasi ke Dokumen Baru (Leave-One-Document-Out)\n\n")
        f.write(_lodo_table(scores, models) + "\n\n")
        f.write(f"## 3. Metrik per Kelas Model Terpilih: {best} (prediksi gabungan LODO)\n\n")
        f.write(_class_report_table(*pooled[best]) + "\n\n")
        f.write("## 4. Pemilihan Model Produksi\n\n")
        f.write(f"Model produksi dipilih berdasarkan macro-F1 rata-rata tertinggi pada protokol LODO, karena "
                f"skenario tersebut paling mendekati penggunaan nyata (dokumen mahasiswa yang belum pernah dilihat). "
                f"Model terpilih: **{best}**, kemudian dilatih ulang pada seluruh {len(df)} paragraf.\n")
        f.write(_limitations_section(df))


def _limitations_section(df: pd.DataFrame) -> str:
    """Catatan keterbatasan: kelas yang hanya ada di satu dokumen tidak dapat dipelajari saat dokumen itu diuji (LODO)."""
    docs_per_class = df.groupby("label")["doc_id"].unique()
    single = {label: docs[0] for label, docs in docs_per_class.items() if len(docs) == 1}
    if not single:
        return ""
    rows = "\n".join(f"| `{label}` | `{doc}` |" for label, doc in sorted(single.items()))
    return (
        "\n## 5. Keterbatasan Dataset\n\n"
        "Kelas berikut hanya muncul pada satu dokumen, sehingga pada protokol LODO model tidak pernah melihat "
        "contohnya saat dokumen tersebut diuji (F1 kelas = 0). Penambahan dokumen latih yang memuat kelas ini "
        "akan berdampak lebih besar daripada penggantian algoritma.\n\n"
        f"| Kelas | Satu-satunya Dokumen |\n|---|---|\n{rows}\n"
    )


def train_and_evaluate(dataset_csv: str = "data/dataset_skripsi.csv"):
    print(f"=== MEMULAI PELATIHAN & EVALUASI MODEL DARI: {dataset_csv} ===")
    df = pd.read_csv(dataset_csv)
    unique_df = _deduplicate(df)
    print(f"[*] Dataset: {len(df)} baris ({len(unique_df)} unik), {df['doc_id'].nunique()} dokumen")

    print(f"[*] Protokol A: split acak 80/20 x {len(EVAL_SEEDS)} seed...")
    scores = _evaluate_random_splits(df, PROTOCOL_RANDOM)
    print(f"[*] Protokol B: split acak setelah deduplikasi x {len(EVAL_SEEDS)} seed...")
    scores += _evaluate_random_splits(unique_df, PROTOCOL_DEDUP)
    print("[*] Protokol C: Leave-One-Document-Out...")
    lodo_scores, pooled = _evaluate_lodo(df)
    scores_df = pd.DataFrame([s.__dict__ for s in scores + lodo_scores])

    lodo_f1 = scores_df[scores_df["protocol"] == PROTOCOL_LODO].groupby("model")["macro_f1"].mean()
    best = lodo_f1.idxmax()
    print("\n" + _summary_table(scores_df) + "\n")
    print(f"[*] Model terpilih (macro-F1 LODO tertinggi): {best} ({lodo_f1[best] * 100:.2f}%)")

    pipeline = DocumentFeaturePipeline(max_tfidf_features=MAX_TFIDF_FEATURES)
    X_all = pipeline.fit_transform(df)
    final_model = clone(candidate_models(RANDOM_STATE)[best]).fit(X_all, df["label"].values)
    save_artifacts(final_model, pipeline)
    print(f"[SUKSES] Model produksi tersimpan di: {MODEL_PATH} | Pipeline: {PIPELINE_PATH}")

    _write_report(df, len(unique_df), scores_df, pooled, best)
    print(f"[SUKSES] Laporan evaluasi Bab 4 tersimpan di: {REPORT_PATH}")
    return scores_df


if __name__ == "__main__":
    train_and_evaluate()
