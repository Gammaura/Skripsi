"""Uji keutuhan isi: naskah sebelum vs sesudah diformat Asdoku (proposal Bab III, rumusan masalah 4).

Yang dibandingkan per dokumen:
  - jumlah gambar (DrawingML blip + VML imagedata), tabel, rumus (OMML), referensi catatan kaki/akhir,
    dan sitasi Mendeley (field ADDIN CSL_CITATION / content control MENDELEY_CITATION);
  - cakupan teks: persentase paragraf sumber (dinormalisasi) yang teksnya ditemukan di dokumen hasil.
    Normalisasi membuang awalan yang memang ditulis ulang Formatter ("BAB I", nomor sub-bab,
    awalan "Gambar/Tabel x.y"), lalu hanya membandingkan huruf dan angka.

Target proposal: tidak ada selisih (gambar/tabel/rumus/catatan/sitasi sama, cakupan teks 100%).

Penggunaan (dari folder App/):
  python3 tools/evaluasi_keutuhan.py [berkas.docx ...]   # tanpa argumen: naskah uji + dokumen uji P
Hasil: output/eval_keutuhan.md
"""
import contextlib
import glob
import io
import os
import re
import sys
import tempfile
from datetime import date

from docx import Document
from docx.oxml.ns import qn

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluasi_ablasi import _NoFeedback  # noqa: E402
from src.agents.critic import QualityCriticAgent  # noqa: E402
from src.agents.formatter import FormattingActuatorAgent  # noqa: E402
from src.agents.inspector import InspectorAgent  # noqa: E402

REPORT_PATH = "output/eval_keutuhan.md"
DEFAULT_INPUTS = sorted(glob.glob("data/corpus/uji/*.docx")) + sorted(glob.glob("data/dokumen_uji/*.docx"))
A_BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
V_IMAGEDATA = "{urn:schemas-microsoft-com:vml}imagedata"
M_OMATH = "{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath"
PREFIX_RE = re.compile(r"^(bab\s+([ivxlc]+|\d+)\b|\d+(\.\d+)+\.?|\d{1,2}[.)]|[a-z][.)]|(gambar|tabel|figure|table)\s*\d*([.\-]\d+)?\.?)\s*", re.I)
# Baris Daftar Isi/Tabel/Gambar lama: diganti Daftar Isi baru (field TOC) oleh Formatter, jadi tidak dihitung.
TOC_LINE_RE = re.compile(r"^(bab\s|\d+(\.\d+)*\s|(gambar|tabel)\s|[a-z ]+\s)?.*\s(\d{1,3}|[ivxlc]{1,6})$", re.I)
NON_ALNUM_RE = re.compile(r"[^0-9a-z]+")
COLUMNS = ("gambar", "tabel", "rumus", "catatan", "sitasi")


def _norm(text: str) -> str:
    return NON_ALNUM_RE.sub("", PREFIX_RE.sub("", text.strip().lower()))


def _counts(path: str) -> dict:
    body = Document(path).element.body
    instr = " ".join(t.text or "" for t in body.iter(qn("w:instrText")))
    sdt_cites = sum(1 for tag in body.iter(qn("w:tag")) if (tag.get(qn("w:val")) or "").startswith("MENDELEY_CITATION"))
    return {
        "gambar": sum(1 for _ in body.iter(A_BLIP)) + sum(1 for _ in body.iter(V_IMAGEDATA)),
        "tabel": sum(1 for _ in body.iter(qn("w:tbl"))),
        "rumus": sum(1 for _ in body.iter(M_OMATH)),
        "catatan": sum(1 for _ in body.iter(qn("w:footnoteReference"))) + sum(1 for _ in body.iter(qn("w:endnoteReference"))),
        "sitasi": instr.count("CSL_CITATION") + sdt_cites,
    }


def _paragraph_texts(path: str, skip_toc: bool = False) -> list:
    doc = Document(path)
    texts = []
    for p in doc.element.body.iter(qn("w:p")):
        text = "".join((t.text or "") if t.tag == qn("w:t") else " "
                       for t in p.iter(qn("w:t"), qn("w:br"), qn("w:tab")))
        if skip_toc and _is_toc_line(p, text):
            continue
        texts.append(text)
    return texts


def _is_toc_line(p, text: str) -> bool:
    style = p.find(f"{qn('w:pPr')}/{qn('w:pStyle')}")
    style_id = (style.get(qn("w:val")) or "").lower() if style is not None else ""
    if style_id.startswith("toc") or style_id.replace(" ", "") == "tableoffigures":
        return True
    in_toc_sdt = any(g.get(qn("w:val")) == "Table of Contents" for a in p.iterancestors(qn("w:sdt"))
                     for g in a.iter(qn("w:docPartGallery")))
    return in_toc_sdt or (len(text.split()) <= 15 and bool(TOC_LINE_RE.match(text.strip())) and "\t" in text)


def _coverage(src: str, out: str):
    out_text = NON_ALNUM_RE.sub("", " ".join(_paragraph_texts(out)).lower())
    src_norm = [n for n in (_norm(t) for t in _paragraph_texts(src, skip_toc=True)) if len(n) >= 3]
    missing = [n for n in src_norm if n not in out_text]
    return (1 - len(missing) / max(len(src_norm), 1)), missing


def main(paths) -> None:
    inspector, critic, formatter = InspectorAgent(), QualityCriticAgent(active_learning=_NoFeedback()), FormattingActuatorAgent()
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for src in paths:
            out = os.path.join(tmp, os.path.basename(src))
            with contextlib.redirect_stdout(io.StringIO()):
                approved = critic.coordinate_tier1_blueprint_loop(inspector.inspect(src), inspector, 3)
                formatter.format_document(src, approved, out)
            before, after = _counts(src), _counts(out)
            cover, missing = _coverage(src, out)
            rows.append((os.path.basename(src), before, after, cover, missing))
            diff = [c for c in COLUMNS if before[c] != after[c]]
            print(f"[{'ok' if not diff and not missing else 'SELISIH'}] {os.path.basename(src)}: "
                  f"cakupan teks {cover * 100:.2f}% | " + ", ".join(f"{c} {before[c]}->{after[c]}" for c in COLUMNS))
            for m in missing[:3]:
                print(f"    hilang: {m[:70]}")

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Uji Keutuhan Isi\n\n**Tanggal:** {date.today():%d-%m-%Y}\n\n")
        f.write("Format sel: jumlah sebelum → sesudah diformat. Cakupan teks = % paragraf sumber yang teksnya ada di hasil.\n\n")
        f.write("| Dokumen | " + " | ".join(c.capitalize() for c in COLUMNS) + " | Cakupan teks (%) |\n")
        f.write("|---|" + "---|" * len(COLUMNS) + "---|\n")
        for name, before, after, cover, _ in rows:
            cells = [f"{before[c]} → {after[c]}" + ("" if before[c] == after[c] else " ⚠") for c in COLUMNS]
            f.write(f"| {name} | " + " | ".join(cells) + f" | {cover * 100:.2f} |\n")
        lost = [(n, m) for n, *_, missing in rows for m in missing]
        if lost:
            f.write("\n## Paragraf sumber yang tidak ditemukan di hasil\n\n")
            for name, m in lost[:50]:
                f.write(f"- `{name}`: {m[:100]}\n")
    print(f"[SUKSES] Laporan keutuhan: {REPORT_PATH}")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT_INPUTS)
