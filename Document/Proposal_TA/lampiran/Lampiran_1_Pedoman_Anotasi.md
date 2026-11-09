# LAMPIRAN 1 — PEDOMAN ANOTASI STRUKTUR PARAGRAF NASKAH TUGAS AKHIR

> Versi 1.1 (9 November 2026). Pedoman ini digunakan untuk memberi label manual pada setiap paragraf dalam korpus penelitian. Label yang dihasilkan menjadi acuan kebenaran (*ground truth*) untuk melatih dan menguji sistem Asdoku. Setiap perubahan pedoman dicatat pada Bagian 7.

---

## 1. Tujuan

Pedoman ini memastikan bahwa dua anotator yang berbeda memberi label yang sama pada paragraf yang sama. Karena itu, setiap kelas didefinisikan berdasarkan **peran paragraf dalam struktur naskah**, bukan berdasarkan tampilannya. Paragraf yang dicetak tebal belum tentu judul, dan judul yang tidak dicetak tebal tetap judul.

## 2. Unit Anotasi

1. **Satu baris pada lembar kerja = satu paragraf Word**, yaitu teks di antara dua penekanan tombol *Enter*. Satu kalimat yang terpotong menjadi dua paragraf tetap dianotasi sebagai dua baris.
2. Paragraf kosong tetap muncul pada lembar kerja dan wajib diberi label.
3. Isi sel tabel, *header*, *footer*, catatan kaki, dan kotak teks **tidak** termasuk unit anotasi. Lembar kerja hanya memuat paragraf badan dokumen.
4. Baris Daftar Isi/Tabel/Gambar, baik otomatis (*field* TOC) maupun diketik manual, termasuk unit anotasi dan diberi label `LAINNYA` (lihat Kasus Batas K10). Daftar Isi yang tersimpan di dalam *content control* Word tidak muncul pada lembar kerja.

## 3. Kelas Label

| No | Label | Nama | Definisi Singkat |
|---|---|---|---|
| 1 | `COVER_METADATA` | Metadata sampul | Teks identitas pada halaman sampul dan halaman judul |
| 2 | `FRONTMATTER_TITLE` | Judul halaman khusus | Judul halaman di luar bab: halaman awal, Daftar Pustaka/Referensi, dan Lampiran |
| 3 | `JUDUL_BAB` | Judul bab | Judul bab utama (BAB I, BAB II, dst.) beserta nama babnya |
| 4 | `SUB_BAB` | Sub-bab | Judul sub-bab dan sub-sub-bab di dalam bab (1.1, 1.1.1, dst.) |
| 5 | `BODY_PARAGRAPH` | Paragraf isi | Semua isi tulisan yang bukan judul dan bukan *caption*: paragraf, butir daftar, rumus, kode, gambar, isi halaman awal |
| 6 | `CAPTION_GAMBAR` | Judul gambar | Judul bernomor yang menamai sebuah gambar |
| 7 | `CAPTION_TABEL` | Judul tabel | Judul bernomor yang menamai sebuah tabel |
| 8 | `DAFTAR_PUSTAKA_ITEM` | Entri daftar pustaka | Satu entri rujukan di bawah judul Daftar Pustaka/Referensi |
| 9 | `LAINNYA` | Lainnya | Paragraf kosong dan sisa yang tidak memiliki peran isi |

## 4. Definisi dan Contoh per Kelas

### 4.1 `COVER_METADATA`

**Definisi:** Setiap baris teks pada **halaman sampul** dan **halaman judul**, yaitu jenis naskah, judul tugas akhir, "Disusun oleh", nama, NIM, program studi, fakultas, universitas, kota, dan tahun.

| Contoh | Label |
|---|---|
| PROPOSAL TUGAS AKHIR | `COVER_METADATA` |
| RANCANG BANGUN SISTEM INFORMASI … (judul pada sampul) | `COVER_METADATA` |
| Arditya Adjie Rosandi / 20230801274 | `COVER_METADATA` |
| PROGRAM STUDI TEKNIK INFORMATIKA | `COVER_METADATA` |

**Bukan:** "Nama : …" dan "NIM : …" pada **lembar pengesahan** atau **abstrak** diberi label `BODY_PARAGRAPH` (isian formulir, bukan sampul). Logo universitas mengikuti aturan gambar, lihat K7.

### 4.2 `FRONTMATTER_TITLE`

**Definisi:** Judul sebuah halaman atau bagian yang **tidak bernomor bab**. Kelas ini mencakup tiga kelompok:

1. Judul halaman awal: LEMBAR PENGESAHAN, PERNYATAAN KEASLIAN, KATA PENGANTAR, UCAPAN TERIMA KASIH, ABSTRAK, ABSTRACT, DAFTAR ISI, DAFTAR TABEL, DAFTAR GAMBAR, DAFTAR LAMPIRAN, DAFTAR SIMBOL.
2. Judul daftar rujukan: DAFTAR PUSTAKA, DAFTAR REFERENSI.
3. Judul lampiran: LAMPIRAN, "Lampiran 1 Kuesioner Penelitian".

**Bukan:** Nama bab (PENDAHULUAN) adalah `JUDUL_BAB`, walaupun tanpa kata "BAB".

### 4.3 `JUDUL_BAB`

**Definisi:** Judul bab utama yang membuka bagian isi naskah. Pada pedoman UEU, judul bab bernomor Romawi besar (BAB I, BAB II).

| Contoh | Label |
|---|---|
| BAB I PENDAHULUAN (satu baris) | `JUDUL_BAB` |
| BAB II (baris 1) + STUDI TEORITIS (baris 2) | keduanya `JUDUL_BAB` |
| PENDAHULUAN (tanpa kata "BAB", di awal bagian isi) | `JUDUL_BAB` |
| BAB 3 METODOLOGI PENELITIAN (nomor Arab) | `JUDUL_BAB` |

**Bukan:**
- Baris di sub-bab Sistematika Penulisan seperti "BAB I PENDAHULUAN: Bab ini berisi latar belakang …" adalah `BODY_PARAGRAPH`, karena kalimat itu **menjelaskan** bab, bukan membuka bab.
- Entri "BAB I Pendahuluan ……… 1" pada daftar isi adalah `LAINNYA` (lihat K10).

### 4.4 `SUB_BAB`

**Definisi:** Judul bagian di dalam bab, pada derajat berapa pun (1.1, 1.1.1, 1.1.1.1). Judul sub-bab biasanya pendek, tidak diakhiri titik, dan diikuti paragraf isi.

| Contoh | Label |
|---|---|
| 1.1 Latar Belakang | `SUB_BAB` |
| 2.2.3 Random Forest | `SUB_BAB` |
| Latar Belakang (tanpa nomor, sebagai judul bagian) | `SUB_BAB` |
| Manfaat Teoretis (judul bagian di bawah 1.6 Manfaat Penelitian, diikuti paragraf) | `SUB_BAB` |

**Bukan:** Butir daftar bernomor yang berupa kalimat atau frasa isi, misalnya "1. Bagaimana merancang …?" pada rumusan masalah, adalah `BODY_PARAGRAPH`. Pembedanya dijelaskan pada K1.

### 4.5 `BODY_PARAGRAPH`

**Definisi:** Semua isi tulisan yang tidak termasuk kelas lain. Kelas ini sengaja dibuat luas:

- paragraf biasa di bagian isi;
- isi halaman awal: teks kata pengantar, abstrak, kata kunci, lembar pengesahan, dan pernyataan;
- butir daftar bernomor atau berbutir (1., a., •);
- rumus, keterangan variabel ("di mana *n* = jumlah data"), dan potongan kode program;
- kutipan langsung yang diblok;
- baris sumber di bawah gambar atau tabel ("Sumber: …");
- **paragraf yang hanya berisi gambar** (tanpa teks);
- isi lampiran.

### 4.6 `CAPTION_GAMBAR`

**Definisi:** Judul gambar yang diawali kata "Gambar" (atau "Figure") dan nomor, paling banyak sekitar 25 kata.

| Contoh | Label |
|---|---|
| Gambar 2.1 Arsitektur Multi-Agent System | `CAPTION_GAMBAR` |
| Gambar 3.2. Diagram Alur Penelitian | `CAPTION_GAMBAR` |

**Bukan:** "Gambar 2.1 menunjukkan bahwa …" adalah kalimat isi yang merujuk gambar, sehingga diberi label `BODY_PARAGRAPH`.

### 4.7 `CAPTION_TABEL`

**Definisi:** Sama dengan `CAPTION_GAMBAR`, tetapi untuk tabel, diawali "Tabel" (atau "Table").

| Contoh | Label |
|---|---|
| Tabel 2.1 Penelitian Terdahulu | `CAPTION_TABEL` |

**Bukan:** "Tabel 4.3 menyajikan hasil …" adalah `BODY_PARAGRAPH`.

### 4.8 `DAFTAR_PUSTAKA_ITEM`

**Definisi:** Satu entri rujukan di bawah judul DAFTAR PUSTAKA/DAFTAR REFERENSI, sampai bagian berikutnya dimulai (misalnya LAMPIRAN).

| Contoh | Label |
|---|---|
| Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32. | `DAFTAR_PUSTAKA_ITEM` |

**Bukan:** Judul DAFTAR PUSTAKA sendiri adalah `FRONTMATTER_TITLE`. Paragraf kosong di antara entri adalah `LAINNYA`.

### 4.9 `LAINNYA`

**Definisi:** Paragraf yang tidak memiliki peran isi, terutama:

- paragraf kosong (termasuk yang hanya berisi spasi, tab, atau pemisah halaman tanpa teks);
- sisa teks yang jelas bukan bagian naskah, misalnya teks petunjuk template yang lupa dihapus ("[Tulis judul di sini]");
- baris Daftar Isi, Daftar Tabel, dan Daftar Gambar (K10).

**Bukan:** Paragraf yang hanya berisi gambar adalah `BODY_PARAGRAPH` (K7).

## 5. Urutan Keputusan

Jika ragu, tanyakan pertanyaan berikut **berurutan** dan berhenti pada jawaban "ya" yang pertama:

1. Apakah paragraf kosong (tanpa teks dan tanpa gambar), atau baris Daftar Isi/Tabel/Gambar? → `LAINNYA`
2. Apakah paragraf berada di halaman sampul atau halaman judul? → `COVER_METADATA`
3. Apakah paragraf diawali "Gambar/Tabel + nomor", pendek, dan **menamai** gambar/tabel (bukan kalimat yang membahasnya)? → `CAPTION_GAMBAR` / `CAPTION_TABEL`
4. Apakah paragraf membuka sebuah bab utama? → `JUDUL_BAB`
5. Apakah paragraf adalah judul halaman/bagian tanpa nomor bab (halaman awal, daftar pustaka, lampiran)? → `FRONTMATTER_TITLE`
6. Apakah paragraf adalah judul bagian di dalam bab, yang diikuti isi bagian tersebut? → `SUB_BAB`
7. Apakah paragraf berada di bawah judul Daftar Pustaka dan merupakan satu rujukan? → `DAFTAR_PUSTAKA_ITEM`
8. Selain itu → `BODY_PARAGRAPH`

## 6. Kasus Batas

| Kode | Kasus | Label | Alasan |
|---|---|---|---|
| K1 | Butir bernomor "1. Kontribusi Teori" yang **diikuti paragraf penjelasan** di bawahnya | `SUB_BAB` | Berfungsi sebagai judul bagian (akan menjadi sub-sub-bab 1.x.y) |
| K2 | Butir bernomor yang berupa kalimat atau frasa isi dan **tidak** diikuti paragraf penjelasan, misalnya rumusan masalah dan tujuan | `BODY_PARAGRAPH` | Isi daftar, bukan judul |
| K3 | Judul bab dua baris ("BAB I" lalu "PENDAHULUAN") | keduanya `JUDUL_BAB` | Satu judul yang dipecah menjadi dua paragraf |
| K4 | Butir penjelasan bab di Sistematika Penulisan ("BAB II Studi Teoritis, berisi …") | `BODY_PARAGRAPH` | Menjelaskan bab, bukan membuka bab |
| K5 | "Gambar 2.1 menunjukkan …" / "Tabel 4.1 berisi …" | `BODY_PARAGRAPH` | Kalimat yang merujuk, bukan judul |
| K6 | Baris "Sumber: Penulis (2026)" di bawah gambar/tabel | `BODY_PARAGRAPH` | Keterangan, bukan judul |
| K7 | Paragraf yang hanya berisi gambar, termasuk logo di sampul | `BODY_PARAGRAPH` | Konvensi sistem: paragraf gambar diformat sebagai isi |
| K8 | Isian "Nama :", "NIM :", "Kata kunci :" pada lembar pengesahan/abstrak | `BODY_PARAGRAPH` | Isian formulir, bukan identitas sampul |
| K9 | Rumus, keterangan variabel, dan kode program | `BODY_PARAGRAPH` | Isi tulisan |
| K10 | Baris daftar isi/tabel/gambar, otomatis maupun diketik manual ("1.1 Latar Belakang ……… 2") | `LAINNYA` | Entri daftar, bukan judul maupun isi: sistem tidak memformatnya sebagai paragraf isi, tetapi menggantinya dengan daftar otomatis. Nomor di awal tidak menjadikannya sub-bab |
| K11 | Hipotesis berlabel ("H1: Terdapat pengaruh …") | `BODY_PARAGRAPH` | Isi tulisan |
| K12 | Judul bagian tanpa nomor di dalam bab yang dicetak tebal, misalnya "Manfaat Praktis" | `SUB_BAB` | Berfungsi sebagai judul bagian |
| K13 | Kalimat pendek tebal di dalam paragraf yang **tidak** diikuti isi bagian (penekanan) | `BODY_PARAGRAPH` | Penekanan, bukan judul |
| K14 | Judul tabel/gambar yang terpisah dua paragraf ("Tabel 2.1" lalu "Penelitian Terdahulu") | keduanya `CAPTION_TABEL`/`CAPTION_GAMBAR` | Satu judul yang dipecah |
| K15 | Judul "LAMPIRAN" dan "Lampiran 1 …" | `FRONTMATTER_TITLE` | Judul bagian tanpa nomor bab |

**Kasus yang belum tercakup:** catat pada kolom `catatan` di lembar kerja, pilih label yang paling sesuai dengan urutan keputusan di Bagian 5, lalu bahas pada sesi penyelarasan (Bagian 7).

## 7. Prosedur Anotasi

1. **Pra-label.** Sistem mengisi kolom `Label Awal` dengan tebakan otomatis dan menyalinnya ke kolom `Label` sebagai titik awal. Tebakan ini hanya bantuan dan **tidak boleh diterima tanpa diperiksa**.
2. **Pemeriksaan.** Anotator membuka naskah asli di Microsoft Word berdampingan dengan lembar kerja, memeriksa **setiap** baris, dan mengisi kolom `label_manual` dari daftar pilihan (*dropdown*). Kolom `label_manual` wajib terisi untuk semua baris, termasuk baris yang sudah benar.
3. **Catatan.** Baris yang membuat anotator ragu ditandai pada kolom `ragu` dan diberi alasan pada kolom `catatan`.
4. **Anotator kedua.** Minimal 20% paragraf (dipilih per dokumen, bukan per paragraf acak) dianotasi ulang oleh anotator kedua **tanpa melihat** label anotator pertama dan tanpa kolom `label_awal`.
5. **Kesepakatan.** Kesepakatan dihitung dengan kappa Cohen. Targetnya κ ≥ 0,80. Jika di bawah target, ketidaksepakatan dibahas, pedoman diperbaiki, lalu anotasi diulang pada bagian yang terdampak.
6. **Label final.** Untuk paragraf yang dianotasi dua kali, ketidaksepakatan diselesaikan melalui diskusi, dan label hasil diskusi menjadi label final.
7. **Pencatatan perubahan.** Setiap perubahan pedoman dicatat di tabel berikut.

| Versi | Tanggal | Perubahan |
|---|---|---|
| 1.0 | 5 November 2026 | Versi awal |
| 1.1 | 9 November 2026 | K10: baris daftar isi/tabel/gambar (otomatis maupun manual) menjadi `LAINNYA`, bukan `BODY_PARAGRAPH`, dan daftar otomatis ikut dianotasi. Alasan: sistem tidak memformat baris daftar sebagai isi, melainkan menggantinya dengan daftar otomatis, sehingga memberinya label isi akan menilai sistem dengan konvensi yang tidak dipakainya. Diputuskan sebelum anotasi manual dimulai. Format lembar kerja disesuaikan dengan alat `tools/label_excel.py` (Bagian 8). |

## 8. Format Lembar Kerja

Lembar kerja dibuat oleh `App/tools/label_excel.py buat`: satu berkas Excel per naskah (`<bagian>__<kode>.xlsx`), sheet **Paragraf** dan sheet **Daftar Label**.

| Kolom | Isi | Diisi oleh |
|---|---|---|
| `No` | Nomor urut paragraf (`para_id`) | Sistem |
| `Teks` | Teks paragraf (dipotong 400 karakter; `[gambar]` untuk paragraf gambar) | Sistem |
| `Gaya Word`, `Ukuran`, `Tebal`, `Rata` | Ringkasan tampilan paragraf | Sistem |
| `Label Awal` | Tebakan sistem (tidak diubah) | Sistem |
| `Label` | Label final (pilihan tertutup 9 kelas) | Anotator |
| `Catatan` | Alasan, keraguan, atau kasus yang belum tercakup | Anotator |

Kode naskah anonim: `L01`–`L05` (data latih), `U01`–`U02` (data uji). Paragraf kosong tanpa gambar tidak ditampilkan dan otomatis berlabel `LAINNYA` saat impor.
