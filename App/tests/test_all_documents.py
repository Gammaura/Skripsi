"""
Test Suite Pengujian Otomatis Sistem Multi-Agent (MAS) Asdoku
Menguji 4 Dokumen Uji Resmi (P1-P3, P5; P4 laporan magang dikeluarkan karena di luar lingkup TA) dari data/dokumen_uji/
"""

import os
import sys
import time

from docx import Document
from docx.oxml.ns import qn

# Pastikan root workspace masuk ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.inspector import InspectorAgent  # noqa: E402
from src.agents.critic import QualityCriticAgent  # noqa: E402
from src.agents.formatter import FormattingActuatorAgent  # noqa: E402
from src.ooxml.numbering import _LVL_ORDER  # noqa: E402
from src.ooxml.tables import _TBLPR_ORDER, _TCPR_ORDER  # noqa: E402
from src.ooxml.xml import _PPR_ORDER, _PPR_UNKNOWN_POS  # noqa: E402

INPUT_DIR = "data/dokumen_uji"
OUTPUT_DIR = "output/pengujian"
TEST_DOCS = [
    ("P1", "P1_Template_Resmi_UEU.docx", "Template Resmi Tugas Akhir UEU"),
    ("P2", "P2_Skripsi_Mbkm_Dhicky.docx", "Skripsi MBKM Mandiri Dhicky"),
    ("P3", "P3_Proposal_Bab1_3_PBB.docx", "Naskah Proposal Bab I-III"),
    ("P5", "P5_Buku_TA_Landscape.docx", "Template Buku TA Section Landscape"),
]
RULE = "=" * 75
MAX_SQA_ITERATIONS = 3


def _ooxml_structure_issues(path: str) -> list:
    """Kesalahan struktur yang lolos uji SQA tetapi membuat Word membuang penomoran
    (terverifikasi di Microsoft Word): urutan anak w:pPr / w:lvl dan w:lvlRestart."""
    doc = Document(path)
    issues = []
    for pPr in doc.element.body.iter(qn("w:pPr")):
        ranks = [_PPR_ORDER.get(child.tag, _PPR_UNKNOWN_POS) for child in pPr]
        if ranks != sorted(ranks):
            issues.append("urutan w:pPr tidak sesuai skema")
            break
    for lvl in doc.part.numbering_part.element.iter(qn("w:lvl")):
        ranks = [_LVL_ORDER.get(child.tag, len(_LVL_ORDER)) for child in lvl]
        if ranks != sorted(ranks):
            issues.append("urutan w:lvl tidak sesuai skema")
            break
    if any(lvl.find(qn("w:lvlRestart")) is not None and lvl.find(qn("w:pStyle")) is not None
           and lvl.find(qn("w:pStyle")).get(qn("w:val")).startswith("Heading")
           for lvl in doc.part.numbering_part.element.iter(qn("w:lvl"))):
        issues.append("w:lvlRestart pada level heading (nomor sub-bab hilang di Word)")
    for tag, order in (("w:tblPr", _TBLPR_ORDER), ("w:tcPr", _TCPR_ORDER)):
        rank = {qn(f"w:{name}"): i for i, name in enumerate(order)}
        if any([rank.get(c.tag, len(order)) for c in el] != sorted(rank.get(c.tag, len(order)) for c in el)
               for el in doc.element.body.iter(qn(tag))):
            issues.append(f"urutan {tag} tidak sesuai skema (Word dapat menolak membuka berkas)")
    rels = doc.part.rels
    r_id = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    r_embed = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
    blip = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
    wrong_rel = [el.get(r_id) for el in doc.element.body.iter(qn("w:hyperlink"))
                 if el.get(r_id) and (el.get(r_id) not in rels or not rels[el.get(r_id)].reltype.endswith("/hyperlink"))]
    wrong_rel += [el.get(r_embed) for el in doc.element.body.iter(blip)
                  if el.get(r_embed) and (el.get(r_embed) not in rels or not rels[el.get(r_embed)].reltype.endswith("/image"))]
    if wrong_rel:
        issues.append(f"rujukan relasi salah sasaran (Word menolak membuka berkas): {sorted(set(wrong_rel))}")
    defined = {style.style_id for style in doc.styles}
    undefined = {ref.get(qn("w:val")) for ref in doc.element.body.iter(qn("w:pStyle"), qn("w:rStyle"), qn("w:tblStyle"))
                 if ref.get(qn("w:val")) not in defined}
    if undefined:
        issues.append(f"rujukan style tidak terdefinisi: {sorted(undefined)}")
    has_toc_title = any(p.text.strip().upper() == "DAFTAR ISI" for p in doc.paragraphs)
    # Daftar Isi dinamis: field TOC berbasis heading (\\o outline atau \\t daftar style), bukan daftar caption (\\c)
    has_toc_field = any((it.text or "").strip().startswith("TOC") and "\\c" not in (it.text or "")
                        for it in doc.element.body.iter(qn("w:instrText")))
    if has_toc_title and not has_toc_field:
        issues.append("Daftar Isi berupa teks statis (tanpa field TOC), tidak dapat diperbarui Word")
    return issues


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
        "defects": qa["defects"] + _ooxml_structure_issues(res_file),
        "status": "PASS" if _is_valid_docx(res_file) and qa["passed"] and not _ooxml_structure_issues(res_file) else "FAIL",
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
