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
| Naskah asli | U02_TA.docx | (b) Aturan Agen 2 saja | 98.80 | 92.82 |
| Naskah asli | U02_TA.docx | (c) Sistem multi-agen | 99.32 | 97.56 |
| Naskah asli | GABUNGAN | (a) Agen 1 saja | 98.72 | 93.79 |
| Naskah asli | GABUNGAN | (b) Aturan Agen 2 saja | 99.10 | 96.76 |
| Naskah asli | GABUNGAN | (c) Sistem multi-agen | 99.51 | 98.86 |
| Naskah heading polos | U01_TA.docx | (a) Agen 1 saja | 99.33 | 99.39 |
| Naskah heading polos | U01_TA.docx | (b) Aturan Agen 2 saja | 98.92 | 96.82 |
| Naskah heading polos | U01_TA.docx | (c) Sistem multi-agen | 99.06 | 97.57 |
| Naskah heading polos | U02_TA.docx | (a) Agen 1 saja | 98.34 | 88.77 |
| Naskah heading polos | U02_TA.docx | (b) Aturan Agen 2 saja | 98.80 | 92.82 |
| Naskah heading polos | U02_TA.docx | (c) Sistem multi-agen | 99.32 | 97.56 |
| Naskah heading polos | GABUNGAN | (a) Agen 1 saja | 98.61 | 92.41 |
| Naskah heading polos | GABUNGAN | (b) Aturan Agen 2 saja | 98.84 | 95.88 |
| Naskah heading polos | GABUNGAN | (c) Sistem multi-agen | 99.25 | 97.99 |

## F1 per Kelas (gabungan naskah uji)

### Naskah asli

| Kelas | (a) Agen 1 saja | (b) Aturan Agen 2 saja | (c) Sistem multi-agen |
|---|---|---|---|
| `BODY_PARAGRAPH` | 0.992 | 0.993 | 0.996 |
| `CAPTION_GAMBAR` | 1.000 | 1.000 | 1.000 |
| `CAPTION_TABEL` | 1.000 | 1.000 | 1.000 |
| `COVER_METADATA` | 0.933 | 0.769 | 0.933 |
| `DAFTAR_PUSTAKA_ITEM` | 0.720 | 1.000 | 1.000 |
| `FRONTMATTER_TITLE` | 0.863 | 1.000 | 1.000 |
| `JUDUL_BAB` | 1.000 | 1.000 | 1.000 |
| `LAINNYA` | 1.000 | 1.000 | 1.000 |
| `SUB_BAB` | 0.933 | 0.946 | 0.968 |

### Naskah heading polos

| Kelas | (a) Agen 1 saja | (b) Aturan Agen 2 saja | (c) Sistem multi-agen |
|---|---|---|---|
| `BODY_PARAGRAPH` | 0.992 | 0.993 | 0.996 |
| `CAPTION_GAMBAR` | 1.000 | 1.000 | 1.000 |
| `CAPTION_TABEL` | 1.000 | 1.000 | 1.000 |
| `COVER_METADATA` | 0.933 | 0.769 | 0.933 |
| `DAFTAR_PUSTAKA_ITEM` | 0.720 | 1.000 | 1.000 |
| `FRONTMATTER_TITLE` | 0.792 | 0.935 | 0.935 |
| `JUDUL_BAB` | 0.947 | 1.000 | 1.000 |
| `LAINNYA` | 1.000 | 0.996 | 0.996 |
| `SUB_BAB` | 0.933 | 0.936 | 0.959 |

