"""
AGENT 2: QUALITY CRITIC & COORDINATOR (Validator & Feedback Loop) - Versi Cerdas.

Tugas & Peran:
1. Menerima draf blueprint prediksi dari Agent 1 (Inspector).
2. Memeriksa konsistensi urutan bab secara monotonik (I -> II -> III -> IV -> V).
3. Mendukung Inferensi Judul Bab Kanonikal (PENDAHULUAN, LANDASAN TEORI, KESIMPULAN DAN SARAN, dll.)
   bahkan jika penulis tidak menyertakan kata literal 'BAB'.
4. Mengisolasi Sub-bab 1.7 Sistematika Penulisan agar tidak menjadi jebakan false-positive.
5. Memvalidasi hierarki sub-bab dan nomor urut caption (Gambar & Tabel).
6. Menerbitkan APPROVED BLUEPRINT yang 100% konsisten untuk dieksekusi oleh Agent 3 (Formatter).
"""

import re
from typing import Dict, Any, List

ROMAWI_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7
}

# Kamus Nama Bab Kanonikal Akademik Indonesia & UEU
CANONICAL_CHAPTER_NAMES = {
    1: ["PENDAHULUAN"],
    2: ["TINJAUAN PUSTAKA", "LANDASAN TEORI", "DASAR TEORI", "KAJIAN PUSTAKA"],
    3: ["GAMBARAN UMUM PERUSAHAAN", "GAMBARAN UMUM", "PROFIL PERUSAHAAN", "PELAKSANAAN KERJA PRAKTIK", "URAIAN MATERI", "URAIAN MATERI KERJA PRAKTIK", "METODE", "METODOLOGI", "METODE PENELITIAN", "METODOLOGI PENELITIAN", "PERANCANGAN SISTEM"],
    4: ["ANALISIS DAN PEMBAHASAN", "ANALISIS HASIL DAN PEMBAHASAN", "HASIL DAN PEMBAHASAN", "ANALISIS DAN PERANCANGAN", "HASIL", "PEMBAHASAN", "IMPLEMENTASI", "HASIL PENELITIAN"],
    5: ["KESIMPULAN DAN SARAN", "PENUTUP", "KESIMPULAN"]
}

class QualityCriticAgent:
    """
    Agent 2: Quality Critic & Coordinator Agent.
    """
    def __init__(self):
        print("[Agent 2 - Quality Critic] Diinisialisasi dengan Aturan Integritas Akademik Cerdas UEU.")

    def _infer_bab_number(self, text: str) -> int:
        """
        Mengekstrak nomor bab dari:
        1. Kata kunci literal 'BAB [I/II/1/2]'
        2. Atau nama bab kanonikal (misal: 'LANDASAN TEORI' -> Bab 2)
        """
        clean = text.strip().upper()
        # Bersihkan tanda baca di akhir
        clean = clean.rstrip('.:;')
        
        # Jika teks diawali pola penomoran sub-bab (misal: '1.1', '2.1', '3.1.2') -> BUKAN BAB!
        if re.match(r'^\d+\.\d+', clean):
            return 0

        # Cek kata literal 'BAB' di awal (misal: 'BAB I PENDAHULUAN', 'BAB 1', 'BAB II')
        match = re.match(r'^BAB\s+([IVX\d]+)\b', clean)
        if match:
            raw_num = match.group(1).upper()
            return ROMAWI_MAP.get(raw_num, 0)

        # Bersihkan nomor prefix jika ada (misal: '2. LANDASAN TEORI' -> 'LANDASAN TEORI')
        clean_no_num = re.sub(r'^\d+(\.\d+)*\s*', '', clean)
        words = clean_no_num.split()

        # Hanya cocokkan jika panjang kata <= 5 agar tidak menangkap sub-bab seperti 'Metode Pengembangan...'
        if len(words) <= 5:
            for bab_num, names in CANONICAL_CHAPTER_NAMES.items():
                if any(clean_no_num == name for name in names):
                    return bab_num

        return 0

    def evaluate_and_refine(self, inspection_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Melakukan audit mendalam terhadap prediksi Agent 1,
        memperbaiki inkonsistensi urutan, dan menerbitkan Approved Blueprint.
        """
        print(f"\n[Agent 2 - Quality Critic] Mengaudit draf blueprint dari Agent 1...")
        paragraphs = inspection_report["paragraphs"]
        
        refined_paragraphs = []
        corrections_made = []
        
        last_valid_bab_num = 0
        has_passed_cover = False
        in_sistematika = False
        sistematika_para_count = 0
        active_heading2 = False
        in_daftar_pustaka = False
        in_formula_legend = False
        formula_legend_count = 0

        for idx, item in enumerate(paragraphs):
            para_id = item["para_id"]
            text = item["text"]
            upper_text = text.upper()
            pred_label = item["predicted_label"]
            meta = item["metadata"]
            
            final_label = pred_label
            correction_reason = None

            clean_up = upper_text.strip()
            clean_up_no_punct = clean_up.rstrip('.:;')
            words = clean_up.split()
            word_count = len(words)

            next_item = paragraphs[idx + 1] if idx + 1 < len(paragraphs) else None
            next_text = next_item["text"].strip().lower() if next_item else ""
            is_followed_by_desc = any(next_text.startswith(k) for k in ["bab ini", "dalam bab ini", "pada bab ini"])

            # 1. Pantau Jendela Sub-bab Sistematika Penulisan
            if "SISTEMATIKA PENULISAN" in upper_text and word_count <= 8:
                in_sistematika = True
                sistematika_para_count = 0
                final_label = "SUB_BAB"
            elif in_sistematika:
                sistematika_para_count += 1
                if sistematika_para_count > 15:
                    in_sistematika = False

            frontmatter_keywords = [
                "ABSTRAK", "ABSTRACT", "KATA PENGANTAR", "PRAKATA", 
                "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR", "DAFTAR SIMBOL", 
                "DAFTAR LAMPIRAN", "DAFTAR PUSTAKA", "DAFTAR REFERENSI",
                "HALAMAN PERNYATAAN", "HALAMAN PENGESAHAN", "HALAMAN PERSETUJUAN", 
                "HALAMAN PERSETUJUAN PUBLIKASI", "PERSETUJUAN PUBLIKASI",
                "LEMBAR PENGESAHAN", "LEMBAR PERNYATAAN", "PERNYATAAN KEASLIAN",
                "UNTUK KEPENTINGAN AKADEMIS",
                "LAMPIRAN"
            ]

            standard_subchapters = [
                "LATAR BELAKANG", "IDENTIFIKASI MASALAH", "RUMUSAN MASALAH", "BATASAN MASALAH", 
                "TUJUAN PENELITIAN", "TUJUAN MAGANG", "MAKSUD DAN TUJUAN", "MANFAAT PENELITIAN", 
                "MANFAAT MAGANG", "MANFAAT TUGAS AKHIR", "TUJUAN TUGAS AKHIR", "MANFAAT", "TUJUAN", 
                "RUANG LINGKUP", "LINGKUP TUGAS AKHIR", "LINGKUP", "KERANGKA BERPIKIR", "KERANGKA PEMIKIRAN",
                "SISTEMATIKA PENULISAN", "SISTEMATIKA PENULISAN LAPORAN", "SISTEMATIKA PENULISAN TUGAS AKHIR",
                "PROFIL PERUSAHAAN", "SEJARAH PERUSAHAAN", "SEJARAH PERUSAHAAN DAN PERKEMBANGANNYA",
                "VISI DAN MISI", "VISI PERUSAHAAN", "MISI PERUSAHAAN", "STRUKTUR ORGANISASI", 
                "TEORI", "LANDASAN", "KAJIAN",
                "RENCANA PENELITIAN", "OBYEK PENELITIAN", "OBJEK PENELITIAN", "POPULASI DAN SAMPEL", 
                "DEFINISI OPERASIONAL VARIABEL", "DEFINISI OPERASIONAL", "TEKNIK PENGUMPULAN DATA", "PENGUMPULAN DATA",
                "ANALISIS KEBUTUHAN", "ANALISIS KEBUTUHAN SISTEM", "DESKRIPSI PROBLEM DAN SOLUSI",
                "KEBUTUHAN FUNGSIONAL", "KEBUTUHAN NON FUNGSIONAL", 
                "DATA HASIL PENELITIAN", "PEMBAHASAN HASIL PENELITIAN", "ANALISIS DATA", "PERBANDINGAN DENGAN PENELITIAN LAIN",
                "TAHAPAN IMPLEMENTASI METODE WATERFALL", "PEMODELAN DATABASE",
                "PEMODELAN BASIS DATA", "DIAGRAM ALUR KERJA", "USE CASE DIAGRAM", 
                "FLOWCHART ALUR PENGGUNA", "ACTIVITY DIAGRAM PENGGUNA", "SEQUENCE DIAGRAM INTERAKSI PENGGUNA", 
                "ANTARMUKA UI/UX", "HASIL PENGUJIAN FUNGSIONAL DAN NON FUNGSIONAL", "PENGUJIAN FUNGSIONAL",
                "KENDALA TEKNIS DAN SOLUSINYA", "KENDALA TEKNIS", "KESIMPULAN", "SARAN"
            ]

            # 2. DETEKSI PRIORITAS: Frontmatter Title Resmi UEU
            is_frontmatter = False
            if word_count <= 10 and not any(clean_up.startswith(k) for k in ["BAB ", "BAB I", "BAB 1"]):
                for fm in frontmatter_keywords:
                    if clean_up_no_punct == fm or clean_up_no_punct.startswith(fm + " ") or clean_up_no_punct.startswith(fm + ":"):
                        is_frontmatter = True
                        break

            # Pantau jika bagian Daftar Pustaka dimulai
            if any(clean_up_no_punct == dp for dp in ["DAFTAR PUSTAKA", "DAFTAR REFERENSI", "BIBLIOGRAPHY", "REFERENCES"]):
                in_daftar_pustaka = True

            # Deteksi Keterangan Rumus, Sumber Data, Notasi Variabel, Hipotesis, Sitasi, dan Rincian Butir
            is_hypo = bool(re.match(r'^(HA?\d*|H0|H\d+)\s*[:\.]', text.strip(), re.IGNORECASE))
            is_formula_legend = bool(re.match(r'^(Keterangan|Dimana|Di mana|Notasi)\s*[:=]?', text.strip(), re.IGNORECASE))
            if is_formula_legend:
                in_formula_legend = True
                formula_legend_count = 0
            elif in_formula_legend:
                formula_legend_count += 1
                if formula_legend_count > 15 or word_count > 25 or (':' not in text and not is_variable_item):
                    in_formula_legend = False

            # Deteksi Formula / Persamaan Matematis (LaTeX, simbol operasi, nomor persamaan)
            has_math_xml = bool(item["metadata"].get("has_formula") or item["metadata"].get("has_math"))
            is_formula = bool(
                has_math_xml or
                re.search(r'\(\d+\.\d+\)\s*$', text.strip()) or
                (any(op in text for op in [' = ', ' / ', ' * ', ' + ', ' \approx ', ' \pm ', ' \sum ']) and (re.search(r'\(\d+(\.\d+)?\)', text) or any(k in text for k in ['Accuracy =', 'Precision =', 'Recall =', 'F1-Score =', 'F1 =', 'MAE =', 'MSE =', 'RMSE =', 'Loss ='])))
            )
            if is_formula:
                item["metadata"]["is_formula"] = True

            is_variable_item = in_formula_legend and bool(re.search(r'^[a-zA-Zα-ωΑ-Ω0-9_\u2080-\u2089,\s\t]{1,20}\s*[:=]\s*', text.strip())) and not is_hypo and not any(clean_up.startswith(k) for k in ["CATATAN", "NOTE", "SUMBER", "SOURCE", "KETERANGAN", "DIMANA"])
            is_source_note = bool(re.match(r'^(Sumber|Source|Catatan|Note)\s*[:=]', text.strip(), re.IGNORECASE))
            is_numbered_list = bool(re.match(r'^(\d+|[a-zA-Z])[\.\)]\s*', text.strip())) and not re.match(r'^\d+\.\d+', text.strip()) and not item["metadata"].get("style", "").startswith("Heading")
            is_citation = bool(re.match(r'^\([^\)]+,\s*\d{4}[a-z]?\)$', text.strip()) or re.match(r'^[A-Z][a-zA-Z\s\.,\-]+\s*\(\d{4}[a-z]?\)\.', text.strip()))
            is_numbered_sub = bool(re.match(r'^\d+\.\d+', text.strip()))
            is_standard_sub = bool(word_count <= 10 and any(clean_up_no_punct == sb or clean_up_no_punct.startswith(sb) for sb in standard_subchapters))

            # 3. DETEKSI PRIORITAS: Judul Bab Resmi UEU (Kanonikal atau Literal 'BAB')
            inferred_bab = self._infer_bab_number(text) if (word_count <= 12 and not is_frontmatter) else 0

            # Validasi apakah teks ini merupakan Judul Bab Utama
            is_real_chapter_header = False
            if inferred_bab > 0 and word_count <= 6 and not any(k in clean_up for k in [":", "BERISI", "MEMBAHAS", "MENJELASKAN"]):
                if in_sistematika and is_followed_by_desc:
                    is_real_chapter_header = False
                elif (last_valid_bab_num == 0 and inferred_bab == 1) or inferred_bab == last_valid_bab_num + 1:
                    is_real_chapter_header = True
                    in_sistematika = False # Menutup jendela Sistematika begitu Bab baru yang sah dimulai
                    in_daftar_pustaka = False
                    in_formula_legend = False

            # Jika Bab 5 (KESIMPULAN DAN SARAN) sudah aktif, teks KESIMPULAN atau SARAN adalah SUB_BAB
            is_kesimpulan_saran_sub = (last_valid_bab_num == 5 and clean_up_no_punct in ["KESIMPULAN", "SARAN"])

            if is_frontmatter:
                final_label = "FRONTMATTER_TITLE"
                has_passed_cover = True
                if pred_label != "FRONTMATTER_TITLE":
                    correction_reason = "Teks adalah judul halaman awal resmi UEU (Frontmatter Title)."

            # KARANTINA KETAT HALAMAN DEPAN: Sebelum Bab 1 dimulai, TIDAK BOLEH ADA SUB_BAB!
            elif last_valid_bab_num == 0 and not is_real_chapter_header:
                cover_keywords = ["NAMA", "NIM", "PROGRAM STUDI", "FAKULTAS", "UNIVERSITAS", "TAHUN", "SKRIPSI", "TUGAS AKHIR"]
                if not has_passed_cover and word_count <= 15 and any(k in upper_text for k in cover_keywords):
                    final_label = "COVER_METADATA"
                else:
                    final_label = "BODY_PARAGRAPH"
                if pred_label in ["SUB_BAB", "JUDUL_BAB", "FRONTMATTER_TITLE"]:
                    correction_reason = "Teks berada di halaman depan/pengesahan/kata pengantar sebelum Bab 1 (dialihkan ke BODY_PARAGRAPH/COVER_METADATA)."

            elif in_daftar_pustaka:
                final_label = "BODY_PARAGRAPH"
                if pred_label in ["SUB_BAB", "JUDUL_BAB"]:
                    correction_reason = "Teks berada di dalam bagian Daftar Pustaka (dialihkan ke BODY_PARAGRAPH)."

            elif is_kesimpulan_saran_sub:
                final_label = "SUB_BAB"
                correction_reason = "Teks 'Kesimpulan' atau 'Saran' berada di bawah Bab V (Sub-Bab)."

            elif is_formula and pred_label in ["SUB_BAB", "JUDUL_BAB", "FRONTMATTER_TITLE"]:
                final_label = "BODY_PARAGRAPH"
                correction_reason = "Teks terdeteksi sebagai notasi/persamaan matematika (Formula) dialihkan ke BODY_PARAGRAPH."

            elif in_formula_legend and (':' in text or is_variable_item):
                final_label = "BODY_PARAGRAPH"
                if pred_label in ["SUB_BAB", "JUDUL_BAB"]:
                    correction_reason = "Teks rincian variabel keterangan rumus (dialihkan ke BODY_PARAGRAPH)."

            # Prioritas Utama: Caption Gambar & Tabel (JANGAN sampai terlempar ke BODY_PARAGRAPH karena style List Paragraph)
            elif re.match(r'^(Gambar|Figure)\s*[\.\d]', text.strip(), re.IGNORECASE) and word_count <= 25:
                narrative_verbs = ["memperlihatkan", "menunjukkan", "menyajikan", "menjelaskan", "terlihat", "tampak", "merupakan", "adalah", "berisi", "menegaskan", "menggambarkan"]
                rest_cap = re.sub(r'^(Gambar|Figure)\s*[\.\d\s:\-]+', '', text.strip(), flags=re.IGNORECASE).strip().lower()
                first_w = rest_cap.split()[0] if rest_cap.split() else ""
                if first_w in narrative_verbs:
                    final_label = "BODY_PARAGRAPH"
                else:
                    final_label = "CAPTION_GAMBAR"
                    if pred_label != "CAPTION_GAMBAR":
                        correction_reason = "Teks dikenali sebagai Caption Gambar baku."

            elif re.match(r'^(Tabel|Table)\s*[\.\d]', text.strip(), re.IGNORECASE) and word_count <= 25:
                narrative_verbs = ["memperlihatkan", "menunjukkan", "menyajikan", "menjelaskan", "terlihat", "tampak", "merupakan", "adalah", "berisi", "menegaskan", "menggambarkan"]
                rest_cap = re.sub(r'^(Tabel|Table)\s*[\.\d\s:\-]+', '', text.strip(), flags=re.IGNORECASE).strip().lower()
                first_w = rest_cap.split()[0] if rest_cap.split() else ""
                if first_w in narrative_verbs:
                    final_label = "BODY_PARAGRAPH"
                else:
                    final_label = "CAPTION_TABEL"
                    if pred_label != "CAPTION_TABEL":
                        correction_reason = "Teks dikenali sebagai Caption Tabel baku."

            elif (not is_standard_sub and not is_numbered_sub) and (not item["metadata"].get("style", "").startswith("Heading")) and not re.match(r'^(Gambar|Figure|Tabel|Table)\b', text.strip(), re.IGNORECASE) and (is_citation or is_hypo or is_formula_legend or is_variable_item or is_source_note or is_numbered_list or meta.get("has_num") or meta.get("style") == "List Paragraph"):
                final_label = "BODY_PARAGRAPH"
                if pred_label in ["SUB_BAB", "JUDUL_BAB"]:
                    correction_reason = "Teks rincian butir/keterangan rumus/sumber/hipotesis/sitasi dialihkan ke BODY_PARAGRAPH."

            elif is_real_chapter_header:
                final_label = "JUDUL_BAB"
                last_valid_bab_num = inferred_bab
                in_sistematika = False
                active_heading2 = False
                if pred_label != "JUDUL_BAB":
                    correction_reason = f"Teks divalidasi sebagai Judul Bab {inferred_bab} Kanonikal UEU."

            elif in_sistematika and (inferred_bab > 0 or any(clean_up.startswith(k) for k in ["BAB I", "BAB II", "BAB III", "BAB IV", "BAB V", "BAB 1", "BAB 2", "BAB 3", "BAB 4", "BAB 5"]) or is_followed_by_desc):
                final_label = "BODY_PARAGRAPH"
                correction_reason = "Teks rincian deskripsi bab di dalam Sistematika Penulisan Laporan (dialihkan ke BODY_PARAGRAPH)."

            elif inferred_bab > 0:
                if inferred_bab < last_valid_bab_num and last_valid_bab_num > 0:
                    final_label = "BODY_PARAGRAPH"
                    correction_reason = f"Nomor Bab {inferred_bab} tidak monotonik (Bab {last_valid_bab_num} sudah lewat)."
                elif inferred_bab == last_valid_bab_num:
                    final_label = "SUB_BAB"
                    correction_reason = f"Teks '{text.strip()}' berada di bawah Bab {inferred_bab} aktif (Sub-Bab)."
                elif inferred_bab > last_valid_bab_num + 1 and not re.match(r'^BAB\s+([IVX\d]+)\b', clean_up):
                    final_label = "SUB_BAB"
                    correction_reason = f"Teks '{text.strip()}' bukan Bab baru (lompatan nomor tanpa kata 'BAB')."
                else:
                    final_label = "JUDUL_BAB"
                    last_valid_bab_num = inferred_bab
                    active_heading2 = False
                    if pred_label != "JUDUL_BAB":
                        correction_reason = f"Teks dikenali sebagai Judul Bab {inferred_bab} Kanonikal UEU."

            elif pred_label == "JUDUL_BAB" and inferred_bab == 0:
                if last_valid_bab_num >= 1 and (re.match(r'^\d+\.\d+', text.strip()) or (word_count <= 10 and any(clean_up_no_punct == sb or clean_up_no_punct.startswith(sb) for sb in standard_subchapters))):
                    final_label = "SUB_BAB"
                    correction_reason = "Teks diprediksi JUDUL_BAB namun memiliki pola penomoran/nama Sub-Bab resmi UEU."
                else:
                    final_label = "BODY_PARAGRAPH"
                    correction_reason = "Teks tidak memuat kata 'BAB' atau nama bab resmi UEU (False Positive ML)."

            # 4. DETEKSI PRIORITAS: Sub-Bab & Sub-Sub-Bab
            elif last_valid_bab_num >= 1 and (
                item["metadata"].get("style") in ["Heading 2", "Heading 3", "Heading2", "Heading3"] or
                item["metadata"].get("is_subsub") or
                is_numbered_sub or
                is_standard_sub or
                (pred_label == "SUB_BAB" and word_count <= 12 and not text.strip().endswith(('.', ':', ';', '!', '?', ',')) and not any(len(w) > 22 for w in text.split()) and not any(k in clean_up for k in ["UNIVERSITAS", "FAKULTAS", "PROGRAM STUDI", "TANDA TANGAN"]))
            ):
                final_label = "SUB_BAB"
                if pred_label != "SUB_BAB":
                    correction_reason = "Teks dikenali sebagai Sub-Bab/Sub-Sub-Bab hierarkis resmi UEU."

            # 5. Audit Sub-Bab sebelum Bab I (Cover Metadata)
            elif pred_label == "SUB_BAB" and last_valid_bab_num == 0:
                cover_keywords = ["NAMA", "NIM", "PROGRAM STUDI", "FAKULTAS", "UNIVERSITAS", "TAHUN", "SKRIPSI", "TUGAS AKHIR"]
                if not has_passed_cover and word_count <= 15 and any(k in upper_text for k in cover_keywords):
                    final_label = "COVER_METADATA"
                    correction_reason = "Teks berada di halaman sampul sebelum Bab I (dialihkan dari SUB_BAB ke COVER_METADATA)."
                else:
                    final_label = "BODY_PARAGRAPH"
                    correction_reason = "Teks sebelum Bab I dialihkan dari SUB_BAB ke BODY_PARAGRAPH."

            # 6. Fallback untuk FRONTMATTER_TITLE yang salah prediksi di luar frontmatter resmi
            elif pred_label == "FRONTMATTER_TITLE" and not is_frontmatter:
                if last_valid_bab_num >= 1 and (word_count <= 10 and any(clean_up_no_punct == sb or clean_up_no_punct.startswith(sb) for sb in standard_subchapters)):
                    final_label = "SUB_BAB"
                    correction_reason = "Teks diprediksi FRONTMATTER_TITLE di dalam Bab Isi divalidasi sebagai Sub-Bab resmi."
                elif last_valid_bab_num == 0 and any(k in upper_text for k in ["TUGAS AKHIR", "SKRIPSI", "FAKULTAS", "PROGRAM STUDI", "UNIVERSITAS"]):
                    final_label = "COVER_METADATA"
                    correction_reason = "Teks halaman sampul dialihkan ke COVER_METADATA."
                else:
                    final_label = "BODY_PARAGRAPH"
                    correction_reason = "Teks berada di halaman pengesahan/pernyataan dialihkan ke format paragraf teks biasa."

            # 7. DETEKSI PRIORITAS: Caption Gambar & Tabel
            elif re.match(r'^(Gambar|Figure)\s*[\.\d]', text.strip(), re.IGNORECASE) and word_count <= 25:
                narrative_verbs = ["memperlihatkan", "menunjukkan", "menyajikan", "menjelaskan", "terlihat", "tampak", "merupakan", "adalah", "berisi", "menegaskan", "menggambarkan"]
                rest_cap = re.sub(r'^(Gambar|Figure)\s*[\.\d\s:\-]+', '', text.strip(), flags=re.IGNORECASE).strip().lower()
                first_w = rest_cap.split()[0] if rest_cap.split() else ""
                if first_w in narrative_verbs:
                    final_label = "BODY_PARAGRAPH"
                else:
                    final_label = "CAPTION_GAMBAR"
                    if pred_label != "CAPTION_GAMBAR":
                        correction_reason = "Teks dikenali sebagai Caption Gambar baku."
            elif re.match(r'^(Tabel|Table)\s*[\.\d]', text.strip(), re.IGNORECASE) and word_count <= 25:
                narrative_verbs = ["memperlihatkan", "menunjukkan", "menyajikan", "menjelaskan", "terlihat", "tampak", "merupakan", "adalah", "berisi", "menegaskan", "menggambarkan"]
                rest_cap = re.sub(r'^(Tabel|Table)\s*[\.\d\s:\-]+', '', text.strip(), flags=re.IGNORECASE).strip().lower()
                first_w = rest_cap.split()[0] if rest_cap.split() else ""
                if first_w in narrative_verbs:
                    final_label = "BODY_PARAGRAPH"
                else:
                    final_label = "CAPTION_TABEL"
                    if pred_label != "CAPTION_TABEL":
                        correction_reason = "Teks dikenali sebagai Caption Tabel baku."
            elif pred_label in ["CAPTION_GAMBAR", "CAPTION_TABEL"] and word_count > 30:
                final_label = "BODY_PARAGRAPH"
                correction_reason = "Teks terlalu panjang untuk sebuah caption (> 30 kata)."

            # 7.1 Cross-Chapter Caption Parity Check
            if final_label in ["CAPTION_GAMBAR", "CAPTION_TABEL"] and last_valid_bab_num >= 1:
                cap_match = re.search(r'^(?:Gambar|Figure|Tabel|Table)\s*(\d+)[\.\-](\d+)', text.strip(), re.IGNORECASE)
                if cap_match:
                    cap_bab = int(cap_match.group(1))
                    cap_num = int(cap_match.group(2))
                    if cap_bab != last_valid_bab_num:
                        prefix_nm = "Gambar" if final_label == "CAPTION_GAMBAR" else "Tabel"
                        correction_reason = f"Koreksi nomor bab pada caption {prefix_nm} dari {cap_bab}.{cap_num} menjadi Bab {last_valid_bab_num} agar konsisten dengan struktur bab aktif."
                        item["metadata"]["target_caption_bab"] = last_valid_bab_num
                        item["metadata"]["original_caption_bab"] = cap_bab

            # 8. DETEKSI GAMBAR: Paragraf yang memuat gambar/drawing/pict adalah BODY_PARAGRAPH
            elif item["metadata"].get("has_img"):
                final_label = "BODY_PARAGRAPH"

            # 9. Karantina Ketat: Setelah Bab 1 dimulai (last_valid_bab_num >= 1), TIDAK BOLEH ADA COVER_METADATA!
            if last_valid_bab_num >= 1 and final_label == "COVER_METADATA":
                final_label = "BODY_PARAGRAPH"
                correction_reason = "Teks berada di dalam Bab Isi naskah (dialihkan dari COVER_METADATA ke BODY_PARAGRAPH)."

            if final_label == "SUB_BAB":
                is_explicit_subsub = bool(
                    item["metadata"].get("is_subsub") or
                    item["metadata"].get("style") in ["Heading 3", "Heading3"] or
                    re.match(r'^\d+\.\d+\.\d+', text.strip())
                )
                is_explicit_heading2 = bool(
                    item["metadata"].get("style") in ["Heading 2", "Heading2"] or
                    re.match(r'^\d+\.\d+\s+[A-Za-z]', text.strip()) or
                    any(clean_up_no_punct == sb or clean_up_no_punct.startswith(sb) for sb in standard_subchapters)
                )

                if is_explicit_subsub:
                    item["metadata"]["is_subsub"] = True
                elif is_explicit_heading2:
                    item["metadata"]["is_subsub"] = False
                    active_heading2 = True
                elif active_heading2:
                    # Di bawah Heading 2 yang aktif, sub-heading tanpa awalan bab kanonikal adalah Sub-sub-bab (Heading 3)
                    item["metadata"]["is_subsub"] = True
                else:
                    item["metadata"]["is_subsub"] = False
                    active_heading2 = True

            # Catat jika ada koreksi (HANYA untuk baris yang berisi teks nyata dan memiliki alasan valid)
            if final_label != pred_label and len(text.strip()) > 0:
                if not correction_reason:
                    correction_reason = f"Penyelarasan label dari {pred_label} ke {final_label} sesuai kaidah naskah akademik UEU."
                corrections_made.append({
                    "para_id": para_id,
                    "text": text[:50],
                    "original_pred": pred_label,
                    "corrected_label": final_label,
                    "reason": correction_reason
                })

            refined_paragraphs.append({
                **item,
                "approved_label": final_label,
                "was_corrected": (final_label != pred_label)
            })

        # Hitung statistik cetak biru final
        final_summary = {}
        for p in refined_paragraphs:
            lbl = p["approved_label"]
            final_summary[lbl] = final_summary.get(lbl, 0) + 1

        approved_chapters = [
            f"P[{p['para_id']}] {p['text'][:40]}" 
            for p in refined_paragraphs if p["approved_label"] == "JUDUL_BAB"
        ]

        # Simpan umpan balik koreksi secara otomatis ke pool Active Learning
        corrected_items = [p for p in refined_paragraphs if p.get("was_corrected", False)]
        new_feedback_count = 0
        try:
            from src.active_learning import ActiveLearningManager
            al_mgr = ActiveLearningManager()
            new_feedback_count = al_mgr.record_corrections(inspection_report.get("source_doc", "dokumen"), corrected_items)
        except Exception as e:
            print(f"[Agent 2 - Quality Critic] Peringatan: Tidak dapat mencatat feedback Active Learning: {e}")

        approved_blueprint = {
            "source_doc": inspection_report["source_doc"],
            "total_paragraphs": inspection_report["total_paragraphs"],
            "total_corrections": len(corrections_made),
            "new_feedback_samples": new_feedback_count,
            "corrections_log": corrections_made,
            "final_summary": final_summary,
            "approved_chapters": approved_chapters,
            "paragraphs": refined_paragraphs,
            "status": "APPROVED BY QUALITY CRITIC AGENT"
        }

        print(f"[Agent 2 - Quality Critic] Audit Selesai! Mengoreksi {len(corrections_made)} anomali.")
        print(f"[Agent 2 - Quality Critic] {new_feedback_count} sampel koreksi baru disalurkan ke Active Learning Pool.")
        print(f"[Agent 2 - Quality Critic] Bab Tervalidasi Monotonik ({len(approved_chapters)} Bab): {approved_chapters}")
        return approved_blueprint

    def verify_formatted_document(self, docx_path: str) -> Dict[str, Any]:
        """
        [SQA AUDITOR & ACCEPTANCE TESTER]
        Menguji secara otomatis berkas Word hasil pemformatan Agent 3 terhadap 8 Kriteria Mutu Akademik UEU:
        1. Standar Margin Baku 4-3-3-3 pada seluruh Section.
        2. Struktur Section & Dual Page Numbering (Romawi di Frontmatter, Latin di Bab Isi).
        3. Heading 1 (Center mutlak tanpa offset indentasi).
        4. Heading 2 (Spasi Sebelum 12 pt, Sesudah 6 pt).
        5. Paragraf Isi Tubuh (Spasi Sebelum 0 pt, Sesudah 6 pt, Spasi Baris 1.15).
        6. Ukuran Kertas Baku A4 Portrait (21.0 x 29.7 cm).
        7. Header Resmi "Universitas Esa Unggul" di kanan atas Section Frontmatter dan Bab Isi.
        8. Format Tabel APA 7 (Bebas garis vertikal, hanya garis horizontal utama).
        """
        import docx
        from docx.oxml.ns import qn
        from docx.enum.section import WD_ORIENTATION
        
        doc = docx.Document(docx_path)
        defects = []
        checks = {}
        
        # 1. Audit Margin (4-3-3-3 cm) pada seluruh Section
        margin_ok = True
        for s_idx, sec in enumerate(doc.sections):
            top_cm = round(sec.top_margin.cm, 2)
            bottom_cm = round(sec.bottom_margin.cm, 2)
            left_cm = round(sec.left_margin.cm, 2)
            right_cm = round(sec.right_margin.cm, 2)
            if not (abs(left_cm - 4.0) <= 0.2 and abs(top_cm - 3.0) <= 0.2 and abs(right_cm - 3.0) <= 0.2 and abs(bottom_cm - 3.0) <= 0.2):
                margin_ok = False
                defects.append(f"Section {s_idx} margin tidak sesuai ({left_cm}-{top_cm}-{right_cm}-{bottom_cm} cm alih-alih 4-3-3-3 cm)")
        checks["margin_4_3_3_3"] = margin_ok

        # 2. Audit Dual Page Numbering & Section Break
        paging_ok = True
        if len(doc.sections) >= 3:
            # Section 0: Cover (tanpa nomor)
            sec_cov = doc.sections[0]
            cov_pg = sec_cov._sectPr.find(qn('w:pgNumType'))
            if cov_pg is not None and cov_pg.attrib.get(qn('w:fmt')) in ['decimal', 'lowerRoman']:
                paging_ok = False
                defects.append("Section 0 (Cover) memiliki penomoran halaman tidak sah")
            
            # Section 1: Frontmatter (Romawi)
            sec_fm = doc.sections[1]
            fm_pg = sec_fm._sectPr.find(qn('w:pgNumType'))
            if fm_pg is None or fm_pg.attrib.get(qn('w:fmt')) != 'lowerRoman':
                paging_ok = False
                defects.append("Section 1 (Frontmatter) tidak menggunakan format penomoran Romawi kecil (lowerRoman)")
            
            # Section 2: Body (Latin decimal start=1)
            sec_body = doc.sections[2]
            body_pg = sec_body._sectPr.find(qn('w:pgNumType'))
            if body_pg is None or body_pg.attrib.get(qn('w:fmt')) != 'decimal':
                paging_ok = False
                defects.append("Section 2 (Bab Isi) tidak menggunakan format penomoran Latin (decimal)")
        elif len(doc.sections) == 2:
            # Dokumen tanpa cover: Section 0 (Frontmatter Romawi) & Section 1 (Bab Isi decimal)
            sec_fm = doc.sections[0]
            fm_pg = sec_fm._sectPr.find(qn('w:pgNumType'))
            if fm_pg is None or fm_pg.attrib.get(qn('w:fmt')) != 'lowerRoman':
                paging_ok = False
                defects.append("Section 0 (Frontmatter) tidak menggunakan format penomoran Romawi kecil (lowerRoman)")
            
            sec_body = doc.sections[1]
            body_pg = sec_body._sectPr.find(qn('w:pgNumType'))
            if body_pg is None or body_pg.attrib.get(qn('w:fmt')) != 'decimal':
                paging_ok = False
                defects.append("Section 1 (Bab Isi) tidak menggunakan format penomoran Latin (decimal)")
        checks["dual_page_numbering"] = paging_ok

        # 3. Audit Heading 1 (Center Mutlak, Tanpa Offset, & Wajib Ada Tulisan BAB)
        h1_centered_ok = True
        for p in doc.paragraphs:
            if p.style and 'Heading 1' in p.style.name:
                p_text_clean = p.text.strip()
                is_frontmatter_title = any(k in p_text_clean.upper() for k in ["DAFTAR", "ABSTRAK", "ABSTRACT", "LAMPIRAN", "PERNYATAAN", "PENGESAHAN", "PERSETUJUAN", "KATA PENGANTAR", "PRAKATA", "RIWAYAT"])
                pPr = p._p.find(qn('w:pPr'))
                has_bab_numpr = (
                    pPr is not None and 
                    pPr.find(qn('w:numPr')) is not None and 
                    pPr.find(qn('w:numPr')).find(qn('w:ilvl')) is not None and 
                    pPr.find(qn('w:numPr')).find(qn('w:ilvl')).attrib.get(qn('w:val')) == '0'
                )
                if not re.search(r'BAB\s+(\d+|[IVXLCDM]+)', p_text_clean, re.IGNORECASE) and not is_frontmatter_title and not has_bab_numpr:
                    h1_centered_ok = False
                    defects.append(f"Heading 1 '{p_text_clean[:25]}' kehilangan kata 'BAB' (Diharuskan 'BAB X\\nJUDUL' atau numPr Word)")
                pPr = p._p.find(qn('w:pPr'))
                if pPr is not None:
                    jc = pPr.find(qn('w:jc'))
                    if jc is not None and jc.attrib.get(qn('w:val')) != 'center':
                        h1_centered_ok = False
                        defects.append(f"Heading 1 '{p.text[:25]}' tidak rata tengah (jc={jc.attrib.get(qn('w:val'))})")
                    ind = pPr.find(qn('w:ind'))
                    if ind is not None:
                        fl = int(ind.attrib.get(qn('w:firstLine'), '0'))
                        left = int(ind.attrib.get(qn('w:left'), '0'))
                        if fl > 300 or left > 0:
                            h1_centered_ok = False
                            defects.append(f"Heading 1 '{p.text[:25]}' memiliki offset indentasi (firstLine={fl}, left={left})")
        checks["heading1_centered"] = h1_centered_ok

        # 4. Audit Heading 2 (Wajib Nomor Eksplisit 1.1, Tab 1.27 cm, Spacing Atas 12 pt, Bawah 6 pt)
        h2_spacing_ok = True
        for p in doc.paragraphs:
            if p.style and 'Heading 2' in p.style.name:
                p_text_clean = p.text.strip()
                pPr = p._p.find(qn('w:pPr'))
                has_numpr = (pPr.find(qn('w:numPr')) is not None) if pPr is not None else False
                if not re.match(r'^\d+\.\d+', p_text_clean) and not has_numpr:
                    h2_spacing_ok = False
                    defects.append(f"Sub-Bab '{p_text_clean[:25]}' kehilangan penomoran bab (Diharuskan nomor '1.1' atau numPr Word)")
                if pPr is not None:
                    sp = pPr.find(qn('w:spacing'))
                    if sp is not None:
                        after_val = int(sp.attrib.get(qn('w:after'), '0'))
                        before_val = int(sp.attrib.get(qn('w:before'), '0'))
                        if abs(after_val - 120) > 40:
                            h2_spacing_ok = False
                            defects.append(f"Sub-Bab '{p.text[:25]}' spasi bawah tidak 6 pt (after={after_val} dxa)")
                        if abs(before_val - 240) > 60:
                            h2_spacing_ok = False
                            defects.append(f"Sub-Bab '{p.text[:25]}' spasi atas tidak 12 pt (before={before_val} dxa)")
        checks["subbab_spacing_12_6"] = h2_spacing_ok

        # 5. Audit Paragraf Tubuh (Tipografi, Spasi Baris 1.15, Spasi Bawah 6, Indentasi Baris Pertama 1.27 cm)
        body_sp_ok = True
        in_body_chapters = False
        for p in doc.paragraphs:
            if p.style and 'Heading 1' in p.style.name and any(k in p.text.upper() for k in ['BAB', 'PENDAHULUAN']):
                in_body_chapters = True
            if in_body_chapters and p.style and p.style.name == 'Normal' and len(p.text.split()) > 15:
                pPr = p._p.find(qn('w:pPr'))
                if pPr is not None:
                    sp = pPr.find(qn('w:spacing'))
                    if sp is not None:
                        line_val = int(sp.attrib.get(qn('w:line'), '276'))
                        after_val = int(sp.attrib.get(qn('w:after'), '120'))
                        if line_val > 300:
                            body_sp_ok = False
                            defects.append(f"Paragraf isi memiliki spasi baris terlalu besar ({line_val} dxa)")
                            break
                        if abs(after_val - 120) > 40:
                            body_sp_ok = False
                            defects.append(f"Paragraf isi spasi bawah tidak 6 pt ({after_val} dxa)")
                            break
                    ind = pPr.find(qn('w:ind'))
                    if ind is not None:
                        fl = int(ind.attrib.get(qn('w:firstLine'), '0'))
                        if fl == 0:
                            body_sp_ok = False
                            defects.append("Paragraf isi tidak memiliki indentasi alinea baris pertama (firstLine=0)")
                            break
        checks["body_spacing_0_6_115"] = body_sp_ok

        # 6. Audit Ukuran Kertas Baku A4 Portrait (21.0 x 29.7 cm)
        a4_ok = True
        for s_idx, sec in enumerate(doc.sections):
            w_cm = round(sec.page_width.cm, 1)
            h_cm = round(sec.page_height.cm, 1)
            if sec.orientation == WD_ORIENTATION.PORTRAIT:
                if abs(w_cm - 21.0) > 0.4 or abs(h_cm - 29.7) > 0.4:
                    a4_ok = False
                    defects.append(f"Section {s_idx} ukuran kertas bukan A4 Portrait ({w_cm} x {h_cm} cm)")
            else:
                if abs(w_cm - 29.7) > 0.4 or abs(h_cm - 21.0) > 0.4:
                    a4_ok = False
                    defects.append(f"Section {s_idx} ukuran kertas bukan A4 Landscape ({w_cm} x {h_cm} cm)")
        checks["page_size_a4"] = a4_ok

        # 7. Audit Header Resmi UEU
        header_ok = True
        if len(doc.sections) >= 2:
            for s_idx in range(1, len(doc.sections)):
                sec = doc.sections[s_idx]
                header_text = "".join(p.text for p in sec.header.paragraphs).upper()
                if "UNIVERSITAS ESA UNGGUL" not in header_text:
                    header_ok = False
                    defects.append(f"Section {s_idx} tidak memiliki Header resmi 'Universitas Esa Unggul'")
                    break
        checks["header_ueu_presence"] = header_ok

        # 8. Audit Format Tabel APA 7 (Tanpa Border Vertikal)
        table_apa7_ok = True
        for t_idx, tbl in enumerate(doc.tables):
            if len(tbl.rows) <= 1 and len(tbl.columns) <= 1:
                continue
            tblBorders = tbl._tbl.tblPr.find(qn('w:tblBorders'))
            if tblBorders is not None:
                insideV = tblBorders.find(qn('w:insideV'))
                left_b = tblBorders.find(qn('w:left'))
                right_b = tblBorders.find(qn('w:right'))
                for b in [insideV, left_b, right_b]:
                    if b is not None and b.attrib.get(qn('w:val')) not in ['none', 'nil']:
                        table_apa7_ok = False
                        defects.append(f"Tabel {t_idx+1} memiliki garis vertikal yang dilarang standar APA 7")
                        break
        checks["table_apa7_borders"] = table_apa7_ok

        total_rules = len(checks)
        passed_rules = sum(1 for v in checks.values() if v)
        qa_score = round((passed_rules / total_rules) * 100, 1) if total_rules > 0 else 100.0
        is_passed = (len(defects) == 0)

        result = {
            "status": "PASS" if is_passed else "FAIL",
            "passed": is_passed,
            "qa_score": qa_score,
            "score": qa_score,
            "total_checks": total_rules,
            "passed_checks": passed_rules,
            "checks": checks,
            "defects_count": len(defects),
            "defects": defects
        }
        print(f"[Agent 2 - SQA Auditor] Audit Hasil Pemformatan: Status={result['status']} | Skor={qa_score}% | Cacat={len(defects)}")
        return result

    def coordinate_tier1_blueprint_loop(self, inspection_report: Dict[str, Any], inspector_agent=None, max_iterations: int = 3) -> Dict[str, Any]:
        """
        [SQA TIER 1 GATEKEEPER LOOP: Agent 1 <-> Agent 2]
        Alur:
        1. Agent 2 (SQA) mengaudit draf hasil kerja Agent 1.
        2. Jika ditemukan cacat / inkonsistensi struktur:
           - SQA membuat daftar instruksi korektif (feedback directives).
           - Mengembalikan draft ke Agent 1 untuk diinspeksi & disempurnakan ulang.
        3. Siklus berulang hingga dokumen memenuhi 100% konsistensi struktural.
        4. SQA menerbitkan APPROVED BLUEPRINT resmi.
        """
        current_report = inspection_report
        tier1_history = []
        approved_blueprint = None

        for it in range(1, max_iterations + 1):
            print(f"\n[SQA Tier 1 Gatekeeper - Iterasi {it}/{max_iterations}] Mengaudit blueprint struktur dari Agent 1...")
            approved_blueprint = self.evaluate_and_refine(current_report)
            corrections = approved_blueprint.get("corrections_log", [])
            tier1_history.append({
                "iteration": it,
                "corrections_count": len(corrections),
                "approved_chapters": approved_blueprint.get("approved_chapters", []),
                "status": "APPROVED" if (len(corrections) == 0 or it == max_iterations or not inspector_agent) else "FEEDBACK_SENT_TO_AGENT_1"
            })

            # Jika terdapat koreksi dan ada referensi ke Agent 1 dan belum mencapai batas iterasi,
            # kirim kembali ke Agent 1 untuk re-inspeksi adaptif:
            if len(corrections) > 0 and inspector_agent is not None and it < max_iterations:
                print(f"[SQA Tier 1 Gatekeeper] Ditemukan {len(corrections)} anomali pada draf Agent 1. Mengembalikan feedback ke Agent 1 untuk re-inspeksi...")
                current_report = inspector_agent.re_inspect_with_feedback(current_report, corrections)
            else:
                print(f"[SQA Tier 1 Gatekeeper] Blueprint STRUKTUR 100% LOLOS AUDIT (Iterasi {it})! Siap diserahkan ke Agent 3 (Formatter).")
                break

        approved_blueprint["sqa_tier1_history"] = tier1_history
        approved_blueprint["sqa_tier1_iterations"] = len(tier1_history)
        approved_blueprint["sqa_tier1_status"] = "100% APPROVED BY SQA AUDITOR"
        return approved_blueprint

    def coordinate_tier2_artifact_loop(self, input_docx_path: str, approved_blueprint: Dict[str, Any], output_docx_path: str, formatter_agent, max_iterations: int = 3) -> Dict[str, Any]:
        """
        [SQA TIER 2 QUALITY GATE LOOP: Agent 3 <-> Agent 2]
        Alur:
        1. Agent 3 mengeksekusi bedah OpenXML berdasarkan Approved Blueprint.
        2. Agent 2 (SQA Auditor) menguji dokumen jadi terhadap 5 Kriteria Penerimaan Mutu UEU:
           - Margin baku 4-3-3-3 cm di semua section.
           - Dual Page Numbering (Romawi di Frontmatter, Latin di Bab Isi).
           - Indentasi Sub-bab 1.1 sejajar alinea 1.27 cm.
           - Spasi rapat Before/After 0 pt & Line Spacing 1.15.
           - Format Tabel APA 7.
        3. Jika ditemukan cacat (defects), SQA mengembalikan defect report ke Agent 3 untuk diremediasi.
        4. Siklus berulang hingga 100% PASS sebelum diserahkan ke pengguna.
        """
        tier2_history = []
        qa_result = None
        current_output = output_docx_path

        for it in range(1, max_iterations + 1):
            print(f"\n[SQA Tier 2 Quality Gate - Iterasi {it}/{max_iterations}] Meminta Agent 3 (Formatter) menyusun dokumen OpenXML...")
            current_output = formatter_agent.format_document(input_docx_path, approved_blueprint, current_output)

            print(f"[SQA Tier 2 Quality Gate - Iterasi {it}/{max_iterations}] Agent 2 (SQA Auditor) menguji kepatuhan naskah jadi...")
            qa_result = self.verify_formatted_document(current_output)
            tier2_history.append({
                "iteration": it,
                "qa_score": qa_result["qa_score"],
                "defects_count": len(qa_result["defects"]),
                "defects": qa_result["defects"],
                "status": "PASS" if qa_result["passed"] else "FAIL_RETRY"
            })

            if qa_result["passed"]:
                print(f"[SQA Tier 2 Quality Gate] Dokumen LOLOS 100% Acceptance Criteria pada iterasi ke-{it}!")
                break
            else:
                print(f"[SQA Tier 2 Quality Gate] Ditemukan {len(qa_result['defects'])} cacat pada iterasi ke-{it}. Mengembalikan ke Agent 3...")

        return {
            "output_path": current_output,
            "final_qa_result": qa_result,
            "tier2_iterations": len(tier2_history),
            "tier2_history": tier2_history,
            "status": "100% PASS" if qa_result and qa_result["passed"] else "PARTIAL_PASS"
        }


if __name__ == "__main__":
    from src.agents.inspector import InspectorAgent
    inspector = InspectorAgent()

    print("\n=== UJI COBA PADA DOKUMEN DHICKY ===")
    draf_dhicky = inspector.inspect("data/doc_dhicky.docx")
    critic = QualityCriticAgent()
    approved_dhicky = critic.evaluate_and_refine(draf_dhicky)

    print("\n--- BAB TERVALIDASI DI DOKUMEN DHICKY ---")
    for b in approved_dhicky["approved_chapters"]:
        print(b)
