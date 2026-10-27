"""
AGENT 2: QUALITY CRITIC & COORDINATOR (Validator & Feedback Loop).

Tugas:
1. Mengaudit Draft Blueprint Agent 1: urutan bab monotonik (I -> II -> ... -> V), inferensi judul bab
   kanonikal tanpa kata 'BAB', karantina halaman depan, isolasi Sistematika Penulisan, filter rumus,
   butir daftar, sitasi, dan validasi nomor caption.
2. Menerbitkan Approved Blueprint untuk Agent 3 dan menyalurkan koreksi ke pool Active Learning.
3. Menguji dokumen jadi terhadap 8 kriteria mutu UEU (SQA Tier 2).
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import docx
from docx.enum.section import WD_ORIENTATION
from docx.oxml.ns import qn

from src.academic_rules import (
    BAB_LITERAL_RE,
    BIBLIOGRAPHY_TITLES,
    CHAPTER_TITLES_BY_NUMBER,
    FRONTMATTER_TITLES,
    HEADING3_STYLES,
    LABEL_BODY,
    LABEL_CHAPTER,
    LABEL_COVER,
    LABEL_FIGURE_CAPTION,
    LABEL_FRONTMATTER,
    LABEL_SUBCHAPTER,
    LABEL_TABLE_CAPTION,
    MAX_CAPTION_WORDS,
    STRUCTURAL_LABELS,
    SUBCHAPTER_NUMBER_RE,
    SUBCHAPTER_TITLES,
    SUBHEADING_STYLES,
    SUBSUB_NUMBER_RE,
    caption_kind,
    is_narrative_caption,
    rule_prior_label,
)

ROMAWI_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
}

COVER_KEYWORDS = ("NAMA", "NIM", "PROGRAM STUDI", "FAKULTAS", "UNIVERSITAS", "TAHUN", "SKRIPSI", "TUGAS AKHIR")
SISTEMATIKA_CHAPTER_PREFIXES = ("BAB I", "BAB II", "BAB III", "BAB IV", "BAB V", "BAB 1", "BAB 2", "BAB 3", "BAB 4", "BAB 5")
CHAPTER_DESCRIPTION_OPENERS = ("bab ini", "dalam bab ini", "pada bab ini")
NARRATIVE_CHAPTER_MARKERS = (":", "BERISI", "MEMBAHAS", "MENJELASKAN")
INSTITUTION_MARKERS = ("UNIVERSITAS", "FAKULTAS", "PROGRAM STUDI", "TANDA TANGAN")
NOTE_PREFIXES = ("CATATAN", "NOTE", "SUMBER", "SOURCE", "KETERANGAN", "DIMANA")
FORMULA_OPERATORS = (" = ", " / ", " * ", " + ", " \\approx ", " \\pm ", " \\sum ")
METRIC_FORMULA_KEYS = ("Accuracy =", "Precision =", "Recall =", "F1-Score =", "F1 =", "MAE =", "MSE =", "RMSE =", "Loss =")
SENTENCE_ENDINGS = (".", ":", ";", "!", "?", ",")
TITLE_CASE_SMALL_WORDS = {"dan", "atau", "yang", "di", "ke", "dari", "pada", "untuk", "dengan", "terhadap", "dalam", "of", "the", "and"}

REVIEW_QUEUE_SIZE = 20  # jumlah maksimum kueri Active Learning per dokumen
SISTEMATIKA_WINDOW = 15
FORMULA_LEGEND_WINDOW = 15
MAX_CHAPTER_WORDS = 6
MAX_SUBCHAPTER_WORDS = 12
LAST_CHAPTER = 5

HYPOTHESIS_RE = re.compile(r"^(HA?\d*|H0|H\d+)\s*[:\.]", re.IGNORECASE)
FORMULA_LEGEND_RE = re.compile(r"^(Keterangan|Dimana|Di mana|Notasi)\s*[:=]?", re.IGNORECASE)
EQUATION_NUMBER_RE = re.compile(r"\(\d+\.\d+\)\s*$")
VARIABLE_ITEM_RE = re.compile(r"^[a-zA-Zα-ωΑ-Ω0-9_\u2080-\u2089,\s\t]{1,20}\s*[:=]\s*")
SOURCE_NOTE_RE = re.compile(r"^(Sumber|Source|Catatan|Note)\s*[:=]", re.IGNORECASE)
NUMBERED_LIST_RE = re.compile(r"^(\d+|[a-zA-Z])[\.\)]\s*")
# Judul poin bernomor ('1. Kontribusi Teori') yang diikuti paragraf penjelasan -> sub-sub-bab
POINT_HEADING_RE = re.compile(r"^\d{1,2}\.\s+(\S.*)$")
MAX_POINT_HEADING_WORDS = 8
MIN_EXPLANATION_WORDS = 8
CITATION_RES = (re.compile(r"^\([^\)]+,\s*\d{4}[a-z]?\)$"), re.compile(r"^[A-Z][a-zA-Z\s\.,\-]+\s*\(\d{4}[a-z]?\)\."))
CAPTION_WORD_RE = re.compile(r"^(Gambar|Figure|Tabel|Table)\b", re.IGNORECASE)
CAPTION_NUMBER_RE = re.compile(r"^(?:Gambar|Figure|Tabel|Table)\s*(\d+)[\.\-](\d+)", re.IGNORECASE)
H1_BAB_TEXT_RE = re.compile(r"BAB\s+(\d+|[IVXLCDM]+)", re.IGNORECASE)
FRONTMATTER_H1_MARKERS = ("DAFTAR", "ABSTRAK", "ABSTRACT", "LAMPIRAN", "PERNYATAAN", "PENGESAHAN", "PERSETUJUAN", "KATA PENGANTAR", "PRAKATA", "RIWAYAT")


def infer_bab_number(text: str) -> int:
    """Nomor bab dari 'BAB II'/'BAB 2' atau nama bab kanonikal ('LANDASAN TEORI' -> 2); 0 jika bukan bab."""
    clean = text.strip().upper().rstrip(".:;")
    if SUBCHAPTER_NUMBER_RE.match(clean):
        return 0
    literal = BAB_LITERAL_RE.match(clean)
    if literal:
        return ROMAWI_MAP.get(literal.group(1).upper(), 0)

    name = re.sub(r"^\d+(\.\d+)*\s*", "", clean)
    if len(name.split()) <= 5:  # cegah sub-bab panjang seperti 'Metode Pengembangan ...'
        for bab_num, names in CHAPTER_TITLES_BY_NUMBER.items():
            if name in names:
                return bab_num
    return 0


@dataclass
class _Signals:
    """Sinyal stateless sebuah paragraf yang dipakai rantai keputusan audit."""

    text: str
    stripped: str
    upper: str
    upper_np: str  # tanpa tanda baca penutup .:;
    word_count: int
    style: str
    is_frontmatter: bool
    is_hypothesis: bool
    is_formula_legend: bool
    is_formula: bool
    is_source_note: bool
    is_numbered_list: bool
    is_citation: bool
    is_numbered_sub: bool
    is_standard_sub: bool
    followed_by_chapter_description: bool


def _is_frontmatter_title(upper: str, upper_np: str, word_count: int) -> bool:
    if word_count > 10 or upper.startswith(("BAB ", "BAB I", "BAB 1")):
        return False
    return any(upper_np == fm or upper_np.startswith((fm + " ", fm + ":")) for fm in FRONTMATTER_TITLES)


def _is_formula(text: str, meta: Dict[str, Any]) -> bool:
    if meta.get("has_formula") or meta.get("has_math") or EQUATION_NUMBER_RE.search(text.strip()):
        return True
    has_operator = any(op in text for op in FORMULA_OPERATORS)
    return has_operator and bool(re.search(r"\(\d+(\.\d+)?\)", text) or any(k in text for k in METRIC_FORMULA_KEYS))


def _extract_signals(item: Dict[str, Any], next_item: Optional[Dict[str, Any]]) -> _Signals:
    text = item["text"]
    stripped = text.strip()
    upper = text.upper().strip()
    upper_np = upper.rstrip(".:;")
    word_count = len(upper.split())
    meta = item["metadata"]
    style = meta.get("style", "")
    next_text = next_item["text"].strip().lower() if next_item else ""
    return _Signals(
        text=text,
        stripped=stripped,
        upper=upper,
        upper_np=upper_np,
        word_count=word_count,
        style=style,
        is_frontmatter=_is_frontmatter_title(upper, upper_np, word_count),
        is_hypothesis=bool(HYPOTHESIS_RE.match(stripped)),
        is_formula_legend=bool(FORMULA_LEGEND_RE.match(stripped)),
        is_formula=_is_formula(text, meta),
        is_source_note=bool(SOURCE_NOTE_RE.match(stripped)),
        is_numbered_list=bool(NUMBERED_LIST_RE.match(stripped)) and not SUBCHAPTER_NUMBER_RE.match(stripped) and not style.startswith("Heading"),
        is_citation=any(regex.match(stripped) for regex in CITATION_RES),
        is_numbered_sub=bool(SUBCHAPTER_NUMBER_RE.match(stripped)),
        is_standard_sub=word_count <= 10 and upper_np.startswith(SUBCHAPTER_TITLES),
        followed_by_chapter_description=next_text.startswith(CHAPTER_DESCRIPTION_OPENERS),
    )


def _looks_like_variable_item(s: _Signals) -> bool:
    """Pola butir variabel keterangan rumus, mis. 'X = ...' (bukan hipotesis/catatan)."""
    return bool(VARIABLE_ITEM_RE.search(s.stripped)) and not s.is_hypothesis and not s.upper.startswith(NOTE_PREFIXES)


class _StructureAuditor:
    """Mesin status audit struktur naskah (dijalankan sekali per blueprint)."""

    def __init__(self):
        self.last_bab = 0
        self.has_passed_cover = False
        self.in_sistematika = False
        self.sistematika_count = 0
        self.active_heading2 = False
        self.in_bibliography = False
        self.in_formula_legend = False
        self.formula_legend_count = 0
        self.awaiting_chapter_title = False

    def audit(self, item: Dict[str, Any], next_item: Optional[Dict[str, Any]], pred: str,
              next_content: Optional[Dict[str, Any]] = None) -> Tuple[str, Optional[str]]:
        """Label akhir & alasan untuk satu paragraf; `pred` = label masukan (rule prior atau prediksi ML),
        `next_content` = paragraf berteks berikutnya (melewati paragraf kosong)."""
        s = _extract_signals(item, next_item)
        meta = item["metadata"]
        final = pred

        if "SISTEMATIKA PENULISAN" in s.upper and s.word_count <= 8:
            self.in_sistematika, self.sistematika_count = True, 0
            final = LABEL_SUBCHAPTER
        elif self.in_sistematika:
            self.sistematika_count += 1
            if self.sistematika_count > SISTEMATIKA_WINDOW:
                self.in_sistematika = False

        if s.upper_np in BIBLIOGRAPHY_TITLES:
            self.in_bibliography = True

        self._track_formula_legend(s)
        if s.is_formula:
            meta["is_formula"] = True
        is_variable_item = self.in_formula_legend and _looks_like_variable_item(s)

        inferred_bab = infer_bab_number(s.text) if (s.word_count <= MAX_SUBCHAPTER_WORDS and not s.is_frontmatter) else 0
        is_real_chapter = self._is_real_chapter(s, inferred_bab)

        is_title_line = self._is_chapter_title_line(s, inferred_bab)
        meta["chapter_title_continuation"] = is_title_line
        is_point_heading = not is_title_line and self._is_point_heading(s, item, next_content)
        if is_title_line:
            decision = (LABEL_CHAPTER, None if pred == LABEL_CHAPTER else "Teks adalah judul Bab yang ditulis di baris terpisah setelah 'BAB X'.")
        elif is_point_heading:
            meta["is_subsub"] = True
            decision = (LABEL_SUBCHAPTER, "Judul poin bernomor yang diikuti paragraf penjelasan dijadikan Sub-Sub-Bab (mis. 1.4.1).")
        else:
            decision = self._decide(s, item, pred, inferred_bab, is_real_chapter, is_variable_item)
        meta["is_bibliography"] = self.in_bibliography and decision is not None and decision[0] == LABEL_BODY
        if decision is not None:
            final, reason = decision
        else:
            reason = None

        final, reason = self._post_checks(s, meta, final, reason)
        if final == LABEL_SUBCHAPTER:
            self._assign_heading_level(s, meta)
        return final, reason

    def _track_formula_legend(self, s: _Signals) -> None:
        if s.is_formula_legend:
            self.in_formula_legend, self.formula_legend_count = True, 0
        elif self.in_formula_legend:
            self.formula_legend_count += 1
            if self.formula_legend_count > FORMULA_LEGEND_WINDOW or s.word_count > 25 or (":" not in s.text and not _looks_like_variable_item(s)):
                self.in_formula_legend = False

    def _is_real_chapter(self, s: _Signals, inferred_bab: int) -> bool:
        if inferred_bab <= 0 or s.word_count > MAX_CHAPTER_WORDS or any(k in s.upper for k in NARRATIVE_CHAPTER_MARKERS):
            return False
        if self.in_sistematika and s.followed_by_chapter_description:
            return False
        if (self.last_bab == 0 and inferred_bab == 1) or inferred_bab == self.last_bab + 1:
            self.in_sistematika = self.in_bibliography = self.in_formula_legend = False
            return True
        return False

    def _start_chapter(self, bab_num: int, s: _Signals) -> None:
        self.last_bab = bab_num
        self.active_heading2 = False
        literal = BAB_LITERAL_RE.match(s.upper_np)
        self.awaiting_chapter_title = bool(literal) and not s.upper_np[literal.end():].strip(" :.-")

    def _is_point_heading(self, s: _Signals, item: Dict[str, Any], next_content: Optional[Dict[str, Any]]) -> bool:
        """'1. Kontribusi Teori' (pendek, tebal/berformat judul, tanpa tanda baca kalimat) di dalam sub-bab
        yang diikuti paragraf penjelasan, bukan butir list lain (rumusan masalah/tujuan tetap list)."""
        if (self.last_bab < 1 or not self.active_heading2 or self.in_bibliography
                or self.in_sistematika or self.in_formula_legend or next_content is None):
            return False
        match = POINT_HEADING_RE.match(s.stripped)
        if match is None:
            return False
        title = match.group(1).strip()
        words = title.split()
        if len(words) > MAX_POINT_HEADING_WORDS or title.endswith(SENTENCE_ENDINGS):
            return False
        is_title_case = all(w[0].isupper() for w in words if w.lower() not in TITLE_CASE_SMALL_WORDS and w[0].isalpha())
        if not (item["raw_features"].get("is_bold") or is_title_case):
            return False
        next_text = next_content["text"].strip()
        return not NUMBERED_LIST_RE.match(next_text) and len(next_text.split()) >= MIN_EXPLANATION_WORDS

    def _is_chapter_title_line(self, s: _Signals, inferred_bab: int) -> bool:
        """Baris judul tepat setelah 'BAB X' tanpa judul, mis. 'BAB I' lalu 'PENDAHULUAN'."""
        if not self.awaiting_chapter_title or not s.stripped:
            return False
        self.awaiting_chapter_title = False
        if s.is_numbered_sub or s.is_frontmatter or BAB_LITERAL_RE.match(s.upper) or s.word_count > MAX_SUBCHAPTER_WORDS:
            return False
        return inferred_bab == self.last_bab or (s.stripped.isupper() and not s.stripped.endswith(SENTENCE_ENDINGS))

    def _cover_or_body(self, s: _Signals) -> str:
        if not self.has_passed_cover and s.word_count <= 15 and any(k in s.upper for k in COVER_KEYWORDS):
            return LABEL_COVER
        return LABEL_BODY

    @staticmethod
    def _caption_decision(s: _Signals, pred: str) -> Optional[Tuple[str, Optional[str]]]:
        kind = caption_kind(s.stripped)
        if kind is None or s.word_count > MAX_CAPTION_WORDS:
            return None
        if is_narrative_caption(s.stripped, kind):
            return LABEL_BODY, None
        reason = None
        if pred != kind:
            noun = "Gambar" if kind == LABEL_FIGURE_CAPTION else "Tabel"
            reason = f"Teks dikenali sebagai Caption {noun} baku."
        return kind, reason

    def _decide(self, s: _Signals, item, pred: str, inferred_bab: int, is_real_chapter: bool, is_variable_item: bool) -> Optional[Tuple[str, Optional[str]]]:
        """Rantai keputusan berprioritas; None berarti label saat ini dipertahankan."""
        meta = item["metadata"]
        if s.is_frontmatter:
            self.has_passed_cover = True
            self.in_bibliography = s.upper_np in BIBLIOGRAPHY_TITLES  # mis. LAMPIRAN mengakhiri daftar pustaka
            return LABEL_FRONTMATTER, (None if pred == LABEL_FRONTMATTER else "Teks adalah judul halaman awal resmi UEU (Frontmatter Title).")

        if self.last_bab == 0 and not is_real_chapter:
            reason = None
            if pred in STRUCTURAL_LABELS:
                reason = "Teks berada di halaman depan/pengesahan/kata pengantar sebelum Bab 1 (dialihkan ke BODY_PARAGRAPH/COVER_METADATA)."
            return self._cover_or_body(s), reason

        if self.in_bibliography:
            reason = "Teks berada di dalam bagian Daftar Pustaka (dialihkan ke BODY_PARAGRAPH)." if pred in (LABEL_SUBCHAPTER, LABEL_CHAPTER) else None
            return LABEL_BODY, reason

        if self.last_bab == LAST_CHAPTER and s.upper_np in ("KESIMPULAN", "SARAN"):
            return LABEL_SUBCHAPTER, "Teks 'Kesimpulan' atau 'Saran' berada di bawah Bab V (Sub-Bab)."

        if s.is_formula and pred in STRUCTURAL_LABELS:
            return LABEL_BODY, "Teks terdeteksi sebagai notasi/persamaan matematika (Formula) dialihkan ke BODY_PARAGRAPH."

        if self.in_formula_legend and (":" in s.text or is_variable_item):
            reason = "Teks rincian variabel keterangan rumus (dialihkan ke BODY_PARAGRAPH)." if pred in (LABEL_SUBCHAPTER, LABEL_CHAPTER) else None
            return LABEL_BODY, reason

        caption = self._caption_decision(s, pred)
        if caption is not None:
            return caption

        is_detail_item = (
            s.is_citation or s.is_hypothesis or s.is_formula_legend or is_variable_item or s.is_source_note
            or s.is_numbered_list or meta.get("has_num") or s.style == "List Paragraph"
        )
        if (not s.is_standard_sub and not s.is_numbered_sub and not s.style.startswith("Heading")
                and not CAPTION_WORD_RE.match(s.stripped) and is_detail_item):
            reason = "Teks rincian butir/keterangan rumus/sumber/hipotesis/sitasi dialihkan ke BODY_PARAGRAPH." if pred in (LABEL_SUBCHAPTER, LABEL_CHAPTER) else None
            return LABEL_BODY, reason

        if is_real_chapter:
            self._start_chapter(inferred_bab, s)
            self.in_sistematika = False
            return LABEL_CHAPTER, (None if pred == LABEL_CHAPTER else f"Teks divalidasi sebagai Judul Bab {inferred_bab} Kanonikal UEU.")

        if self.in_sistematika and (inferred_bab > 0 or s.upper.startswith(SISTEMATIKA_CHAPTER_PREFIXES) or s.followed_by_chapter_description):
            return LABEL_BODY, "Teks rincian deskripsi bab di dalam Sistematika Penulisan Laporan (dialihkan ke BODY_PARAGRAPH)."

        if inferred_bab > 0:
            return self._non_sequential_chapter(s, pred, inferred_bab)

        # Mulai titik ini last_bab >= 1 (seluruh kasus last_bab == 0 sudah ditangani di atas)
        if pred == LABEL_CHAPTER:
            if s.is_numbered_sub or s.is_standard_sub:
                return LABEL_SUBCHAPTER, "Teks diprediksi JUDUL_BAB namun memiliki pola penomoran/nama Sub-Bab resmi UEU."
            return LABEL_BODY, "Teks tidak memuat kata 'BAB' atau nama bab resmi UEU (False Positive ML)."

        if self._looks_like_subchapter(s, meta, pred):
            return LABEL_SUBCHAPTER, (None if pred == LABEL_SUBCHAPTER else "Teks dikenali sebagai Sub-Bab/Sub-Sub-Bab hierarkis resmi UEU.")

        if pred == LABEL_FRONTMATTER:
            if s.is_standard_sub:
                return LABEL_SUBCHAPTER, "Teks diprediksi FRONTMATTER_TITLE di dalam Bab Isi divalidasi sebagai Sub-Bab resmi."
            return LABEL_BODY, "Teks berada di halaman pengesahan/pernyataan dialihkan ke format paragraf teks biasa."

        if pred in (LABEL_FIGURE_CAPTION, LABEL_TABLE_CAPTION) and s.word_count > 30:
            return LABEL_BODY, "Teks terlalu panjang untuk sebuah caption (> 30 kata)."
        return None

    def _non_sequential_chapter(self, s: _Signals, pred: str, inferred_bab: int) -> Tuple[str, str]:
        if inferred_bab < self.last_bab:
            return LABEL_BODY, f"Nomor Bab {inferred_bab} tidak monotonik (Bab {self.last_bab} sudah lewat)."
        if inferred_bab == self.last_bab:
            return LABEL_SUBCHAPTER, f"Teks '{s.stripped}' berada di bawah Bab {inferred_bab} aktif (Sub-Bab)."
        if inferred_bab > self.last_bab + 1 and not BAB_LITERAL_RE.match(s.upper):
            return LABEL_SUBCHAPTER, f"Teks '{s.stripped}' bukan Bab baru (lompatan nomor tanpa kata 'BAB')."
        self._start_chapter(inferred_bab, s)
        return LABEL_CHAPTER, (None if pred == LABEL_CHAPTER else f"Teks dikenali sebagai Judul Bab {inferred_bab} Kanonikal UEU.")

    @staticmethod
    def _looks_like_subchapter(s: _Signals, meta: Dict[str, Any], pred: str) -> bool:
        if s.style in SUBHEADING_STYLES or meta.get("is_subsub") or s.is_numbered_sub or s.is_standard_sub:
            return True
        return (
            pred == LABEL_SUBCHAPTER
            and s.word_count <= MAX_SUBCHAPTER_WORDS
            and not s.stripped.endswith(SENTENCE_ENDINGS)
            and not any(len(w) > 22 for w in s.text.split())
            and not any(k in s.upper for k in INSTITUTION_MARKERS)
        )

    def _post_checks(self, s: _Signals, meta: Dict[str, Any], final: str, reason: Optional[str]) -> Tuple[str, Optional[str]]:
        if final in (LABEL_FIGURE_CAPTION, LABEL_TABLE_CAPTION) and self.last_bab >= 1:
            match = CAPTION_NUMBER_RE.search(s.stripped)
            if match and int(match.group(1)) != self.last_bab:
                cap_bab, cap_num = int(match.group(1)), int(match.group(2))
                noun = "Gambar" if final == LABEL_FIGURE_CAPTION else "Tabel"
                reason = f"Koreksi nomor bab pada caption {noun} dari {cap_bab}.{cap_num} menjadi Bab {self.last_bab} agar konsisten dengan struktur bab aktif."
                meta["target_caption_bab"] = self.last_bab
                meta["original_caption_bab"] = cap_bab
        elif meta.get("has_img"):
            final = LABEL_BODY

        if self.last_bab >= 1 and final == LABEL_COVER:
            final = LABEL_BODY
            reason = "Teks berada di dalam Bab Isi naskah (dialihkan dari COVER_METADATA ke BODY_PARAGRAPH)."
        return final, reason

    def _assign_heading_level(self, s: _Signals, meta: Dict[str, Any]) -> None:
        """Heading 2 vs Heading 3: sub-heading tanpa penanda eksplisit di bawah Heading 2 aktif menjadi Heading 3."""
        is_explicit_subsub = bool(meta.get("is_subsub") or meta.get("style") in HEADING3_STYLES or SUBSUB_NUMBER_RE.match(s.stripped))
        is_explicit_heading2 = bool(
            meta.get("style") in ("Heading 2", "Heading2")
            or re.match(r"^\d+\.\d+\s+[A-Za-z]", s.stripped)
            or s.upper_np.startswith(SUBCHAPTER_TITLES)
        )
        if is_explicit_subsub:
            meta["is_subsub"] = True
        elif is_explicit_heading2 or not self.active_heading2:
            meta["is_subsub"] = False
            self.active_heading2 = True
        else:
            meta["is_subsub"] = True


class QualityCriticAgent:
    """Agent 2: Quality Critic & Coordinator Agent."""

    def __init__(self, active_learning=None):
        """`active_learning`: ActiveLearningManager penampung koreksi; default dibuat saat pertama dipakai."""
        self._active_learning = active_learning
        print("[Agent 2 - Quality Critic] Diinisialisasi dengan Aturan Integritas Akademik Cerdas UEU.")

    # ------------------------------------------------------------------
    # SQA Tier 1: audit blueprint
    # ------------------------------------------------------------------
    def evaluate_and_refine(self, inspection_report: Dict[str, Any]) -> Dict[str, Any]:
        """Mengaudit prediksi Agent 1, memperbaiki inkonsistensi, dan menerbitkan Approved Blueprint."""
        print("\n[Agent 2 - Quality Critic] Mengaudit draf blueprint dari Agent 1...")
        paragraphs = inspection_report["paragraphs"]
        auditor = _StructureAuditor()
        refined, corrections, review_candidates = [], [], []

        for idx, item in enumerate(paragraphs):
            next_item = paragraphs[idx + 1] if idx + 1 < len(paragraphs) else None
            next_content = next((p for p in paragraphs[idx + 1:] if p["text"].strip()), None)
            ml_pred = item["predicted_label"]
            # Tahap 1: rule prior per paragraf; Tahap 2: rantai audit konteks dokumen
            prior = rule_prior_label(item["raw_features"])
            final, reason = auditor.audit(item, next_item, prior[0] if prior else ml_pred, next_content)
            if reason is None and prior and prior[0] == final:
                reason = f"Aturan baku UEU: {prior[1]}"
            if final != ml_pred and item["text"].strip():
                corrections.append({
                    "para_id": item["para_id"],
                    "text": item["text"][:50],
                    "original_pred": ml_pred,
                    "corrected_label": final,
                    "reason": reason or f"Penyelarasan label dari {ml_pred} ke {final} sesuai kaidah naskah akademik UEU.",
                })
            refined.append({**item, "approved_label": final, "was_corrected": final != ml_pred})
            if item.get("is_ambiguous") and prior is None and reason is None and final == ml_pred and item["text"].strip():
                review_candidates.append(item)

        final_summary: Dict[str, int] = {}
        for p in refined:
            final_summary[p["approved_label"]] = final_summary.get(p["approved_label"], 0) + 1
        approved_chapters = [
            f"P[{p['para_id']}] {p['text'][:40]}" for p in refined
            if p["approved_label"] == LABEL_CHAPTER and not p["metadata"].get("chapter_title_continuation")
        ]
        new_feedback_count = self._record_active_learning_feedback(inspection_report, refined)

        print(f"[Agent 2 - Quality Critic] Audit Selesai! Mengoreksi {len(corrections)} anomali.")
        print(f"[Agent 2 - Quality Critic] {new_feedback_count} sampel koreksi baru disalurkan ke Active Learning Pool.")
        print(f"[Agent 2 - Quality Critic] Bab Tervalidasi Monotonik ({len(approved_chapters)} Bab): {approved_chapters}")
        return {
            "source_doc": inspection_report["source_doc"],
            "total_paragraphs": inspection_report["total_paragraphs"],
            "total_corrections": len(corrections),
            "new_feedback_samples": new_feedback_count,
            "corrections_log": corrections,
            "final_summary": final_summary,
            "approved_chapters": approved_chapters,
            "review_queue": self._build_review_queue(review_candidates),
            "paragraphs": refined,
            "status": "APPROVED BY QUALITY CRITIC AGENT",
        }

    @staticmethod
    def _build_review_queue(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Kueri Active Learning (uncertainty sampling, least-confidence): paragraf yang membuat ML ragu
        DAN tidak dapat dipastikan oleh aturan Agent 2, sehingga perlu dikonfirmasi manusia."""
        queue = []
        for item in sorted(candidates, key=lambda it: it["confidence"])[:REVIEW_QUEUE_SIZE]:
            ranked = sorted(item["probabilities"].items(), key=lambda kv: kv[1], reverse=True)
            queue.append({
                "para_id": item["para_id"],
                "text": item["text"],
                "predicted_label": item["predicted_label"],
                "confidence": item["confidence"],
                "alternatives": ranked[:3],
                "raw_features": item["raw_features"],
            })
        return queue

    def _record_active_learning_feedback(self, inspection_report: Dict[str, Any], refined: List[Dict[str, Any]]) -> int:
        if self._active_learning is None:
            from src.active_learning import ActiveLearningManager  # impor lokal: hindari siklus impor
            self._active_learning = ActiveLearningManager()

        corrected = [p for p in refined if p["was_corrected"] and p["text"].strip()]
        try:
            return self._active_learning.record_corrections(inspection_report.get("source_doc", "dokumen"), corrected)
        except (OSError, ValueError, KeyError) as exc:
            print(f"[Agent 2 - Quality Critic] Peringatan: Tidak dapat mencatat feedback Active Learning: {exc}")
            return 0

    def coordinate_tier1_blueprint_loop(self, inspection_report: Dict[str, Any], inspector_agent=None, max_iterations: int = 3) -> Dict[str, Any]:
        """
        [SQA TIER 1: Agent 1 <-> Agent 2] Audit blueprint; jika ada koreksi, Agent 1 menerapkannya lalu
        blueprint diaudit ulang. Iterasi ulang adalah uji konsistensi (konvergen bila audit tidak lagi
        menghasilkan koreksi), bukan prediksi ulang oleh model.
        """
        current_report = inspection_report
        history = []
        all_corrections: List[Dict[str, Any]] = []
        new_feedback_samples = 0
        approved = None
        for it in range(1, max_iterations + 1):
            print(f"\n[SQA Tier 1 Gatekeeper - Iterasi {it}/{max_iterations}] Mengaudit blueprint struktur dari Agent 1...")
            approved = self.evaluate_and_refine(current_report)
            corrections = approved["corrections_log"]
            all_corrections.extend({**c, "iteration": it} for c in corrections)
            new_feedback_samples += approved["new_feedback_samples"]
            should_retry = bool(corrections) and inspector_agent is not None and it < max_iterations
            history.append({
                "iteration": it,
                "corrections_count": len(corrections),
                "approved_chapters": approved["approved_chapters"],
                "status": "FEEDBACK_SENT_TO_AGENT_1" if should_retry else ("CONVERGED" if not corrections else "CORRECTED_BY_AGENT_2"),
            })
            if not should_retry:
                break
            print(f"[SQA Tier 1 Gatekeeper] Ditemukan {len(corrections)} anomali pada draf Agent 1. Mengembalikan feedback ke Agent 1 untuk diterapkan & diuji ulang...")
            current_report = inspector_agent.re_inspect_with_feedback(current_report, corrections)

        converged = history[-1]["corrections_count"] == 0
        if converged:
            print(f"[SQA Tier 1 Gatekeeper] Blueprint konsisten (iterasi {len(history)}, total {len(all_corrections)} koreksi). Diserahkan ke Agent 3.")
        else:
            print(f"[SQA Tier 1 Gatekeeper] Blueprint belum konvergen setelah {len(history)} iterasi; "
                  f"{history[-1]['corrections_count']} koreksi terakhir diterapkan langsung oleh Agent 2.")
        # Laporan memuat seluruh koreksi lintas iterasi, bukan hanya iterasi terakhir (yang biasanya 0).
        approved["corrections_log"] = all_corrections
        approved["total_corrections"] = len(all_corrections)
        approved["new_feedback_samples"] = new_feedback_samples
        approved["sqa_tier1_history"] = history
        approved["sqa_tier1_iterations"] = len(history)
        approved["sqa_tier1_status"] = "CONVERGED" if converged else "MAX_ITERATIONS_REACHED"
        return approved

    # ------------------------------------------------------------------
    # SQA Tier 2: uji penerimaan dokumen jadi
    # ------------------------------------------------------------------
    def verify_formatted_document(self, docx_path: str) -> Dict[str, Any]:
        """
        Menguji berkas Word hasil Agent 3 terhadap 8 kriteria mutu UEU: margin 4-3-3-3, penomoran
        halaman ganda, Heading 1 rata tengah, spasi sub-bab, spasi paragraf isi, kertas A4,
        header 'Universitas Esa Unggul', dan tabel APA 7 tanpa garis vertikal.
        """
        doc = docx.Document(docx_path)
        defects: List[str] = []
        check_functions = (
            ("margin_4_3_3_3", _check_margins),
            ("dual_page_numbering", _check_page_numbering),
            ("heading1_centered", _check_heading1),
            ("subbab_spacing_12_6", _check_heading2),
            ("body_spacing_0_6_115", _check_body_paragraphs),
            ("page_size_a4", _check_page_size),
            ("header_ueu_presence", _check_header),
            ("table_apa7_borders", _check_table_borders),
        )
        checks = {}
        for name, check in check_functions:
            found = check(doc)
            checks[name] = not found
            defects.extend(found)

        passed_checks = sum(1 for ok in checks.values() if ok)
        qa_score = round(passed_checks / len(checks) * 100, 1)
        passed = not defects
        result = {
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "qa_score": qa_score,
            "score": qa_score,
            "total_checks": len(checks),
            "passed_checks": passed_checks,
            "checks": checks,
            "defects_count": len(defects),
            "defects": defects,
        }
        print(f"[Agent 2 - SQA Auditor] Audit Hasil Pemformatan: Status={result['status']} | Skor={qa_score}% | Cacat={len(defects)}")
        return result

    def coordinate_tier2_artifact_loop(self, input_docx_path: str, approved_blueprint: Dict[str, Any], output_docx_path: str, formatter_agent, max_iterations: int = 3) -> Dict[str, Any]:
        """
        [SQA TIER 2: Agent 3 <-> Agent 2] Agent 3 menyusun dokumen, Agent 2 mengujinya terhadap
        8 kriteria mutu; diulang hingga PASS atau batas iterasi tercapai.
        """
        history = []
        qa_result = None
        current_output = output_docx_path
        for it in range(1, max_iterations + 1):
            print(f"\n[SQA Tier 2 Quality Gate - Iterasi {it}/{max_iterations}] Meminta Agent 3 (Formatter) menyusun dokumen OpenXML...")
            current_output = formatter_agent.format_document(input_docx_path, approved_blueprint, current_output)
            print(f"[SQA Tier 2 Quality Gate - Iterasi {it}/{max_iterations}] Agent 2 (SQA Auditor) menguji kepatuhan naskah jadi...")
            qa_result = self.verify_formatted_document(current_output)
            history.append({
                "iteration": it,
                "qa_score": qa_result["qa_score"],
                "defects_count": len(qa_result["defects"]),
                "defects": qa_result["defects"],
                "status": "PASS" if qa_result["passed"] else "FAIL_RETRY",
            })
            if qa_result["passed"]:
                print(f"[SQA Tier 2 Quality Gate] Dokumen lolos seluruh {qa_result['total_checks']} kriteria pada iterasi ke-{it}.")
                break
            if len(history) > 1 and history[-2]["defects"] == qa_result["defects"]:
                print(f"[SQA Tier 2 Quality Gate] Cacat tidak berubah dari iterasi sebelumnya; Agent 3 tidak dapat memperbaikinya otomatis. "
                      f"{len(qa_result['defects'])} cacat dilaporkan ke pengguna.")
                break
            print(f"[SQA Tier 2 Quality Gate] Ditemukan {len(qa_result['defects'])} cacat pada iterasi ke-{it}. Mengembalikan ke Agent 3...")

        return {
            "output_path": current_output,
            "final_qa_result": qa_result,
            "tier2_iterations": len(history),
            "tier2_history": history,
            "status": "100% PASS" if qa_result and qa_result["passed"] else "PARTIAL_PASS",
        }


# ----------------------------------------------------------------------
# Kriteria SQA Tier 2 (masing-masing mengembalikan daftar cacat)
# ----------------------------------------------------------------------
def _check_margins(doc) -> List[str]:
    defects = []
    for idx, sec in enumerate(doc.sections):
        top, bottom = round(sec.top_margin.cm, 2), round(sec.bottom_margin.cm, 2)
        left, right = round(sec.left_margin.cm, 2), round(sec.right_margin.cm, 2)
        expected = ((left, 4.0), (top, 3.0), (right, 3.0), (bottom, 3.0))
        if not all(abs(actual - target) <= 0.2 for actual, target in expected):
            defects.append(f"Section {idx} margin tidak sesuai ({left}-{top}-{right}-{bottom} cm alih-alih 4-3-3-3 cm)")
    return defects


def _page_number_format(section) -> Optional[str]:
    pg_num_type = section._sectPr.find(qn("w:pgNumType"))
    return pg_num_type.attrib.get(qn("w:fmt")) if pg_num_type is not None else None


def _check_page_numbering(doc) -> List[str]:
    sections = doc.sections
    if len(sections) >= 3:
        defects = []
        if _page_number_format(sections[0]) in ("decimal", "lowerRoman"):
            defects.append("Section 0 (Cover) memiliki penomoran halaman tidak sah")
        if _page_number_format(sections[1]) != "lowerRoman":
            defects.append("Section 1 (Frontmatter) tidak menggunakan format penomoran Romawi kecil (lowerRoman)")
        if _page_number_format(sections[2]) != "decimal":
            defects.append("Section 2 (Bab Isi) tidak menggunakan format penomoran Latin (decimal)")
        return defects
    if len(sections) == 2:
        defects = []
        if _page_number_format(sections[0]) != "lowerRoman":
            defects.append("Section 0 (Frontmatter) tidak menggunakan format penomoran Romawi kecil (lowerRoman)")
        if _page_number_format(sections[1]) != "decimal":
            defects.append("Section 1 (Bab Isi) tidak menggunakan format penomoran Latin (decimal)")
        return defects
    return []


def _has_level0_num_pr(pPr) -> bool:
    num_pr = pPr.find(qn("w:numPr")) if pPr is not None else None
    ilvl = num_pr.find(qn("w:ilvl")) if num_pr is not None else None
    return ilvl is not None and ilvl.attrib.get(qn("w:val")) == "0"


def _check_heading1(doc) -> List[str]:
    defects = []
    for p in doc.paragraphs:
        if not (p.style and "Heading 1" in p.style.name):
            continue
        text = p.text.strip()
        pPr = p._p.find(qn("w:pPr"))
        is_frontmatter_title = any(k in text.upper() for k in FRONTMATTER_H1_MARKERS) or text.upper().startswith(FRONTMATTER_TITLES)
        if not H1_BAB_TEXT_RE.search(text) and not is_frontmatter_title and not _has_level0_num_pr(pPr):
            defects.append(f"Heading 1 '{text[:25]}' kehilangan kata 'BAB' (Diharuskan 'BAB X\\nJUDUL' atau numPr Word)")
        if pPr is None:
            continue
        jc = pPr.find(qn("w:jc"))
        if jc is not None and jc.attrib.get(qn("w:val")) != "center":
            defects.append(f"Heading 1 '{p.text[:25]}' tidak rata tengah (jc={jc.attrib.get(qn('w:val'))})")
        ind = pPr.find(qn("w:ind"))
        if ind is not None:
            first_line = int(ind.attrib.get(qn("w:firstLine"), "0"))
            left = int(ind.attrib.get(qn("w:left"), "0"))
            if first_line > 300 or left > 0:
                defects.append(f"Heading 1 '{p.text[:25]}' memiliki offset indentasi (firstLine={first_line}, left={left})")
    return defects


def _check_heading2(doc) -> List[str]:
    defects = []
    for p in doc.paragraphs:
        if not (p.style and "Heading 2" in p.style.name):
            continue
        text = p.text.strip()
        pPr = p._p.find(qn("w:pPr"))
        has_num_pr = pPr is not None and pPr.find(qn("w:numPr")) is not None
        if not SUBCHAPTER_NUMBER_RE.match(text) and not has_num_pr:
            defects.append(f"Sub-Bab '{text[:25]}' kehilangan penomoran bab (Diharuskan nomor '1.1' atau numPr Word)")
        spacing = pPr.find(qn("w:spacing")) if pPr is not None else None
        if spacing is None:
            continue
        after = int(spacing.attrib.get(qn("w:after"), "0"))
        before = int(spacing.attrib.get(qn("w:before"), "0"))
        if abs(after - 120) > 40:
            defects.append(f"Sub-Bab '{p.text[:25]}' spasi bawah tidak 6 pt (after={after} dxa)")
        if abs(before - 240) > 60:
            defects.append(f"Sub-Bab '{p.text[:25]}' spasi atas tidak 12 pt (before={before} dxa)")
    return defects


def _check_body_paragraphs(doc) -> List[str]:
    """Berhenti pada cacat pertama: cukup satu contoh untuk menandai kriteria gagal.

    Butir daftar (numPr), paragraf gambar, dan entri daftar pustaka (hanging indent) punya aturan spasi sendiri.
    """
    in_body = False
    for p in doc.paragraphs:
        if p.style and "Heading 1" in p.style.name and any(k in p.text.upper() for k in ("BAB", "PENDAHULUAN")):
            in_body = True
        if not (in_body and p.style and p.style.name == "Normal" and len(p.text.split()) > 15):
            continue
        pPr = p._p.find(qn("w:pPr"))
        if pPr is None or pPr.find(qn("w:numPr")) is not None or p._p.find(".//" + qn("w:drawing")) is not None:
            continue
        ind = pPr.find(qn("w:ind"))
        if ind is not None and qn("w:hanging") in ind.attrib:
            continue
        spacing = pPr.find(qn("w:spacing"))
        if spacing is not None:
            line = int(spacing.attrib.get(qn("w:line"), "276"))
            after = int(spacing.attrib.get(qn("w:after"), "120"))
            if line > 300:
                return [f"Paragraf isi memiliki spasi baris terlalu besar ({line} dxa)"]
            if abs(after - 120) > 40:
                return [f"Paragraf isi spasi bawah tidak 6 pt ({after} dxa)"]
        if ind is not None and int(ind.attrib.get(qn("w:firstLine"), "0")) == 0:
            return ["Paragraf isi tidak memiliki indentasi alinea baris pertama (firstLine=0)"]
    return []


def _check_page_size(doc) -> List[str]:
    defects = []
    for idx, sec in enumerate(doc.sections):
        width, height = round(sec.page_width.cm, 1), round(sec.page_height.cm, 1)
        if sec.orientation == WD_ORIENTATION.PORTRAIT:
            if abs(width - 21.0) > 0.4 or abs(height - 29.7) > 0.4:
                defects.append(f"Section {idx} ukuran kertas bukan A4 Portrait ({width} x {height} cm)")
        elif abs(width - 29.7) > 0.4 or abs(height - 21.0) > 0.4:
            defects.append(f"Section {idx} ukuran kertas bukan A4 Landscape ({width} x {height} cm)")
    return defects


def _check_header(doc) -> List[str]:
    for idx in range(1, len(doc.sections)):
        header_text = "".join(p.text for p in doc.sections[idx].header.paragraphs).upper()
        if "UNIVERSITAS ESA UNGGUL" not in header_text:
            return [f"Section {idx} tidak memiliki Header resmi 'Universitas Esa Unggul'"]
    return []


def _check_table_borders(doc) -> List[str]:
    defects = []
    for idx, table in enumerate(doc.tables):
        if len(table.rows) <= 1 and len(table.columns) <= 1:
            continue
        borders = table._tbl.tblPr.find(qn("w:tblBorders"))
        if borders is None:
            continue
        for side in ("w:insideV", "w:left", "w:right"):
            border = borders.find(qn(side))
            if border is not None and border.attrib.get(qn("w:val")) not in ("none", "nil"):
                defects.append(f"Tabel {idx + 1} memiliki garis vertikal yang dilarang standar APA 7")
                break
    return defects
