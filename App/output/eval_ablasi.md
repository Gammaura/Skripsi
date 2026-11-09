# Uji Ablasi Deteksi Struktur

**Tanggal:** 09-11-2026  
**Data:** naskah uji (tidak dipakai melatih model)  
**Pembanding:** label manual per paragraf (9 kelas)

| Set | Naskah | Konfigurasi | Akurasi (%) | Macro-F1 (%) |
|---|---|---|---|---|
| Naskah asli | U01_TA.docx | (a) Agen 1 saja | 99.33 | 99.39 |
| Naskah asli | U01_TA.docx | (b) Aturan Agen 2 saja | 99.87 | 99.25 |
| Naskah asli | U01_TA.docx | (c) Sistem multi-agen | 100.00 | 100.00 |
| Naskah asli | U02_TA.docx | (a) Agen 1 saja | 98.49 | 91.37 |
| Naskah asli | U02_TA.docx | (b) Aturan Agen 2 saja | 98.86 | 92.87 |
| Naskah asli | U02_TA.docx | (c) Sistem multi-agen | 99.38 | 97.61 |
| Naskah asli | GABUNGAN | (a) Agen 1 saja | 98.72 | 93.79 |
| Naskah asli | GABUNGAN | (b) Aturan Agen 2 saja | 99.14 | 96.79 |
| Naskah asli | GABUNGAN | (c) Sistem multi-agen | 99.55 | 98.90 |
| Naskah heading polos | U01_TA.docx | (a) Agen 1 saja | 99.33 | 99.39 |
| Naskah heading polos | U01_TA.docx | (b) Aturan Agen 2 saja | 93.53 | 88.96 |
| Naskah heading polos | U01_TA.docx | (c) Sistem multi-agen | 93.67 | 89.71 |
| Naskah heading polos | U02_TA.docx | (a) Agen 1 saja | 98.34 | 88.77 |
| Naskah heading polos | U02_TA.docx | (b) Aturan Agen 2 saja | 98.86 | 92.87 |
| Naskah heading polos | U02_TA.docx | (c) Sistem multi-agen | 99.38 | 97.61 |
| Naskah heading polos | GABUNGAN | (a) Agen 1 saja | 98.61 | 92.41 |
| Naskah heading polos | GABUNGAN | (b) Aturan Agen 2 saja | 97.37 | 94.16 |
| Naskah heading polos | GABUNGAN | (c) Sistem multi-agen | 97.79 | 96.35 |

## F1 per Kelas (gabungan naskah uji)

### Naskah asli

| Kelas | (a) Agen 1 saja | (b) Aturan Agen 2 saja | (c) Sistem multi-agen |
|---|---|---|---|
| `BODY_PARAGRAPH` | 0.992 | 0.994 | 0.997 |
| `CAPTION_GAMBAR` | 1.000 | 1.000 | 1.000 |
| `CAPTION_TABEL` | 1.000 | 1.000 | 1.000 |
| `COVER_METADATA` | 0.933 | 0.769 | 0.933 |
| `DAFTAR_PUSTAKA_ITEM` | 0.720 | 1.000 | 1.000 |
| `FRONTMATTER_TITLE` | 0.863 | 1.000 | 1.000 |
| `JUDUL_BAB` | 1.000 | 1.000 | 1.000 |
| `LAINNYA` | 1.000 | 1.000 | 1.000 |
| `SUB_BAB` | 0.933 | 0.949 | 0.971 |

### Naskah heading polos

| Kelas | (a) Agen 1 saja | (b) Aturan Agen 2 saja | (c) Sistem multi-agen |
|---|---|---|---|
| `BODY_PARAGRAPH` | 0.992 | 0.982 | 0.985 |
| `CAPTION_GAMBAR` | 1.000 | 1.000 | 1.000 |
| `CAPTION_TABEL` | 1.000 | 1.000 | 1.000 |
| `COVER_METADATA` | 0.933 | 0.769 | 0.933 |
| `DAFTAR_PUSTAKA_ITEM` | 0.720 | 1.000 | 1.000 |
| `FRONTMATTER_TITLE` | 0.792 | 0.935 | 0.935 |
| `JUDUL_BAB` | 0.947 | 1.000 | 1.000 |
| `LAINNYA` | 1.000 | 0.996 | 0.996 |
| `SUB_BAB` | 0.933 | 0.792 | 0.822 |

