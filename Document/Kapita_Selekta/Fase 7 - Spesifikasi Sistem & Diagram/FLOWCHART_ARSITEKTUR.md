# FASE 7: SPESIFIKASI SISTEM & DIAGRAM ALIR PROSES (FLOWCHART SYSTEM)
## Multi-Agent System untuk Otomatisasi Deteksi Struktur dan Formatting Dokumen Akademik Berbasis NLP (ASDOKU)

> **Kode Dokumen:** `SPEC-ASDOKU-2026-F7`  
> **Mata Kuliah:** Kapita Selekta — FASILKOM Universitas Esa Unggul  
> **Penyusun:** Arditya Adjie Rosandi (NIM: 20230801274)  
> **Program Studi / Institusi:** Teknik Informatika, Fakultas Ilmu Komputer (FASILKOM) — Universitas Esa Unggul  
> **Regulasi Acuan:** SK Rektor Universitas Esa Unggul No. 5 Tahun 2018 (Pedoman Penulisan Skripsi & Tugas Akhir)  
> **Dokumen Terkait:** [BRD_Business_Requirements_Document.md](file:///root/Gammaura/Skripsi/Document/Kapita_Selekta/Fase%203%20-%20Dokumen%20BRD/BRD_Business_Requirements_Document.md), [SLR_Systematic_Literature_Review.md](file:///root/Gammaura/Skripsi/Document/Kapita_Selekta/Fase%204%20-%20Dokumen%20SLR/SLR_Systematic_Literature_Review.md), [Evidence_Matrix_Scopus.md](file:///root/Gammaura/Skripsi/Document/Kapita_Selekta/Fase%202%20-%20Penelusuran%20Literatur%20&%20Evidence%20Matrix/Evidence_Matrix_Scopus.md), [Gap_Analysis_dan_Penetapan_Judul.md](file:///root/Gammaura/Skripsi/Document/Kapita_Selekta/Fase%205%20-%20Analisis%20Gap%20&%20Penetapan%20Judul/Gap_Analysis_dan_Penetapan_Judul.md), dan [Audit_Kritis_BRD_SLR_Portofolio.md](file:///root/Gammaura/Skripsi/Document/Kapita_Selekta/Fase%206%20-%20Uji%20Kesesuaian%20&%20Kritik%20Keras/Audit_Kritis_BRD_SLR_Portofolio.md)  
> **Tanggal Penyusunan:** 21 Oktober 2026  
> **Status Dokumen:** Final Spesifikasi Sistem & Flowchart (Fase 7 — Telah Disinkronisasi Penuh: 420 Dimensi Fitur Hibrida & Akurasi Puncak 97,22%)

---

## 1. Kode Mermaid.js (Siap Copy-Paste ke Draw.io / Mermaid Live Editor)

Kode Mermaid.js untuk *Flowchart / Process Diagram* Sistem ASDOKU di bawah ini mencakup keempat tahapan utama secara berurutan, dengan sintaks yang 100% valid untuk langsung ditempel (*paste*) ke Draw.io (**Arrange** $\rightarrow$ **Insert** $\rightarrow$ **Advanced** $\rightarrow$ **Mermaid**) maupun **Mermaid Live Editor** ([mermaid.live](https://mermaid.live)):

```mermaid
flowchart TD
    %% ==========================================
    %% DEFINISI STYLE VISUAL (WARM & CLEAN)
    %% ==========================================
    classDef inputStyle fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef agent1Style fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef agent2Style fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef agent3Style fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#4A148C
    classDef evalStyle fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef uiStyle fill:#E0F2F1,stroke:#00695C,stroke-width:2px,color:#004D40
    classDef decisionStyle fill:#FFFFFF,stroke:#37474F,stroke-width:2px,color:#263238

    %% ==========================================
    %% 1. NODE INPUT DATA & PREPROCESSING
    %% ==========================================
    subgraph S1 ["1. INPUT DATA & PREPROCESSING"]
        direction TB
        IN1(["Unggah Dokumen Akademik Mentah (.docx)<br/>via FastAPI Web Interface"])
        PRE1["Validasi Skema & Pembacaan Non-Destruktif<br/>Pohon DOM OpenXML (python-docx / lxml)"]
        PRE2["Segmentasi Elemen Paragraf (w:p),<br/>Tabel (w:tbl), dan Gambar (w:drawing)"]
        PRE3["Ekstraksi 420 Fitur Hibrida:<br/>400 Dimensi TF-IDF N-Gram (1,2) +<br/>20 Fitur Metadata Spasial OpenXML"]

        IN1 --> PRE1 --> PRE2 --> PRE3
    end

    %% ==========================================
    %% 2. EKSEKUSI ALGORITMA & PROSES BISNIS UTAMA (TRI-AGENT)
    %% ==========================================
    subgraph S2 ["2. EKSEKUSI ALGORITMA UTAMA (TRI-AGENT SYSTEM)"]
        direction TB
        
        subgraph A1_BOX ["Agent 1: Inspector (Klasifikasi ML Murni, Tanpa Aturan)"]
            A1_1["Inferensi Model Random Forest (Balanced)<br/>vs Baseline Logistic Regression"]
            A1_2["Penyusunan Draft Blueprint Struktur<br/>& Perhitungan Confidence Score"]
            A1_3{"Confidence Score<br/>&lt; 0.70?"}
            A1_4["Tandai Status:<br/>is_ambiguous = True"]
            A1_5["Tandai Status:<br/>is_ambiguous = False"]
            
            A1_1 --> A1_2 --> A1_3
            A1_3 -- "Ya" --> A1_4
            A1_3 -- "Tidak" --> A1_5
        end

        subgraph A2_BOX ["Agent 2: Quality Critic (Rule-Based, SQA Tier 1 - Blueprint Gate)"]
            A2_1["Rule Prior per Paragraf (^BAB, Judul Baku, Caption)<br/>& Audit Urutan Bab Monotonik (Bab I -> II -> III)"]
            A2_2["Eksekusi 5 Lapisan Guardrail:<br/>Karantina Frontmatter, Isolasi Sub-bab 1.7,<br/>Filter Rumus & Caption Gambar/Tabel"]
            A2_3{"Blueprint Konsisten<br/>(Tanpa Koreksi Baru)?"}
            A2_4["Kirim Feedback Directives:<br/>Agent 1 Terapkan Koreksi, Lalu Diaudit Ulang (Maks. 3x)"]
            A2_5["Hasilkan Approved Blueprint"]
            
            A2_1 --> A2_2 --> A2_3
            A2_3 -- "Tidak (Anomali)" --> A2_4
            A2_3 -- "Ya (Valid)" --> A2_5
        end

        subgraph A3_BOX ["Agent 3: Formatting Actuator (Rekonstruksi OpenXML)"]
            A3_1["Salin-lalu-Normalisasi (Zero-Loss):<br/>Sitasi Mendeley, Footnote, Italic Tetap Utuh;<br/>Hanya Spasi, Indentasi & Font yang Diseragamkan"]
            A3_2["Rekonstruksi Cover Resmi UEU (Logo 3.0 cm)<br/>& Isolasi 3 Section (link_to_previous = False)"]
            A3_3["Injeksi Dual Page Numbering (Romawi i,ii vs Latin 1,2)<br/>& Tag &lt;w:outlineLvl&gt; Heading 1-3 ke Navigation Pane"]
            A3_4["Generate Dynamic TOC (&lt;w:updateFields&gt;)<br/>& Standarisasi Tabel APA 7th Edition"]
            
            A3_1 --> A3_2 --> A3_3 --> A3_4
        end

        PRE3 --> A1_1
        A1_4 --> A2_1
        A1_5 --> A2_1
        A2_4 -->|"Loop Koreksi Tier 1"| A1_2
        A2_5 --> A3_1
    end

    %% ==========================================
    %% 3. EVALUASI METRIK, SQA TIER 2 & ACTIVE LEARNING
    %% ==========================================
    subgraph S3 ["3. EVALUASI METRIK, SQA TIER 2 & MODEL OUTPUT"]
        direction TB
        EV1["Evaluasi Performa Model Klasifikasi NLP:<br/>Accuracy (97,22%), Macro/Weighted F1 (0,97),<br/>& Confusion Matrix"]
        EV2["Audit Fisik SQA Tier 2 (Artifact Acceptance Gate):<br/>Verifikasi 8 Kriteria SK Rektor UEU No. 5/2018<br/>(Margin 4-3-3-3, Kertas A4, Spasi 1.15, Header, APA 7)"]
        EV3{"Lolos 8/8<br/>Kriteria?"}
        EV4["Ulangi Penyusunan Format<br/>(Berhenti Bila Cacat Tidak Berubah)"]
        
        AL0["Kueri Paragraf Ambigu ke Pengguna<br/>(Least-Confidence, Maks. 20) → Label Manual"]
        AL1["Catat Weak Label Agent 2<br/>(Untuk Analisis, Tidak Memicu Retraining)"]
        AL2{"Label Manual Baru<br/>>= 5?"}
        AL3["Retraining + Uji Non-Regresi:<br/>Hot-Reload Hanya Bila Macro-F1 Tidak Turun"]
        
        A2_4 -.->|"Catat Koreksi Label"| AL1
        A1_4 -.->|"Ambigu & Tak Dipastikan Aturan"| AL0
        AL0 --> AL2
        AL2 -- "Ya" --> AL3
        AL3 -.->|"Update Bobot Model"| A1_1
        
        A3_4 --> EV1 --> EV2 --> EV3
        EV3 -- "Belum (Ada Cacat)" --> EV4
        EV4 -->|"Loop Remediasi Tier 2"| A3_2
    end

    %% ==========================================
    %% 4. OUTPUT VISUAL & USER INTERFACE
    %% ==========================================
    subgraph S4 ["4. OUTPUT VISUAL & USER INTERFACE (WEB STUDIO)"]
        direction TB
        UI1["Render Live Execution Terminal Log<br/>& Visualisasi Pipeline Antar-Agen (alat.html)"]
        UI2["Tampilkan Skor 8 Kriteria, Sisa Cacat,<br/>Waktu Proses & Kartu Kueri Paragraf Ambigu"]
        UI3(["Unduh Dokumen Akademik Terformat:<br/>(Asdoku) - Nama_File.docx"])
        
        EV3 -- "Lulus (PASS 8/8)" --> UI1
        EV4 -.->|"Cacat Tak Berubah: Dilaporkan"| UI1
        UI1 --> UI2 --> UI3
    end

    %% ==========================================
    %% PENERAPAN CLASS STYLE KE NODE
    %% ==========================================
    class IN1,PRE1,PRE2,PRE3 inputStyle
    class A1_1,A1_2,A1_4,A1_5 agent1Style
    class A2_1,A2_2,A2_4,A2_5 agent2Style
    class A3_1,A3_2,A3_3,A3_4 agent3Style
    class EV1,EV2,EV4,AL0,AL1,AL3 evalStyle
    class UI1,UI2,UI3 uiStyle
    class A1_3,A2_3,EV3,AL2 decisionStyle
```

---

## 2. Panduan Cara Menggunakan di Draw.io / Diagrams.net

1. Buka peramban dan akses **[app.diagrams.net](https://app.diagrams.net/)** (atau aplikasi Draw.io Desktop).
2. Buat diagram baru atau buka dokumen kerja yang sudah ada.
3. Klik menu **Arrange (Atur)** $\rightarrow$ **Insert (Sisipkan)** $\rightarrow$ **Advanced (Lanjutan)** $\rightarrow$ **Mermaid...**
4. Hapus teks kode bawaan, lalu tempelkan (*paste*) seluruh blok kode Mermaid di atas (tanpa tanda pagar pembungkus ```mermaid).
5. Klik **Insert** — diagram alir akan otomatis ter-render lengkap dengan warna kategori per modul (*Input* Biru, *Agent 1* Hijau, *Agent 2* Kuning/Oranye, *Agent 3* Ungu, *Evaluasi/SQA* Merah, dan *UI* Toska).
6. Untuk ekspor ke skripsi: Klik **File** $\rightarrow$ **Export as** $\rightarrow$ **PNG** (centang *Transparent Background*, DPI 300 untuk cetak berkualitas tinggi) atau **SVG** (format vektor tajam).

---

## 3. Keterangan Pemetaan 4 Komponen Diagram (Untuk Penjelasan di Bab III Skripsi)

### Blok 1 (Input Data & Preprocessing)
Memvisualisasikan proses unggah berkas `.docx` melalui antarmuka FastAPI (**FR-01**), pembacaan pohon DOM OpenXML secara non-destruktif (**NFR-03**), hingga ekstraksi **420 dimensi fitur hibrida** (400 fitur leksikal *TF-IDF N-Gram 1,2* + 20 atribut metadata spasial & struktural *OpenXML*) (**FR-02**).

### Blok 2 (Eksekusi Algoritma Utama — Tri-Agent System)
Memvisualisasikan alur kerja kolaboratif tiga agen:
* **Agent 1 (Inspector):** Mengklasifikasikan paragraf ke label struktur **murni dengan model Machine Learning** (tanpa aturan buatan) dan menandai ambiguitas jika *confidence score* $< 0,70$ (**FR-03, FR-04**).
* **Agent 2 (Quality Critic - SQA Tier 1):** Agen berbasis aturan yang menerapkan *rule prior* per paragraf, lalu mengaudit urutan bab monotonik ($\text{Bab I} \rightarrow \text{Bab II} \rightarrow \text{Bab III}$) serta mengeksekusi **5 Lapisan Guardrail** (karantina *frontmatter*, isolasi zona sub-bab 1.7 Sistematika Penulisan, filter proteksi rumus & *caption*) (**FR-05 s/d FR-08**). Koreksi dikirim ke *Agent 1* untuk diterapkan, lalu *blueprint* diaudit ulang sebagai uji konsistensi (maks. 3 iterasi); model tidak memprediksi ulang.
* **Agent 3 (Formatting Actuator):** Menyalin paragraf sumber secara utuh lalu menormalisasi spasi, indentasi, dan font (*zero-loss*: sitasi Mendeley, catatan kaki, hyperlink, dan cetak miring tetap utuh); melakukan sanitasi pohon DOM OpenXML (penghapusan tag `<w:numPr>` liar), rekonstruksi sampul resmi UEU (logo 3.0 cm), isolasi 3 *section* (`link_to_previous = False`) untuk *dual page numbering*, injeksi `<w:outlineLvl>` untuk *Heading 1–3* ke *Navigation Pane*, pembuatan *Dynamic TOC*, dan standarisasi tabel APA 7th Edition (**FR-09 s/d FR-13**).

### Blok 3 (Evaluasi Metrik, SQA Tier 2 & Active Learning)
Memvisualisasikan evaluasi komprehensif performa sistem:
* **Pengukuran Model Klasifikasi NLP:** Akurasi puncak **97,22%**, Macro/Weighted F1-Score **0,97**, serta *Confusion Matrix*.
* **Audit Fisik SQA Tier 2 (*Artifact Acceptance Gate*):** Verifikasi deterministik terhadap **8 Kriteria Mutu SK Rektor UEU No. 5 Tahun 2018** (Margin 4-3-3-3 cm, ukuran kertas A4, spasi 1.15, header/footer, dan format tabel APA 7) (**FR-14**). Jika ditemukan cacat, *Agent 3* menyusun ulang dokumen; pengulangan dihentikan bila cacat tidak berubah, dan sisa cacat dilaporkan apa adanya kepada pengguna.
* **Siklus Active Learning (*uncertainty sampling*):** Paragraf ambigu yang tidak dapat dipastikan aturan *Agent 2* ditanyakan kepada pengguna (maks. 20 per dokumen, keyakinan terendah lebih dulu). Setiap $\ge 5$ label manual baru memicu pelatihan ulang dengan **uji non-regresi**: model baru hanya di-*hot-reload* bila macro-F1 pada data uji basis tidak turun. Koreksi otomatis *Agent 2* dicatat sebagai *weak label* tetapi tidak memicu pelatihan, karena terbukti menurunkan macro-F1 (0,920 → 0,694) (**FR-15, NFR-04**).

### Blok 4 (Output Visual & User Interface)
Memvisualisasikan antarmuka Web Studio FastAPI (`alat.html` & `alat.js`):
* Penayangan konsol log eksekusi terminal *real-time* dan status interaksi antar-agen.
* Kartu skor kepatuhan mutu SQA Tier 2 (jumlah kriteria lolos dari 8 beserta sisa cacat) dan waktu pemrosesan (0,79 – 1,83 detik pada 5 dokumen uji, 27-10-2026).
* Kartu konfirmasi paragraf ambigu untuk menjawab kueri *Active Learning*.
* Tombol unduh instan berkas hasil rekonstruksi yang dinamai otomatis `(Asdoku) - Nama_File.docx` (**FR-16**).

---

## 4. Opsi Alternatif: Alur Horizontal Ringkas (Slide Presentasi Sempro/Sidang 16:9)

Untuk kebutuhan slide presentasi PowerPoint / Canva dengan aspek rasio 16:9, diagram di bawah ini mengemas interaksi secara horizontal (*left-to-right*):

```mermaid
flowchart LR
    classDef inputStyle fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef agent1Style fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef agent2Style fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef agent3Style fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#4A148C
    classDef evalStyle fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef uiStyle fill:#E0F2F1,stroke:#00695C,stroke-width:2px,color:#004D40

    subgraph IN ["1. Input & Preprocessing"]
        A["Dokumen Mentah (.docx)"] --> B["Ekstraksi 420 Fitur<br/>(400 TF-IDF + 20 OpenXML)"]
    end

    subgraph MAS ["2. Eksekusi Tri-Agent & Two-Tier SQA"]
        B --> C["Agent 1: Inspector<br/>(Random Forest, ML Murni)"]
        C <-->|"SQA Tier 1:<br/>Koreksi Aturan + Uji Konsistensi"| D["Agent 2: Quality Critic<br/>(Rule-Based Gatekeeper & Auditor)"]
        D -->|"Approved<br/>Blueprint"| E["Agent 3: Actuator<br/>(OpenXML Zero-Loss)"]
        E <-->|"SQA Tier 2:<br/>8 Kriteria UEU"| D
    end

    subgraph EVAL ["3. Evaluasi & Active Learning"]
        D -. "Kueri Ambigu → Label Manual" .-> F["Active Learning Pool<br/>(Retrain + Uji Non-Regresi)"]
        F -.-> C
        D --> G["Evaluasi Metrik:<br/>Akurasi 97.22% | Skor SQA 8 Kriteria"]
    end

    subgraph OUT ["4. Output & Web UI"]
        G --> H["Web Studio FastAPI:<br/>Log, SQA Card & Download<br/>(Asdoku) - Hasil.docx"]
    end

    class A,B inputStyle
    class C agent1Style
    class D agent2Style
    class E agent3Style
    class F,G evalStyle
    class H uiStyle
```

---

> **Pernyataan Pengesahan Fase 6:**  
> Berkas diagram alir dan spesifikasi sistem ini merupakan luaran resmi Fase 6 mata kuliah Kapita Selekta, siap diadopsi penuh sebagai diagram utama arsitektur sistem pada Bab III (Metodologi Penelitian) Proposal Tugas Akhir Program Studi Teknik Informatika, Fakultas Ilmu Komputer, Universitas Esa Unggul.
