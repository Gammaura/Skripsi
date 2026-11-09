# Asdoku (Asisten Dokumenku)

Multi-Agent System berbasis NLP untuk otomatisasi deteksi struktur dan formatting dokumen tugas akhir
(studi kasus: Fakultas Ilmu Komputer, Universitas Esa Unggul). Repositori skripsi Arditya Adjie Rosandi.

Tiga agen bekerja berurutan:

1. **Agen 1 – Inspector** (`App/src/agents/inspector.py`): Random Forest menebak label struktur tiap paragraf
   dari fitur teks (TF-IDF) dan tampilan Word (tipografi, gaya, pola teks).
2. **Agen 2 – Quality Critic** (`App/src/agents/critic.py`): memeriksa dan mengoreksi tebakan itu dengan aturan
   pedoman UEU dan konteks dokumen (urutan bab, daftar isi, sistematika), lalu menguji berkas hasil (8 kriteria SQA).
3. **Agen 3 – Formatter** (`App/src/agents/formatter.py`): menyusun ulang naskah ke templat UEU tanpa menghilangkan isi
   (gambar, tabel, rumus, sitasi Mendeley, catatan kaki, rujukan silang).

## Struktur folder

```
Skripsi/
├── README.md                      ← berkas ini
├── App/                           ← aplikasi Asdoku (Python, FastAPI)
│   ├── app.py, main.py, api/      ← server web, CLI, entri Vercel
│   ├── src/                       ← kode inti
│   │   ├── agents/                ← Agen 1–3
│   │   ├── ooxml/                 ← operasi XML Word (penyalinan, penomoran, daftar isi, tabel)
│   │   ├── features.py            ← fitur model (TF-IDF + tipografi + gaya + pola teks)
│   │   ├── paragraph_features.py  ← ekstraksi fitur mentah per paragraf
│   │   ├── classifiers.py         ← kandidat model (LR, RF, XGBoost)
│   │   ├── train.py               ← pelatihan + evaluasi korpus
│   │   ├── active_learning.py     ← pelatihan ulang dari koreksi pengguna
│   │   └── academic_rules.py, build_pure_training_data.py  ← aturan pedoman & aturan pra-label
│   ├── tools/                     ← alat penelitian (lihat "Alur kerja")
│   ├── tests/                     ← uji regresi P1–P5 (pipeline utuh + SQA + struktur XML)
│   ├── data/
│   │   ├── corpus/                ← korpus berlabel (PRIVAT, tidak masuk git)
│   │   ├── dokumen_uji/           ← dokumen uji regresi P1, P2, P3, P5
│   │   ├── template_clean_ueu.docx
│   │   ├── active_learning_feedback.csv
│   │   └── uploads/               ← salinan sementara unggahan web (dihapus otomatis)
│   ├── models/                    ← model produksi (Random Forest) + pipeline fitur
│   ├── output/                    ← laporan evaluasi (eval_*.md) + hasil uji regresi (pengujian/)
│   ├── static/img/, templates/    ← aset & halaman web
│   └── requirements*.txt, vercel.json
├── Data/                          ← naskah mentah dari penulis (PRIVAT, tidak masuk git) — lihat Data/README.md
├── Document/
│   ├── Proposal_TA/
│   │   ├── naskah/                ← DRAF_PROPOSAL_TA_v2.docx (versi kerja, diedit di Word)
│   │   ├── lampiran/              ← pedoman anotasi, formulir izin, kuesioner
│   │   ├── diagram/               ← kerangka berpikir, kerangka pemikiran, tahapan penelitian (.drawio + .png)
│   │   └── arsip/                 ← draf v1 (tidak dipakai lagi)
│   ├── Review/                    ← catatan review pembimbing/penguji
│   ├── Kapita_Selekta/            ← fase 1–7 mata kuliah Kapita Selekta (prototipe awal)
│   ├── Pedoman/                   ← Pedoman Penulisan Skripsi UEU 2018 + template
│   ├── LOGBOOK_PROGRES.md         ← catatan per sesi
│   └── RINGKASAN_PROYEK_ASDOKU.md
└── Sempro/                        ← bahan seminar proposal
```

## Menjalankan aplikasi

```bash
cd App
pip install -r requirements.txt            # + requirements-train.txt untuk melatih (xgboost)
python3 -m uvicorn app:app --port 8000     # buka http://localhost:8000/alat
python3 main.py naskah.docx                # atau lewat terminal
```

## Alur kerja penelitian (dari folder `App/`)

| Langkah | Perintah | Hasil |
|---|---|---|
| 1. Buat Excel pra-label | `python3 tools/label_excel.py buat` | `data/corpus/label/*.xlsx` |
| 2. Koreksi label di Excel | (manual, kolom **Label**) | — |
| 3. Impor label | `python3 tools/label_excel.py impor` | `data/corpus/dataset_latih.csv`, `dataset_uji.csv` |
| 4. Buat versi heading polos | `python3 tools/buat_heading_polos.py` | `dataset_*_polos.csv` + dokumen polos |
| 5. Latih & pilih model | `python3 -m src.train` | `models/`, `output/eval_report_korpus.md` |
| 6. Uji ablasi (RM 3) | `python3 tools/evaluasi_ablasi.py` | `output/eval_ablasi.md` |
| 7. Uji keutuhan isi | `python3 tools/evaluasi_keutuhan.py` | `output/eval_keutuhan.md` |
| 8. Uji regresi | `python3 tests/test_all_documents.py` | `output/pengujian/` |

Aturan penting:
- Pembagian data **per naskah**: korpus latih `L01–L05`, uji `U01–U02`. Naskah uji tidak boleh dipakai untuk
  melatih, memilih model, atau menyusun aturan Agen 2.
- Setelah mengubah label: ulangi langkah 3–7.
- Setiap perubahan Formatter: jalankan langkah 7–8 **dan** buka hasilnya di Microsoft Word asli
  (Word diam-diam membuang XML yang tidak sesuai skema).

## Privasi

`Data/` dan `App/data/corpus/` berisi naskah orang lain dan tercantum di `.gitignore`. Korpus memakai kode
(L01…, U01…); kunci kode → nama hanya ada di `Data/_kode_naskah.csv`. Jangan di-commit, jangan dibagikan.
