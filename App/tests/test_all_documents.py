"""
Test Suite Pengujian Otomatis Sistem Multi-Agent (MAS) Asdoku
Menguji 5 Dokumen Uji Resmi (P1 - P5) dari data/dokumen_uji/
"""

import os
import sys
import time

from docx import Document

# Pastikan root workspace masuk ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.inspector import InspectorAgent  # noqa: E402
from src.agents.critic import QualityCriticAgent  # noqa: E402
from src.agents.formatter import FormattingActuatorAgent  # noqa: E402

INPUT_DIR = "data/dokumen_uji"
OUTPUT_DIR = "output/pengujian"
TEST_DOCS = [
    ("P1", "P1_Template_Resmi_UEU.docx", "Template Resmi Tugas Akhir UEU"),
    ("P2", "P2_Skripsi_Mbkm_Dhicky.docx", "Skripsi MBKM Mandiri Dhicky"),
    ("P3", "P3_Proposal_Bab1_3_PBB.docx", "Naskah Proposal Bab I-III"),
    ("P4", "P4_Laporan_Mbkm_Arditya.docx", "Laporan MBKM Arditya"),
    ("P5", "P5_Buku_TA_Landscape.docx", "Template Buku TA Section Landscape"),
]
RULE = "=" * 75
MAX_SQA_ITERATIONS = 3


def _is_valid_docx(path: str) -> bool:
    try:
        return len(Document(path).paragraphs) > 0
    except Exception:
        return False


def _run_document(inspector, critic, formatter, code: str, fname: str, label: str) -> dict:
    in_path = os.path.join(INPUT_DIR, fname)
    out_path = os.path.join(OUTPUT_DIR, f"(Asdoku) - {fname}")
    print(f"\n[{code}] Menguji: {label} ({fname})...")
    start = time.time()

    draft = inspector.inspect(in_path)  # 1. Inspector
    approved = critic.coordinate_tier1_blueprint_loop(draft, inspector, MAX_SQA_ITERATIONS)  # 2. SQA Tier 1
    tier2 = critic.coordinate_tier2_artifact_loop(in_path, approved, out_path, formatter, MAX_SQA_ITERATIONS)  # 3. Formatter + SQA Tier 2
    res_file, qa = tier2["output_path"], tier2["final_qa_result"]

    elapsed = round(time.time() - start, 2)
    print(f"[{code}] SELESAI ({elapsed}s) -> Disimpan ke: {res_file}")
    return {
        "code": code,
        "name": fname,
        "paras": draft["total_paragraphs"],
        "corrections": approved["total_corrections"],
        "chapters": len(approved["approved_chapters"]),
        "time": elapsed,
        "sqa": qa["qa_score"],
        "defects": qa["defects"],
        "status": "PASS" if _is_valid_docx(res_file) and qa["passed"] else "FAIL",
    }


def _print_summary(results: list) -> None:
    print("\n" + RULE)
    print("                      HASIL PENGUJIAN SELURUH DOKUMEN")
    print(RULE)
    print(f"{'Kode':<6} | {'Dokumen':<32} | {'Paragraf':<8} | {'Koreksi':<8} | {'SQA':<6} | {'Waktu':<7} | {'Status'}")
    print("-" * 85)
    for r in results:
        print(f"{r['code']:<6} | {r['name']:<32} | {r['paras']:<8} | {r['corrections']:<8} | {r['sqa']:<5}% | {r['time']:<5}s | {r['status']}")
        for defect in r["defects"]:
            print(f"{'':<6}   - {defect}")
    print(RULE)


def test_pipeline():
    print(RULE)
    print("  ASDOKU MULTI-AGENT SYSTEM (MAS) — PENGUJIAN OTOMATIS SUITE P1 S/D P5")
    print(RULE)

    agents = (InspectorAgent(), QualityCriticAgent(), FormattingActuatorAgent())
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = [_run_document(*agents, *doc) for doc in TEST_DOCS]
    _print_summary(results)

    failed = [r["code"] for r in results if r["status"] != "PASS"]
    assert not failed, f"Dokumen gagal lolos SQA: {failed}"


if __name__ == "__main__":
    test_pipeline()
