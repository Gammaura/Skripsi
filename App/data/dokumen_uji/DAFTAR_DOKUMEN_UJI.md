# DAFTAR DOKUMEN PENGUJIAN SISTEM MULTI-AGENT (MAS)
**Sistem:** Asdoku (Autonomous Academic Document Formatter MAS)  
**Institusi:** Universitas Esa Unggul (UEU)  
**Standar Acuan:** SK Rektor UEU No. 5 Tahun 2018 (Panduan Penulisan Skripsi & Tugas Akhir)

Dokumen-dokumen di bawah ini merupakan dataset dokumen uji resmi (*Benchmark Test Suite*) yang digunakan untuk mengevaluasi kinerja klasifikasi hierarki dan akurasi pemformatan otonom dari 3 Agen: **Agent 1 (Inspector)**, **Agent 2 (Quality Critic)**, dan **Agent 3 (Actuator / Formatter)**.

---

## 1. Tabel Karakteristik Dokumen Pengujian (Dataset Uji)

| Kode Dokumen | Nama Berkas | Ukuran | Paragraf | Tabel | Section | Total Kata | Fokus Skenario Pengujian Sistem |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **P1** | `P1_Template_Resmi_UEU.docx` | 2.95 MB | 248 | 3 | 5 | 4.273 | **Golden Standard Template:** Menguji struktur lengkap BAB I–V, Sub-bab (Heading 2), Sub-sub-bab (Heading 3), Multilevel List (`BAB 1`, `1.1`, `1.1.1`), Caption Gambar, Caption Tabel, Daftar Isi otomatis, dan proteksi gambar. |
| **P2** | `P2_Skripsi_Mbkm_Dhicky.docx` | 8.72 MB | 381 | 8 | 3 | 5.070 | **Heavy Real-World Thesis:** Menguji naskah nyata ukuran besar (8.7 MB) dengan puluhan gambar screenshot sistem, lampiran kompleks, dan tabel data luas. |
| **P3** | `P3_Proposal_Bab1_3_PBB.docx` | 0.08 MB | 177 | 7 | 2 | 5.813 | **Raw Text / Tanpa Template:** Menguji naskah proposal mahasiswa yang tidak menggunakan template Word bawaan (format teks murni, tanpa heading style awal). |
| **P5** | `P5_Buku_TA_Landscape.docx` | 0.38 MB | 250 | 4 | 6 | 1.389 | **Anomaly Layout & Orientation:** Menguji pemulihan otomatis section rusak berorientasi landscape (`w:orient="landscape"`) menjadi 100% A4 Portrait dan margin 4-3-3-3. |

---

## 2. Deskripsi Detail Setiap Dokumen Pengujian

### P1 — Template Resmi Tugas Akhir UEU (`P1_Template_Resmi_UEU.docx`)
* **Asal Dokumen:** Panduan Resmi Fakultas Ilmu Komputer Universitas Esa Unggul (UEU).
* **Karakteristik:** Memiliki halaman cover, lembar pengesahan, persetujuan, abstrak bilingual, daftar isi, daftar tabel, daftar gambar, bab I hingga bab V, serta daftar pustaka.
* **Tujuan Pengujian:**
  1. Validasi akurasi ekstraksi metadata cover dan tab stop titik dua.
  2. Validasi penghapusan komentar/petunjuk template secara otomatis.
  3. Validasi penomoran hierarkis Multilevel List native Word (`BAB 1`, `1.1`, `1.1.1`).
  4. Validasi Daftar Isi dinamis 2 tingkat dengan tab leader titik-titik.

### P2 — Skripsi MBKM Mandiri Dhicky Haryadi (`P2_Skripsi_Mbkm_Dhicky.docx`)
* **Asal Dokumen:** Laporan Akhir MBKM Mandiri / Skripsi Mahasiswa Prodi Teknik Informatika UEU.
* **Karakteristik:** Naskah lengkap dengan banyak diagram UML (Use Case, Activity, Sequence Diagram), tabel matriks pengujian fungsional, dan bukti dokumentasi.
* **Tujuan Pengujian:**
  1. Menjamin proteksi 100% elemen gambar (`w:drawing` dan `w:pict`) agar tidak hilang saat pembersihan baris kosong.
  2. Menerapkan standar APA 7 (3 garis horizontal, tanpa garis vertikal) pada seluruh tabel dokumen.
  3. Menguji stabilitas dual page numbering (Romawi depan dan Latin isi).

### P3 — Proposal Bab I s/d III PBB-P2 (`P3_Proposal_Bab1_3_PBB.docx`)
* **Asal Dokumen:** Proposal Skripsi Bab 1 sampai Bab 3 topik Pajak Bumi dan Bangunan (PBB-P2).
* **Karakteristik:** Naskah polos tanpa pemformatan template Word baku, margin awal tidak beraturan, dan belum memiliki style Heading Word.
* **Tujuan Pengujian:**
  1. Menguji kemampuan machine learning Agent 1 dan aturan Agent 2 dalam mengidentifikasi struktur Bab dan Sub-bab dari naskah murni.
  2. Menguji otomatisasi injeksi style Heading 1, 2, 3 ke dalam Navigation Pane Word.
  3. Menguji penataan margin resmi 4 3 3 3 cm dan line spacing 1.15.

> **Catatan:** P4 (Laporan MBKM Mandiri) dikeluarkan dari suite uji per 9 November 2026 karena laporan magang berada di luar lingkup sistem (dokumen tugas akhir). Kode P4 sengaja tidak dipakai ulang.

### P5 — Template Buku Tugas Akhir 2018 (`P5_Buku_TA_Landscape.docx`)
* **Asal Dokumen:** Template Buku Tugas Akhir UEU terbitan September 2018.
* **Karakteristik:** Memiliki beberapa section break dengan orientasi halaman mendatar (Landscape) dan margin default Word (Normal 2.54 cm).
* **Tujuan Pengujian:**
  1. Menguji fungsi `_enforce_a4_and_margins` dalam menormalisasi seluruh section dokumen menjadi A4 Portrait (21.0 x 29.7 cm).
  2. Menjamin margin resmi (Kiri 4 cm, Atas 3 cm, Kanan 3 cm, Bawah 3 cm) diterapkan merata tanpa ada halaman yang terpotong.

---

## 3. Catatan Penggunaan untuk Bab 4 Skripsi
Tabel dan deskripsi di atas dapat langsung disalin ke **Sub-Bab 4.1 Persiapan Pengujian (Dataset Dokumen Uji)** sebagai pembuktian bahwa sistem diuji secara komprehensif menggunakan beragam skenario naskah akademik nyata.
