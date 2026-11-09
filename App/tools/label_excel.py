"""Pelabelan manual korpus naskah TA lewat Excel (Fase 1).

Dua perintah, dijalankan dari folder App/:

  python3 tools/label_excel.py buat
      Untuk tiap .docx di data/corpus/latih dan data/corpus/uji, buat
      data/corpus/label/<split>__<nama>.xlsx berisi satu baris per paragraf.
      Kolom "Label" sudah diisi tebakan awal dari aturan (pra-label) dan punya
      dropdown 9 label; pelabel tinggal memeriksa dan membetulkan yang salah.
      File Excel yang sudah ada TIDAK ditimpa (supaya label yang sudah dikerjakan
      tidak hilang); pakai --timpa untuk memaksa.

  python3 tools/label_excel.py impor
      Baca semua Excel di data/corpus/label, periksa labelnya, lalu tulis
      data/corpus/dataset_latih.csv dan data/corpus/dataset_uji.csv
      (siap dipakai src/train.py).

Paragraf kosong tanpa gambar tidak ditampilkan di Excel; saat impor otomatis diberi label LAINNYA.
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter

from docx import Document
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.build_pure_training_data import _label, _next_zone  # noqa: E402
from src.paragraph_features import extract_paragraph_features  # noqa: E402

CORPUS = "data/corpus"
SPLITS = ("latih", "uji")
LABEL_DIR = os.path.join(CORPUS, "label")
SHEET = "Paragraf"
SHEET_LABELS = "Daftar Label"
AUTO_LABEL_EMPTY = "LAINNYA"

# Definisi mengikuti Lampiran 1 proposal (Pedoman Anotasi v1.1); kode kasus batas (K1–K15) merujuk ke sana.
LABELS = [
    ("COVER_METADATA", "Teks identitas di halaman sampul/judul (jenis naskah, judul, nama, NIM, prodi, fakultas, universitas, tahun). Logo = BODY (K7)"),
    ("FRONTMATTER_TITLE", "Judul halaman tanpa nomor bab: halaman awal, Daftar Pustaka/Referensi, Lampiran (judul terpecah: semua barisnya)"),
    ("JUDUL_BAB", "Judul bab utama (BAB I / PENDAHULUAN / dua baris). Daftar BAB di Sistematika = BODY (K4)"),
    ("SUB_BAB", "Judul bagian di dalam bab (1.1, 1.1.1, judul poin bernomor/tebal yang diikuti penjelasan: K1, K12)"),
    ("BODY_PARAGRAPH", "Semua isi: paragraf, butir daftar, rumus, kode, gambar, isian \"Nama :\" (K8), \"Sumber:\" (K6), tanda tangan"),
    ("CAPTION_GAMBAR", "Judul bernomor yang menamai gambar (\"Gambar 2.1 ...\"); kalimat yang merujuk gambar = BODY (K5)"),
    ("CAPTION_TABEL", "Judul bernomor yang menamai tabel (\"Tabel 3.2 ...\")"),
    ("DAFTAR_PUSTAKA_ITEM", "Satu entri rujukan di bawah judul Daftar Pustaka/Referensi"),
    ("LAINNYA", "Paragraf kosong, sisa petunjuk template, dan baris Daftar Isi/Tabel/Gambar (pedoman v1.1, K10)"),
]
LABEL_NAMES = {name for name, _ in LABELS}

# Kolom yang terlihat pelabel, lalu fitur lengkap (disembunyikan) untuk impor.
VISIBLE = [("No", 6), ("Teks", 80), ("Gaya Word", 16), ("Ukuran", 8), ("Tebal", 7), ("Rata", 10),
           ("Label Awal", 22), ("Label", 22), ("Catatan", 30)]
FEATURES = ["para_id", "text", "style", "char_len", "word_count", "font_size", "is_bold", "is_italic", "align",
            "has_num", "has_img", "has_pgbrk", "space_before", "space_after", "line_spacing", "first_line_indent",
            "left_indent", "uppercase_ratio", "doc_pos"]
COL_LABEL = [h for h, _ in VISIBLE].index("Label") + 1
TEXT_PREVIEW = 400
LEADER_RE = re.compile(r"\.{5,}|…{2,}")


def _doc_id(split: str, filename: str) -> str:
    return f"{split.upper()}_{os.path.splitext(filename)[0]}"


def _is_list_entry(f) -> bool:
    """Baris Daftar Isi/Tabel/Gambar (gaya TOC atau titik-titik penuntun) -> bukan caption/sub-bab asli."""
    style = f["style"].lower()
    return style.startswith("toc") or style == "table of figures" or bool(LEADER_RE.search(f["text"]))


def _extract(path: str):
    """Fitur + pra-label tiap paragraf (aturan build_pure_training_data + baris daftar isi -> LAINNYA)."""
    paragraphs = Document(path).paragraphs
    total, zone = len(paragraphs), "COVER"
    for idx, p in enumerate(paragraphs):
        f = extract_paragraph_features(p, idx, total)
        zone = _next_zone(zone, f["text"].upper())
        yield f, AUTO_LABEL_EMPTY if f["char_len"] and _is_list_entry(f) else _label(f, zone)


def _is_auto(f) -> bool:
    return f["char_len"] == 0 and not f["has_img"]


def _write_workbook(src: str, dst: str) -> Counter:
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET
    ws.append([h for h, _ in VISIBLE] + FEATURES)
    for c in ws[1]:
        c.font = Font(bold=True)

    counts = Counter()
    for f, guess in _extract(src):
        if _is_auto(f):
            continue
        text = f["text"] if f["text"] else "[gambar]"
        preview = text if len(text) <= TEXT_PREVIEW else text[:TEXT_PREVIEW] + " …"
        ws.append([f["para_id"], preview, f["style"], f["font_size"], "Ya" if f["is_bold"] else "",
                   f["align"], guess, guess, ""] + [f[k] for k in FEATURES])
        counts[guess] += 1

    for i, (_, width) in enumerate(VISIBLE, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = width
    for i in range(len(VISIBLE) + 1, len(VISIBLE) + len(FEATURES) + 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].hidden = True
    wrap = Alignment(wrap_text=True, vertical="top")
    for row in ws.iter_rows(min_row=2, max_col=len(VISIBLE)):
        for c in row:
            c.alignment = wrap
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{ws.cell(1, len(VISIBLE)).column_letter}{ws.max_row}"

    lw = wb.create_sheet(SHEET_LABELS)
    lw.append(["Label", "Kapan dipakai"])
    for c in lw[1]:
        c.font = Font(bold=True)
    for name, desc in LABELS:
        lw.append([name, desc])
    lw.column_dimensions["A"].width = 24
    lw.column_dimensions["B"].width = 100

    col = ws.cell(1, COL_LABEL).column_letter
    dv = DataValidation(type="list", formula1=f"='{SHEET_LABELS}'!$A$2:$A${len(LABELS) + 1}", allow_blank=False,
                        showErrorMessage=True, errorTitle="Label tidak dikenal",
                        error="Pilih salah satu label dari daftar (lihat sheet Daftar Label).")
    ws.add_data_validation(dv)
    dv.add(f"{col}2:{col}{ws.max_row}")

    wb.save(dst)
    return counts


def cmd_buat(overwrite: bool) -> None:
    os.makedirs(LABEL_DIR, exist_ok=True)
    for split in SPLITS:
        folder = os.path.join(CORPUS, split)
        for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if not name.lower().endswith(".docx") or name.startswith("~$"):
                continue
            dst = os.path.join(LABEL_DIR, f"{split}__{os.path.splitext(name)[0]}.xlsx")
            if os.path.exists(dst) and not overwrite:
                print(f"[lewati] {dst} sudah ada (pakai --timpa untuk membuat ulang)")
                continue
            counts = _write_workbook(os.path.join(folder, name), dst)
            print(f"[ok] {dst}: {sum(counts.values())} baris | " + ", ".join(f"{k}={v}" for k, v in counts.most_common()))


def _read_workbook(path: str, split: str, docx_name: str):
    """Baris dataset dari satu Excel berlabel, ditambah paragraf kosong yang dilabel otomatis."""
    ws = load_workbook(path, read_only=True)[SHEET]
    header = [c.value for c in next(ws.iter_rows(max_row=1))]
    pos = {h: i for i, h in enumerate(header)}
    labeled, errors, changed = {}, [], 0
    for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row[pos["para_id"]] is None:
            continue
        label = (row[pos["Label"]] or "").strip()
        if label not in LABEL_NAMES:
            errors.append(f"baris {r}: label '{label}' tidak dikenal")
            labeled[int(row[pos["para_id"]])] = None
            continue
        changed += label != row[pos["Label Awal"]]
        labeled[int(row[pos["para_id"]])] = label

    # Fitur diambil ulang dari .docx agar teks utuh & tipe data sama persis dengan saat inferensi.
    doc_id = _doc_id(split, docx_name)
    rows, missing = [], []
    for f, _ in _extract(os.path.join(CORPUS, split, docx_name)):
        if _is_auto(f):
            label = AUTO_LABEL_EMPTY
        elif f["para_id"] in labeled:
            label = labeled[f["para_id"]]
            if label is None:
                continue
        else:
            missing.append(f["para_id"])
            continue
        rows.append({"doc_id": doc_id, **f, "label": label})
    if missing:
        errors.append(f"{len(missing)} paragraf di .docx tidak ada di Excel (naskah berubah? buat ulang Excel-nya)")
    return rows, errors, changed, sum(v is not None for v in labeled.values())


def cmd_impor() -> None:
    per_split = {s: [] for s in SPLITS}
    failed = False
    for name in sorted(os.listdir(LABEL_DIR)):
        if not name.endswith(".xlsx") or name.startswith("~$") or "__" not in name:
            continue
        split, stem = name[:-5].split("__", 1)
        if split not in SPLITS:
            continue
        rows, errors, changed, n = _read_workbook(os.path.join(LABEL_DIR, name), split, stem + ".docx")
        status = "GAGAL" if errors else "ok"
        print(f"[{status}] {name}: {n} baris berlabel, {changed} diubah dari label awal ({changed / max(n, 1):.0%})")
        for e in errors[:10]:
            print(f"    - {e}")
        failed |= bool(errors)
        per_split[split].extend(rows)

    if failed:
        sys.exit("\nAda kesalahan; dataset TIDAK ditulis. Betulkan Excel-nya lalu jalankan impor lagi.")
    for split, rows in per_split.items():
        if not rows:
            continue
        out = os.path.join(CORPUS, f"dataset_{split}.csv")
        with open(out, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        dist = Counter(r["label"] for r in rows)
        print(f"\n{out}: {len(rows)} baris dari {len({r['doc_id'] for r in rows})} naskah")
        for label, c in dist.most_common():
            print(f"  {label:22s} {c:5d}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("buat", help="buat Excel pra-label dari naskah .docx")
    b.add_argument("--timpa", action="store_true", help="timpa Excel yang sudah ada")
    sub.add_parser("impor", help="baca Excel berlabel menjadi dataset CSV")
    args = ap.parse_args()
    cmd_buat(args.timpa) if args.cmd == "buat" else cmd_impor()


if __name__ == "__main__":
    main()
