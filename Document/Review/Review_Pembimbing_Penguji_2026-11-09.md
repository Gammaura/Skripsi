# Catatan Review Pembimbing & Penguji — Proposal TA Asdoku

**Judul:** Rancang Bangun Multi-Agent System Berbasis NLP untuk Otomatisasi Deteksi Struktur dan Formatting Dokumen Tugas Akhir (Studi Kasus: FIK UEU)
**Ditinjau:** 9 November 2026. Bahan: naskah `Proposal_TA/naskah/DRAF_PROPOSAL_TA_v2.docx`, Lampiran 1 (Pedoman Anotasi), kode `App/`, korpus, dan laporan evaluasi di `App/output/`.
**Peran:** pembimbing (apa yang harus dibenahi) sekaligus penguji (apa yang akan ditanyakan di sidang).

---

## 1. Penilaian Umum

Kekuatan utama proposal ini adalah **artefaknya sudah berjalan dari ujung ke ujung** dan bisa diuji: naskah masuk, struktur terdeteksi, naskah keluar rapi, dan hasilnya terbuka di Microsoft Word. Itu jarang ada di tahap proposal. Desain evaluasinya juga sudah benar secara prinsip: data dibagi per naskah, ada uji ablasi, ada uji keutuhan isi, dan macro-F1 dipakai sebagai metrik utama.

Kelemahan utamanya ada di **validitas angka**, bukan di sistem. Saat ini ada tiga hal yang membuat angka evaluasi belum bisa dipertahankan di depan penguji: (1) label belum diperiksa manusia, (2) naskah uji sudah ikut dipakai untuk menyempurnakan aturan Agen 2, dan (3) data uji terlalu kecil untuk menghasilkan angka setajam dua desimal.

**Kesimpulan:** layak maju seminar proposal **setelah butir K1–K6 di bawah dibereskan**. Butir P1–P10 wajib selesai sebelum sidang akhir.

Posisi angka saat ini (naskah uji U01–U02, macro-F1), untuk rujukan:

| Konfigurasi | Naskah asli | Naskah heading polos |
|---|:---:|:---:|
| Agen 1 saja (Random Forest) | 93,79 | 92,41 |
| Aturan Agen 2 saja | 96,79 | 94,16 |
| Sistem multi-agen | 98,90 | 96,35 |

Angka ini **belum boleh dikutip sebagai hasil penelitian**. Alasannya ada di K1 dan K2.

---

## 2. Temuan Kritis — wajib sebelum seminar proposal

### K1. Label belum dari manusia, dan berisiko melingkar
**Masalah.** Proposal berjanji label adalah "anotasi manual … diperiksa dan dikoreksi seluruhnya oleh anotator" (Bab III), dan menyebut korpus berlabel manusia sebagai kontribusi (Bab I, celah kedua). Kenyataannya, label sekarang adalah pra-label aturan yang dikoreksi dengan bantuan AI.

Yang lebih berbahaya adalah **lingkaran**: pra-label dibuat dari aturan yang mirip dengan aturan Agen 2. Kalau label "mewarisi" cara pandang aturan, wajar konfigurasi "aturan Agen 2 saja" mendapat 96,8% dan sistem multi-agen 98,9%. Sistem dinilai dengan kunci jawaban yang sebagian disusun oleh dirinya sendiri. Penguji yang jeli akan langsung menanyakan ini.

**Yang harus dilakukan.**
1. Periksa **setiap baris** naskah uji U01 dan U02 (2.664 baris, sekitar 3–4 jam), lalu naskah latih. Buka naskah di Word berdampingan dengan Excel, sesuai Pedoman Bagian 7.
2. Catat berapa persen label yang kamu ubah. Angka ini menjadi ukuran seberapa jauh label awal bias ke aturan, dan layak dilaporkan.
3. Anotator kedua melabel ulang minimal 20% paragraf **tanpa melihat Label Awal**. Hitung Cohen's kappa dengan target ≥ 0,80. Untuk itu perlu Excel tanpa kolom Label Awal (bisa saya buatkan).
4. Tulis apa adanya di Bab III: "label awal dihasilkan aturan dan alat bantu; seluruh label diverifikasi penulis; 20% dianotasi ulang secara buta oleh anotator kedua (κ = …)".

### K2. Naskah uji sudah "terlihat" oleh aturan Agen 2
**Masalah.** Bab III menyatakan "data uji … tidak pernah digunakan dalam pelatihan maupun penyusunan aturan Agen 2". Pada 9 November 2026, sebagian aturan Agen 2 dan perbaikan Formatter dirumuskan setelah melihat kegagalan di U01/U02: baris daftar isi "BAB 1 PENDAHULUAN 1", judul bab bernomor otomatis, bookmark caption, dan paragraf kosong. Aturannya umum dan masuk akal, tapi **prosedurnya melanggar pernyataan validitas proposal sendiri**.

**Yang harus dilakukan.**
1. Jadikan U01/U02 **data pengembangan (dev set)**, bukan data uji akhir. Laporkan angkanya sebagai "hasil pada data pengembangan".
2. Dapatkan **2–4 naskah baru** dalam format Word yang belum pernah dibuka siapa pun di proyek ini. Idealnya 2 TA + 2 proposal, sesuai rencana proposal (±4 naskah uji). Kandidat paling cepat: penulis yang sejauh ini baru menyerahkan PDF (lihat `Data/README.md`).
3. **Bekukan sistem** sebelum membuka naskah uji baru (`git tag uji-final`), lalu jalankan `evaluasi_ablasi.py` **sekali**. Kalau kemudian ada perbaikan, laporkan sebagai versi baru dengan naskah uji baru lagi.
4. Laporkan kedua angka (dev dan uji akhir). Kalau angka uji akhir turun, itu justru menunjukkan kejujuran evaluasi dan menjadi bahan pembahasan yang bagus.

### K3. Proposal tidak konsisten soal rumusan masalah
Bab I memuat **3 rumusan masalah** dan 3 tujuan, tetapi Bab III merujuk ke "rumusan masalah 4" untuk kepatuhan format dan keutuhan isi. Pilih salah satu:
- **Tambah RM4:** "Bagaimana kepatuhan format dan keutuhan isi dokumen hasil sistem terhadap Pedoman Penulisan UEU?" Tambahkan juga Tujuan 4. Saya sarankan opsi ini, karena keutuhan isi adalah klaim terkuatmu.
- Atau masukkan kepatuhan format ke RM2 dan ubah rujukan di Bab III.

### K4. Placeholder masih tertinggal di naskah
Ada **3 [KONFIRMASI DOSPEM]** (metode CRISP-DM, pedoman 2018 vs spasi, hipotesis H0/H1), **4 [ISI]** (pembanding DocuForge, rujukan dokumentasi pustaka, anotator kedua, target jurnal), dan **sekitar 8 rujukan [lengkapi]**. Naskah sempro tidak boleh memuat penanda seperti ini. Bawa ketiga pertanyaan [KONFIRMASI DOSPEM] ke bimbingan berikutnya, dan lengkapi rujukan dari Mendeley (volume, nomor, halaman, DOI).

### K5. Izin tertulis penulis naskah
Bab III dan Lampiran 4 menyatakan naskah "hanya digunakan setelah penulis memberikan izin tertulis". Pastikan **ketujuh penulis** (kode L01–L05, U01–U02) sudah menandatangani formulir sebelum angka apa pun dilaporkan. Kalau belum, minta sekarang dan simpan formulirnya di `Data/<penulis>/`. Naskah tanpa izin harus dikeluarkan dari korpus. Ini masalah etika, bukan teknis, dan penguji bisa meminta buktinya.

### K6. Komposisi korpus berbeda dari rencana
| | Proposal | Kenyataan |
|---|---|---|
| Jumlah naskah | ±10 (±5 TA, ±5 proposal) | 7 (6 TA, 1 proposal) |
| Pembagian | ±6 latih, ±4 uji (2 TA + 2 proposal) | 5 latih, 2 uji (keduanya TA) |
| Dokumen uji regresi | 5 (P1–P5) | 4 (P4 dikeluarkan) |
| Ciri metadata | 20 | 37 (20 + 7 gaya Word + 10 pola teks) |

Sesuaikan teks proposal dengan kenyataan, atau kejar targetnya. Kalau tidak dikejar, tambahkan kalimat bahwa proposal dan TA memakai aturan format yang sama, sehingga satu jenis naskah mewakili keduanya.

---

## 3. Temuan Penting — wajib sebelum sidang akhir

**P1. Angka dari data uji kecil itu rapuh.** Di U01–U02 hanya ada 9 judul bab dan 16 entri pustaka. Satu kesalahan judul bab mengubah F1 kelas itu sekitar 11 poin. Laporkan per naskah, dan tambahkan **interval kepercayaan bootstrap** (resampling per naskah, atau per paragraf bila naskahnya sedikit). Hindari kesan presisi palsu: "sekitar 94%" lebih jujur daripada "93,79%" dari dua naskah.

**P2. Ekspektasi ablasi perlu uji statistik.** Ini sekaligus menjawab [KONFIRMASI DOSPEM] tentang hipotesis. Usulan:
H0: proporsi paragraf yang benar pada sistem multi-agen sama dengan Agen 1 saja.
H1: sistem multi-agen lebih tinggi.
Uji: **McNemar** berpasangan per paragraf (keduanya menilai paragraf yang sama). Karena paragraf dalam satu naskah tidak saling bebas, tambahkan perbandingan per naskah sebagai pendukung.

**P3. Jelaskan kenapa akurasi dan macro-F1 kadang berlawanan.** Pada naskah polos, akurasi sistem multi-agen (97,8%) lebih rendah daripada Agen 1 (98,6%), padahal macro-F1-nya lebih tinggi. Artinya Agen 2 memperbaiki kelas kecil (judul bab, caption, sampul) tapi menambah kesalahan di kelas besar. Siapkan **analisis kesalahan per kelas**: kelas mana yang diperbaiki Agen 2, kelas mana yang dirusaknya, dan contoh paragrafnya. Proposal sudah menjanjikan analisis ini (Bab IV), jadi jangan sampai hilang.

**P4. Data "heading polos" adalah simulasi.** Versi polos menghilangkan gaya Heading tetapi juga menghilangkan nomor otomatis. Ini kasus ekstrem, dan belum tentu mewakili naskah nyata yang tidak memakai gaya. Jangan mengklaim "tangguh untuk naskah tanpa gaya" hanya dari data simulasi. Kalau bisa, cari 1–2 naskah asli yang judulnya hanya ditebalkan, lalu uji. Tulis juga kasus gagal yang diketahui: di versi polos L05, sub-bab "Hasil" masih terbaca sebagai judul bab.

**P5. Model bergantung pada gaya Word, dan itu harus dibuktikan aman.** Fitur gaya Word menaikkan macro-F1 uji silang dari 84 ke 90. Penguji bisa bertanya: "kalau mahasiswa tidak memakai gaya, apakah sistem gagal?" Jawabanmu adalah eksperimen polos (P4). Sajikan **tabel ablasi fitur**: dasar, +gaya, +pola, +keduanya, +pelatihan dengan versi polos. Sebagian angkanya sudah ada di Logbook Sesi 31, tapi dihitung sebelum label diselaraskan dengan pedoman. Jalankan ulang sebelum dikutip.

**P6. SQA 100% berisiko melingkar.** Agen 2 memeriksa hasil Formatter dengan aturan yang sama dengan yang ditulis Formatter, jadi nilai 100% memang bisa diduga. Proposal sudah menjanjikan "diverifikasi manual di Microsoft Word". Buat **lembar cek manual** untuk 8 kriteria (margin, font, spasi, penomoran halaman, header, dan seterusnya), lalu periksa beberapa halaman sampel per dokumen secara visual. Lebih kuat lagi kalau dosen atau teman yang memeriksa.

**P7. Pertanyaan spasi pedoman 2018 belum dijawab.** Pedoman 2018 menetapkan spasi 1,15 dengan 0 pt sebelum/sesudah. Asdoku memakai 6 pt (isi) dan 12/6 pt (sub-bab), dan kriteria SQA 4–5 ikut memeriksa nilai Asdoku sendiri. Selama belum ada jawaban fakultas, "kepatuhan format" diukur terhadap asumsimu sendiri. Minta jawaban tertulis (template terbaru atau konfirmasi pembimbing) lalu sesuaikan kodenya.

**P8. Active Learning dijelaskan panjang tapi tidak dievaluasi.** Bab II menjelaskan Active Learning, dan sistem menjalankannya, tetapi tidak ada rumusan masalah atau metrik untuknya. Di Vercel, pelatihan ulangnya juga dilewati karena korpus tidak ikut di-deploy. Pilih salah satu: (a) evaluasi dengan simulasi (tambah label manual bertahap pada naskah latih, ukur macro-F1 di dev set), atau (b) turunkan posisinya menjadi fitur pendukung yang tidak dievaluasi, dan kurangi porsinya di Bab II.

**P9. Black-box KF-01 sampai KF-09 belum didefinisikan di proposal.** Bab III merujuk ke kebutuhan fungsional ini, tetapi daftarnya ada di BRD Kapita Selekta, bukan di proposal. Masukkan tabel KF ke proposal (Bab III atau lampiran), lalu siapkan tabel skenario uji, hasil yang diharapkan, dan hasil sebenarnya.

**P10. Batasan generalisasi.** Semua naskah berasal dari FIK UEU, berformat Word, dan berbahasa Indonesia. Daftar nama bab di Agen 2 juga disesuaikan dengan pedoman 2018 dan panduan proposal fakultas. Tulis eksplisit di batasan masalah dan saran: untuk fakultas lain, daftar nama bab dan aturan format perlu dibuat bisa dikonfigurasi.

---

## 4. Pertanyaan yang Kemungkinan Muncul di Sidang (dan Bahan Jawabannya)

1. **"Kenapa tidak pakai LLM atau IndoBERT?"** Data berlabel sedikit (7 naskah), sistem harus berjalan murah di server biasa (Vercel), dan keputusannya harus bisa dijelaskan per fitur. Algoritma klasik kompetitif untuk data kecil (Ali et al., 2024). LLM sudah disebut sebagai saran untuk TA-2.
2. **"Akurasi 98%, apa artinya kalau paragraf isi saja sudah lebih dari separuh data?"** Karena itu metrik utamanya macro-F1, bukan akurasi. Tunjukkan baseline "tebak semua paragraf isi": akurasinya sudah 67,8% di naskah uji, padahal tidak menemukan satu pun judul.
3. **"Bagaimana Anda tahu labelnya benar?"** Jawab dengan K1: verifikasi penuh oleh penulis ditambah kappa anotator kedua. Tanpa ini, pertanyaan ini tidak bisa dijawab.
4. **"Apakah data uji pernah dilihat selama pengembangan?"** Jawab dengan K2: U01/U02 dijadikan dev set, uji akhir memakai naskah baru, dan sistem dibekukan dengan tag git.
5. **"Apa bukti agen kedua memang perlu?"** Tabel ablasi ditambah uji McNemar (P2), ditambah contoh konkret kesalahan Agen 1 yang diperbaiki Agen 2 (judul bab tanpa kata BAB, baris daftar isi, sistematika penulisan).
6. **"Apakah ada isi naskah yang hilang?"** Tunjukkan `eval_keutuhan.md`: gambar, tabel, rumus, sitasi, dan catatan kaki sama persis, dan cakupan teks 100%. Ceritakan juga bug yang sempat ditemukan (gambar di caption, sitasi di caption, rujukan silang) sebagai bukti bahwa uji ini benar-benar menangkap masalah.
7. **"Kenapa Random Forest, bukan XGBoost?"** Macro-F1 uji silang per naskah tertinggi (94,7 vs 91,7), simpangannya lebih kecil (4,2 vs 7,6), dan bisa di-deploy di Vercel.
8. **"Apa bedanya dengan pemeriksa format yang sudah ada (Castrena, Kolinu, Putra)?"** Mereka melaporkan kesalahan, sedangkan Asdoku juga memperbaikinya. Asdoku tidak bergantung pada pencocokan string karena memakai model berbasis fitur dan konteks. Isinya pun utuh, dan itu diukur.
9. **"Bagaimana kalau mahasiswa memakai template fakultas lain?"** Lihat P10. Sebut sebagai keterbatasan, dan usulkan aturan yang bisa dikonfigurasi untuk TA-2.
10. **"Berapa waktu yang dihemat?"** Saat ini belum diukur. Jujur saja: pengukuran waktu dan uji kegunaan (SUS) masuk saran TA-2, sesuai Bab V.

---

## 5. Saran Teknis (sistem)

1. **Render judul dan caption dari isi aslinya.** Hampir semua kehilangan isi yang ditemukan terjadi pada elemen yang dibangun ulang dari teks: caption, judul, sub-bab. Arah yang lebih aman: salin paragraf asli, lalu ganti gaya dan nomornya saja. Isi seperti sitasi, gambar, dan bookmark otomatis terbawa. Ini jalan tengah antara "menyalin ke templat" dan "memperbaiki langsung di berkas asli". Cocok dibahas sebagai keputusan desain di Bab IV, atau dijadikan rencana TA-2.
2. **Aturan pedoman dalam berkas konfigurasi.** Daftar nama bab, frasa sampul, dan nilai spasi sekarang ditulis langsung di kode (`academic_rules.py`, `critic.py`). Pindahkan ke satu berkas konfigurasi (YAML) per pedoman. Generalisasi ke fakultas lain jadi mudah, dan jawaban fakultas soal spasi (P7) cukup diubah di satu tempat.
3. **Ambang 0,8 untuk nama bab di luar daftar** dipilih tanpa dasar data. Tetapkan dari data latih (uji silang), atau sebut sebagai parameter yang diuji kepekaannya.
4. **Kalibrasi keyakinan model.** Antrean Active Learning dan ambang di atas memakai probabilitas Random Forest, yang biasanya tidak terkalibrasi. Pertimbangkan kalibrasi isotonic/Platt, atau minimal laporkan diagram reliabilitas.
5. **Reprodusibilitas.** Kunci versi pustaka di `requirements*.txt`, simpan seed (sudah ada `RANDOM_STATE`), dan tag commit yang menghasilkan angka di skripsi. Setiap tabel Bab IV harus bisa dibuat ulang dari satu perintah. Urutan perintahnya sudah ada di `README.md`.
6. **Uji otomatis untuk keutuhan.** Jalankan `evaluasi_keutuhan.py` pada P1–P5 di dalam `tests/`, supaya setiap perubahan Formatter langsung tertangkap kalau menghilangkan isi.

---

## 6. Rencana Aksi (urut prioritas)

| No | Kegiatan | Siapa | Perkiraan | Batas |
|---|---|---|---|---|
| 1 | Bersihkan placeholder, tambah RM4/Tujuan 4, sesuaikan angka korpus dan jumlah fitur di proposal (K3, K4, K6) | Kamu | 1 hari | Sebelum sempro |
| 2 | Pastikan 7 formulir izin bertanda tangan (K5) | Kamu | 2–3 hari | Sebelum sempro |
| 3 | Bawa 3 pertanyaan [KONFIRMASI DOSPEM] + pertanyaan spasi ke bimbingan (K4, P7) | Kamu | 1 sesi | Sebelum sempro |
| 4 | Verifikasi seluruh label U01–U02, lalu L01–L05 (K1) | Kamu | 1–2 hari | Sebelum sempro (minimal U01–U02) |
| 5 | Minta naskah Word baru untuk uji akhir (K2) | Kamu | 1–2 minggu | Sebelum TA-2 berjalan |
| 6 | Anotator kedua 20% + kappa (K1) | Teman/dosen | 1 hari | Sebelum sidang |
| 7 | Bekukan sistem, uji akhir sekali, bootstrap CI, McNemar, analisis kesalahan (K2, P1–P3) | Kamu + Claude | 2 hari | Sebelum sidang |
| 8 | Ablasi fitur dan naskah polos nyata (P4, P5) | Kamu + Claude | 1 hari | Sebelum sidang |
| 9 | Lembar cek manual 8 kriteria + black-box KF-01–KF-09 (P6, P9) | Kamu | 1–2 hari | Sebelum sidang |
| 10 | Putuskan nasib Active Learning: evaluasi atau turunkan klaim (P8) | Kamu + dospem | — | Sebelum sidang |

---

## 7. Kondisi Repositori per 9 November 2026

- Peta folder dan alur kerja: `README.md` (akar).
- Laporan evaluasi: `App/output/eval_report_korpus.md` (model), `eval_ablasi.md` (RM3), `eval_keutuhan.md` (keutuhan isi).
- Pedoman Anotasi naik ke **v1.1** (K10: baris daftar isi = `LAINNYA`) dan korpus diselaraskan: 158 baris disesuaikan dengan K3/K7/K8/K14.
- Catatan lengkap perubahan: `Document/LOGBOOK_PROGRES.md` Sesi 31.
