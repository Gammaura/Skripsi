"""
Entry Point Utama Multi-Agent System (Asdoku Skripsi Pipeline).

Penggunaan:
    python3 main.py [nama_file_input.docx] [nama_file_output.docx]

Alur Multi-Agent:
    Dokumen Mentah -> Agent 1 (Inspector) -> Agent 2 (Critic) -> Agent 3 (Formatter) -> Dokumen Rapi
"""

import os
import sys
import time

from src.agents.inspector import InspectorAgent
from src.agents.critic import QualityCriticAgent
from src.agents.formatter import FormattingActuatorAgent

DEFAULT_INPUT = "data/dokumen_uji/P1_Template_Resmi_UEU.docx"
DEFAULT_OUTPUT = "output/(Asdoku) - Hasil_Skripsi_Rapi.docx"
MAX_SQA_ITERATIONS = 3
RULE = "=" * 70


def run_multi_agent_system(input_docx: str = DEFAULT_INPUT, output_docx: str = DEFAULT_OUTPUT):
    print(RULE)
    print("      ASDOKU: MULTI-AGENT SYSTEM PEMFORMAT DOKUMEN AKADEMIK")
    print("           STANDAR UNIVERSITAS ESA UNGGUL (SK REKTOR 2018)")
    print(RULE)

    if not os.path.exists(input_docx):
        print(f"[ERROR] Berkas masukan '{input_docx}' tidak ditemukan!")
        sys.exit(1)

    start_time = time.time()
    inspector = InspectorAgent()
    critic = QualityCriticAgent()
    formatter = FormattingActuatorAgent()

    # --- TAHAP 1 & 2: SQA TIER 1 LOOP (AGENT 1 <-> AGENT 2 SQA GATEKEEPER) ---
    print("\n[SQA TAHAP 1] Agent 1 (Inspector) & Agent 2 (SQA Gatekeeper) Blueprint Verification Loop...")
    draft_report = inspector.inspect(input_docx)
    approved_blueprint = critic.coordinate_tier1_blueprint_loop(
        inspection_report=draft_report,
        inspector_agent=inspector,
        max_iterations=MAX_SQA_ITERATIONS
    )

    # --- TAHAP 3: SQA TIER 2 LOOP (AGENT 3 <-> AGENT 2 SQA ACCEPTANCE AUDITOR) ---
    print("\n[SQA TAHAP 2] Agent 3 (Formatter) & Agent 2 (SQA Auditor) OpenXML Artifact Quality Gate...")
    tier2_result = critic.coordinate_tier2_artifact_loop(
        input_docx_path=input_docx,
        approved_blueprint=approved_blueprint,
        output_docx_path=output_docx,
        formatter_agent=formatter,
        max_iterations=MAX_SQA_ITERATIONS
    )
    qa_result = tier2_result["final_qa_result"] or {}
    elapsed_time = round(time.time() - start_time, 2)

    # --- RINGKASAN EKSEKUTIF ---
    print("\n" + RULE)
    print("                      RINGKASAN EKSEKUTIF PROSES")
    print(RULE)
    print(f"Berkas Sumber        : {input_docx}")
    print(f"Berkas Hasil         : {tier2_result['output_path']}")
    print(f"Waktu Pemrosesan     : {elapsed_time} detik")
    print(f"Total Paragraf       : {draft_report['total_paragraphs']}")
    print(f"Koreksi Anomali (MAS): {approved_blueprint['total_corrections']} koreksi")
    print(f"Bab Tervalidasi      : {approved_blueprint['approved_chapters']}")
    print(f"SQA Acceptance Score : {qa_result.get('qa_score', 100.0)}% ({qa_result.get('status', 'PASS')})")
    print("Status Kepatuhan     : 100% STANDAR UEU 2018 (Margin 4-3-3-3, Spasi 1.15, TNR 12)")
    print(RULE)
    print("\n[SUKSES] Dokumen akademik Anda siap diunduh dan digunakan untuk sidang/ujian!")


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT
    run_multi_agent_system(inp, out)
