"""Buat versi "heading polos" dari naskah korpus (Fase 1, uji ketangguhan).

Banyak mahasiswa tidak memakai gaya Heading/Caption Word: judul cukup ditebalkan dan diperbesar
manual. Skrip ini meniru kondisi itu: setiap paragraf bergaya Heading, Title, Caption, TOC, atau
Table of Figures diubah ke gaya Normal, sementara tampilannya (tebal, miring, ukuran huruf, perataan)
dipertahankan sebagai format langsung. Nomor otomatis dari gaya Heading ikut hilang (kasus terberat).

Urutan paragraf tidak berubah, sehingga label diambil dari Excel naskah asli (data/corpus/label).

Penggunaan (dari folder App/):
  python3 tools/buat_heading_polos.py
Hasil:
  data/corpus/<split>_polos/<nama>.docx        dokumen polos (bisa dipakai menguji Asdoku utuh)
  data/corpus/dataset_<split>_polos.csv        fitur + label, format sama dengan dataset_<split>.csv
"""
import csv
import os
import re
import sys

from docx import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from label_excel import CORPUS, LABEL_DIR, SPLITS, _read_workbook  # noqa: E402
from src.paragraph_features import extract_paragraph_features  # noqa: E402

STRIP_STYLE_RE = re.compile(r"^(heading \d|title|subtitle|caption|toc \d|table of figures)$", re.I)


def _resolve(style, getter):
    """Nilai pertama yang terdefinisi di sepanjang rantai gaya (gaya -> gaya dasar -> ...)."""
    while style is not None:
        value = getter(style)
        if value is not None:
            return value
        style = style.base_style
    return None


def strip_styles(src: str, dst: str) -> int:
    doc = Document(src)
    normal = doc.styles["Normal"]
    changed = 0
    for p in doc.paragraphs:
        style = p.style
        if style is None or not STRIP_STYLE_RE.match(style.name):
            continue
        bold = _resolve(style, lambda s: s.font.bold)
        italic = _resolve(style, lambda s: s.font.italic)
        size = _resolve(style, lambda s: s.font.size)
        align = p.paragraph_format.alignment or _resolve(style, lambda s: s.paragraph_format.alignment)
        p.style = normal
        if align is not None:
            p.paragraph_format.alignment = align
        for run in p.runs:
            if run.font.bold is None and bold is not None:
                run.font.bold = bold
            if run.font.italic is None and italic is not None:
                run.font.italic = italic
            if run.font.size is None and size is not None:
                run.font.size = size
        changed += 1
    doc.save(dst)
    return changed


def main() -> None:
    for split in SPLITS:
        src_dir, out_dir = os.path.join(CORPUS, split), os.path.join(CORPUS, f"{split}_polos")
        if not os.path.isdir(src_dir):
            continue
        os.makedirs(out_dir, exist_ok=True)
        rows_all = []
        for name in sorted(os.listdir(src_dir)):
            if not name.endswith(".docx") or name.startswith("~$"):
                continue
            xlsx = os.path.join(LABEL_DIR, f"{split}__{os.path.splitext(name)[0]}.xlsx")
            if not os.path.exists(xlsx):
                print(f"[lewati] {name}: belum ada Excel label")
                continue
            dst = os.path.join(out_dir, name)
            n = strip_styles(os.path.join(src_dir, name), dst)

            # Label dari naskah asli, dicocokkan per para_id; teks harus identik.
            labeled, errors, _, _ = _read_workbook(xlsx, split, name)
            if errors:
                sys.exit(f"{xlsx}: {errors[0]} — jalankan impor dulu sampai bersih")
            by_id = {r["para_id"]: r for r in labeled}
            paragraphs = Document(dst).paragraphs
            for idx, p in enumerate(paragraphs):
                f = extract_paragraph_features(p, idx, len(paragraphs))
                orig = by_id.get(idx)
                if orig is None or orig["text"] != f["text"]:
                    sys.exit(f"{name} paragraf {idx}: teks berbeda dengan naskah asli")
                rows_all.append({"doc_id": orig["doc_id"] + "_POLOS", **f, "label": orig["label"]})
            print(f"[ok] {dst}: {n} paragraf dilepas gayanya")

        if rows_all:
            out_csv = os.path.join(CORPUS, f"dataset_{split}_polos.csv")
            with open(out_csv, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(rows_all[0].keys()))
                writer.writeheader()
                writer.writerows(rows_all)
            print(f"    -> {out_csv}: {len(rows_all)} baris")


if __name__ == "__main__":
    main()
