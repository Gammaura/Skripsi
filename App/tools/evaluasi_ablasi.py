"""Uji ablasi deteksi struktur (rumusan masalah 3 proposal).

Membandingkan tiga konfigurasi pada naskah uji yang sama terhadap label manual:
  (a) Agen 1 saja        : prediksi model machine learning (Inspector) tanpa koreksi.
  (b) Aturan Agen 2 saja : Quality Critic dijalankan tanpa masukan model (prediksi ML dikosongkan).
  (c) Sistem multi-agen  : alur produksi (Agen 1 -> putaran umpan balik Agen 2).

Label keluaran Agen 2 dipetakan ke 9 kelas yang sama dengan label manual: paragraf BODY yang ditandai
Agen 2 sebagai bagian daftar pustaka (metadata is_bibliography) dihitung sebagai DAFTAR_PUSTAKA_ITEM,
karena Formatter memperlakukannya sebagai entri daftar pustaka.

Penggunaan (dari folder App/):
  python3 tools/evaluasi_ablasi.py            # naskah uji asli + versi heading polos
Hasil: output/eval_ablasi.md
"""
import contextlib
import io
import os
import sys
from collections import defaultdict
from datetime import date

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.academic_rules import LABEL_BIBLIOGRAPHY, LABEL_BODY  # noqa: E402
from src.agents.critic import QualityCriticAgent  # noqa: E402
from src.agents.inspector import InspectorAgent  # noqa: E402

CORPUS = "data/corpus"
REPORT_PATH = "output/eval_ablasi.md"
SETS = (("uji", "Naskah asli"), ("uji_polos", "Naskah heading polos"))
CONFIGS = ("(a) Agen 1 saja", "(b) Aturan Agen 2 saja", "(c) Sistem multi-agen")


class _NoFeedback:
    """Pengganti pool Active Learning: evaluasi tidak boleh menulis naskah uji ke data latih."""

    def record_corrections(self, *_args, **_kwargs) -> int:
        return 0


def _critic_labels(paragraphs) -> dict:
    out = {}
    for p in paragraphs:
        label = p["approved_label"]
        if label == LABEL_BODY and p.get("metadata", {}).get("is_bibliography"):
            label = LABEL_BIBLIOGRAPHY
        out[p["para_id"]] = label
    return out


def _run_document(path: str, inspector, critic) -> dict:
    with contextlib.redirect_stdout(io.StringIO()):
        report = inspector.inspect(path)
        ml = {p["para_id"]: p["predicted_label"] for p in report["paragraphs"]}

        rules_only = {**report, "paragraphs": [
            {**p, "predicted_label": LABEL_BODY, "confidence": 0.0, "is_ambiguous": False,
             "metadata": dict(p["metadata"])} for p in report["paragraphs"]]}
        rules = _critic_labels(critic.evaluate_and_refine(rules_only)["paragraphs"])

        full = critic.coordinate_tier1_blueprint_loop(inspector.inspect(path), inspector, 3)
        mas = _critic_labels(full["paragraphs"])
    return dict(zip(CONFIGS, (ml, rules, mas)))


def main() -> None:
    inspector, critic = InspectorAgent(), QualityCriticAgent(active_learning=_NoFeedback())
    rows, per_class = [], {}
    for folder, title in SETS:
        csv_path = os.path.join(CORPUS, f"dataset_{folder}.csv")
        if not os.path.exists(csv_path):
            continue
        truth = pd.read_csv(csv_path)
        y_true, y_pred = [], defaultdict(list)
        for name in sorted(os.listdir(os.path.join(CORPUS, folder))):
            doc_truth = truth[truth["doc_id"].str.endswith(os.path.splitext(name)[0] + ("_POLOS" if "polos" in folder else ""))]
            preds = _run_document(os.path.join(CORPUS, folder, name), inspector, critic)
            labels = dict(zip(doc_truth["para_id"], doc_truth["label"]))
            ids = sorted(labels)
            y_true += [labels[i] for i in ids]
            for config in CONFIGS:
                y_pred[config] += [preds[config][i] for i in ids]
                doc_pred = [preds[config][i] for i in ids]
                doc_true = [labels[i] for i in ids]
                rows.append((title, name, config, accuracy_score(doc_true, doc_pred),
                             f1_score(doc_true, doc_pred, average="macro", zero_division=0)))
            print(f"[ok] {folder}/{name}")
        for config in CONFIGS:
            rows.append((title, "GABUNGAN", config, accuracy_score(y_true, y_pred[config]),
                         f1_score(y_true, y_pred[config], average="macro", zero_division=0)))
            per_class[(title, config)] = classification_report(y_true, y_pred[config], output_dict=True, zero_division=0)

    df = pd.DataFrame(rows, columns=["set", "naskah", "konfigurasi", "akurasi", "macro_f1"])
    print(df[df["naskah"] == "GABUNGAN"].to_string(index=False))

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Uji Ablasi Deteksi Struktur\n\n")
        f.write(f"**Tanggal:** {date.today():%d-%m-%Y}  \n**Data:** naskah uji (tidak dipakai melatih model)  \n")
        f.write("**Pembanding:** label manual per paragraf (9 kelas)\n\n")
        f.write("| Set | Naskah | Konfigurasi | Akurasi (%) | Macro-F1 (%) |\n|---|---|---|---|---|\n")
        for r in df.itertuples():
            f.write(f"| {r.set} | {r.naskah} | {r.konfigurasi} | {r.akurasi * 100:.2f} | {r.macro_f1 * 100:.2f} |\n")
        f.write("\n## F1 per Kelas (gabungan naskah uji)\n\n")
        for _, title in SETS:
            reports = {c: per_class.get((title, c)) for c in CONFIGS}
            if not all(reports.values()):
                continue
            classes = [k for k in reports[CONFIGS[0]] if k not in ("accuracy", "macro avg", "weighted avg")]
            f.write(f"### {title}\n\n| Kelas | " + " | ".join(CONFIGS) + " |\n|---|" + "---|" * len(CONFIGS) + "\n")
            for cls in classes:
                f.write(f"| `{cls}` | " + " | ".join(f"{reports[c].get(cls, {}).get('f1-score', 0):.3f}" for c in CONFIGS) + " |\n")
            f.write("\n")
    print(f"[SUKSES] Laporan ablasi: {REPORT_PATH}")


if __name__ == "__main__":
    main()
