# Laporan Evaluasi Model — Korpus Naskah TA

**Tanggal Pengujian:** 09-11-2026
**Data latih:** 9386 paragraf dari 5 naskah (asli + versi heading polos)
**Data uji:** 5328 paragraf dari 2 naskah (asli + versi heading polos) (penulis berbeda, tidak dipakai saat pelatihan maupun pemilihan model)
**Sumber label:** pra-label berbasis aturan, dikoreksi dengan bantuan AI; verifikasi manual penulis belum selesai.

---

## 1. Pemilihan Model (Leave-One-Document-Out pada Naskah Latih)

| Model | Macro-F1 (%) |
|---|---|
| Logistic Regression (Balanced) | 88.83 ± 3.50 |
| Random Forest (Balanced) | 94.70 ± 4.19 |
| XGBoost (Balanced) | 91.72 ± 7.57 |

Model terpilih: **Random Forest (Balanced)** — macro-F1 LODO tertinggi di antara model yang dapat di-deploy (Logistic Regression (Balanced), Random Forest (Balanced)). XGBoost hanya menjadi pembanding karena pustakanya melebihi batas ukuran paket deploy Vercel.

## 2. Hasil pada Naskah Uji

| Model / Naskah | Akurasi (%) | Macro-F1 (%) |
|---|---|---|
| Logistic Regression (Balanced) | 83.75 | 84.49 |
| Logistic Regression (Balanced) · semua naskah asli | 84.12 | 86.57 |
| Logistic Regression (Balanced) · semua naskah heading polos | 83.37 | 82.59 |
| Logistic Regression (Balanced) · UJI_U01_TA | 97.98 | 95.78 |
| Logistic Regression (Balanced) · UJI_U02_TA | 78.77 | 82.12 |
| Logistic Regression (Balanced) · UJI_U01_TA_POLOS | 96.09 | 91.01 |
| Logistic Regression (Balanced) · UJI_U02_TA_POLOS | 78.46 | 77.72 |
| Random Forest (Balanced) | 98.67 | 93.10 |
| Random Forest (Balanced) · semua naskah asli | 98.72 | 93.79 |
| Random Forest (Balanced) · semua naskah heading polos | 98.61 | 92.41 |
| Random Forest (Balanced) · UJI_U01_TA | 99.33 | 99.39 |
| Random Forest (Balanced) · UJI_U02_TA | 98.49 | 91.37 |
| Random Forest (Balanced) · UJI_U01_TA_POLOS | 99.33 | 99.39 |
| Random Forest (Balanced) · UJI_U02_TA_POLOS | 98.34 | 88.77 |
| XGBoost (Balanced) | 94.69 | 70.65 |
| XGBoost (Balanced) · semua naskah asli | 94.97 | 71.59 |
| XGBoost (Balanced) · semua naskah heading polos | 94.41 | 69.69 |
| XGBoost (Balanced) · UJI_U01_TA | 89.22 | 83.77 |
| XGBoost (Balanced) · UJI_U02_TA | 97.19 | 70.01 |
| XGBoost (Balanced) · UJI_U01_TA_POLOS | 87.33 | 82.22 |
| XGBoost (Balanced) · UJI_U02_TA_POLOS | 97.14 | 66.79 |

## 3. Metrik per Kelas Model Terpilih pada Naskah Uji: Random Forest (Balanced)

### Naskah asli

| Kelas Struktur Dokumen | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| `BODY_PARAGRAPH` | 0.9944 | 0.9900 | **0.9922** | 1806 |
| `CAPTION_GAMBAR` | 1.0000 | 1.0000 | **1.0000** | 50 |
| `CAPTION_TABEL` | 1.0000 | 1.0000 | **1.0000** | 49 |
| `COVER_METADATA` | 1.0000 | 0.8750 | **0.9333** | 16 |
| `DAFTAR_PUSTAKA_ITEM` | 1.0000 | 0.5625 | **0.7200** | 16 |
| `FRONTMATTER_TITLE` | 1.0000 | 0.7586 | **0.8627** | 29 |
| `JUDUL_BAB` | 1.0000 | 1.0000 | **1.0000** | 9 |
| `LAINNYA` | 1.0000 | 1.0000 | **1.0000** | 523 |
| `SUB_BAB` | 0.8737 | 1.0000 | **0.9326** | 166 |
| **Rata-rata Macro** | 0.9853 | 0.9096 | **0.9379** | 2664 |
| **Rata-rata Weighted** | 0.9884 | 0.9872 | **0.9870** | 2664 |

### Naskah heading polos

| Kelas Struktur Dokumen | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| `BODY_PARAGRAPH` | 0.9933 | 0.9900 | **0.9917** | 1806 |
| `CAPTION_GAMBAR` | 1.0000 | 1.0000 | **1.0000** | 50 |
| `CAPTION_TABEL` | 1.0000 | 1.0000 | **1.0000** | 49 |
| `COVER_METADATA` | 1.0000 | 0.8750 | **0.9333** | 16 |
| `DAFTAR_PUSTAKA_ITEM` | 1.0000 | 0.5625 | **0.7200** | 16 |
| `FRONTMATTER_TITLE` | 1.0000 | 0.6552 | **0.7917** | 29 |
| `JUDUL_BAB` | 0.9000 | 1.0000 | **0.9474** | 9 |
| `LAINNYA` | 1.0000 | 1.0000 | **1.0000** | 523 |
| `SUB_BAB` | 0.8737 | 1.0000 | **0.9326** | 166 |
| **Rata-rata Macro** | 0.9741 | 0.8981 | **0.9241** | 2664 |
| **Rata-rata Weighted** | 0.9873 | 0.9861 | **0.9856** | 2664 |

Versi heading polos = naskah yang sama dengan gaya Heading/Caption/TOC diganti Normal (tebal/ukuran/perataan dipertahankan), meniru mahasiswa yang tidak memakai gaya Word.
