"""
AGENT 3: ACTUATOR (Formatting & Layout Enforcement Agent / Tukang Bedah OpenXML) - Versi Paripurna Template Resmi UEU.

Fitur Lengkap & Perbaikan Paripurna:
1. Rekonstruksi Halaman Sampul (Cover) 100% Sesuai Template Tugas Akhir Fasilkom UEU:
   - Struktur baku: Judul Skripsi (TNR 14 pt Bold ALL CAPS, Center) -> Jenis Karya ("TUGAS AKHIR" / "SKRIPSI")
     -> Keterangan Syarat Gelar (TNR 12 pt Center) -> Logo Resmi UEU 3 cm Center -> Nama & NIM (TNR 12 pt Bold Center)
     -> Program Studi, Fakultas Ilmu Komputer, Universitas Esa Unggul, Tahun (TNR 14 pt Bold Center).
   - Menggantikan cover lama yang berantakan dengan format baku resmi tanpa kehilangan data.
2. Otomatisasi Heading & Navigation Pane MS Word:
   - Menerapkan style 'Heading 1', 'Heading 2', 'Heading 3' secara otomatis pada Bab, Sub-bab, dan Frontmatter.
   - Menyuntikkan tag XML `<w:outlineLvl w:val="0"/>` dan `val="1"` sehingga Navigation Pane Word terisi otomatis.
3. Otomatisasi Daftar Isi, Daftar Tabel, dan Daftar Gambar:
   - Menyusun baris entri hierarkis lengkap dengan titik-titik tab (tab leader 'dot' 14 cm) dan nomor halaman.
   - Menyisipkan field dinamis Word TOC (`TOC \\o "1-3"`, `TOC \\c "Gambar"`, `TOC \\c "Tabel"`).
   - Mengaktifkan `<w:updateFields w:val="true"/>` agar Word otomatis memperbarui seluruh daftar dan nomor halaman saat dibuka.
4. Penomoran Halaman Ganda (Dual Page Numbering):
   - Section 0 (Cover): Bersih tanpa header dan tanpa nomor halaman.
   - Section 1 (Frontmatter): Header "Universitas Esa Unggul" kanan atas, nomor Romawi kecil ('i, ii, iii...') tengah bawah 2 cm.
   - Section 2 (Bab Isi): Header "Universitas Esa Unggul" kanan atas, nomor Latin ('1, 2, 3...') tengah bawah 2 cm mulai dari 1.
5. Tabel Standar APA 7: 3 garis horizontal, tanpa garis vertikal.
"""

import os
import io
import copy
import re
from typing import Dict, Any, List
import docx
import docx.opc.constants
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENTATION
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls

class FormattingActuatorAgent:
    """
    Agent 3: Tukang Bedah OpenXML Paripurna UEU 2018.
    """
    def __init__(self):
        print("[Agent 3 - Formatter Actuator] Diinisialisasi dengan Format Template Tugas Akhir UEU 2018.")

    def _sanitize_styles(self, doc: Document):
        """
        Membersihkan cacat indentasi bawaan dari style template,
        menghapus numPr bawaan agar Word TIDAK PERNAH menambah nomor BAB otomatis ganda,
        dan memastikan Heading 1 s/d 3 memiliki konfigurasi font & outline level yang benar.
        """
        # Bersihkan numPr dari SELURUH style dokumen agar Word TIDAK PERNAH auto-number
        for s in doc.styles:
            if hasattr(s, '_element') and s._element.pPr is not None:
                numPr = s._element.pPr.find(qn('w:numPr'))
                if numPr is not None:
                    s._element.pPr.remove(numPr)
                ind = s._element.pPr.find(qn('w:ind'))
                if ind is not None and ('Heading' in s.name or s.name in ['Title', 'List Paragraph', 'Normal2']):
                    s._element.pPr.remove(ind)
                tabs = s._element.pPr.find(qn('w:tabs'))
                if tabs is not None and ('Heading' in s.name or s.name in ['Title', 'List Paragraph', 'Normal2']):
                    s._element.pPr.remove(tabs)

        # Pastikan seluruh style Heading 1, 2, 3 dan linked character style memiliki font Times New Roman, Bold, warna Hitam (000000)
        for s_name in ['Heading 1', 'Heading 2', 'Heading 3', 'Heading 1 Char', 'Heading 2 Char', 'Heading 3 Char']:
            if s_name in doc.styles:
                s = doc.styles[s_name]
                s.font.name = 'Times New Roman'
                s.font.bold = True
                s.font.color.rgb = RGBColor(0, 0, 0)
                if '1' in s_name:
                    s.font.size = Pt(14)
                else:
                    s.font.size = Pt(12)
                
                # Konfigurasi OpenXML rPr agar Word Ribbon menampilkan preview warna hitam & bold
                rPr = s._element.get_or_add_rPr()
                for c in rPr.findall(qn('w:color')):
                    rPr.remove(c)
                rPr.append(parse_xml(r'<w:color xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="000000"/>'))
                for b in rPr.findall(qn('w:b')):
                    rPr.remove(b)
                rPr.append(parse_xml(r'<w:b xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                for rf in rPr.findall(qn('w:rFonts')):
                    rPr.remove(rf)
                rPr.append(parse_xml(r'<w:rFonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'))
                sz_val = "28" if '1' in s_name else "24"
                for sz in rPr.findall(qn('w:sz')):
                    rPr.remove(sz)
                rPr.append(parse_xml(f'<w:sz xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="{sz_val}"/>'))

                if hasattr(s, '_element') and s._element.pPr is not None:
                    numPr = s._element.pPr.find(qn('w:numPr'))
                    if numPr is not None:
                        s._element.pPr.remove(numPr)
                    ol = s._element.pPr.find(qn('w:outlineLvl'))
                    if ol is None:
                        lvl_num = "0" if '1' in s_name else ("1" if '2' in s_name else "2")
                        s._element.pPr.append(parse_xml(f'<w:outlineLvl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="{lvl_num}"/>'))

    def _to_roman(self, n: int) -> str:
        """Konversi integer ke angka Romawi kapital (1 -> I, 2 -> II, 3 -> III, dst)."""
        if not isinstance(n, int) or n <= 0:
            return str(n)
        roman_map = [
            (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
            (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
            (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")
        ]
        res = ""
        for val, rom in roman_map:
            while n >= val:
                res += rom
                n -= val
        return res

    def _ensure_heading_multilevel_list(self, doc: Document) -> str:
        """
        Memastikan definisi Multilevel List untuk Heading (BAB I, 1.1, 1.1.1) terdaftar di word/numbering.xml.
        Mengembalikan numId aktif yang mengikat abstractNum multilevel list ini.
        """
        try:
            numbering_part = doc.part.numbering_part
            numbering_elm = numbering_part._element
        except Exception:
            return "1"

        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

        # 1. Cek apakah dokumen sudah memiliki abstractNum dengan lvlText="BAB %1"
        for abs_num in numbering_elm.findall('w:abstractNum', ns):
            lvl0 = abs_num.find('w:lvl[@w:ilvl="0"]', ns)
            if lvl0 is not None:
                lvl_text = lvl0.find('w:lvlText', ns)
                if lvl_text is not None and 'BAB' in lvl_text.attrib.get(qn('w:val'), ''):
                    # Level 0 (BAB I): pStyle=Heading1, numFmt=upperRoman, suff=nothing, lvlJc=center, ind left=0 hanging=0
                    pStyle0 = lvl0.find('w:pStyle', ns)
                    if pStyle0 is not None:
                        pStyle0.set(qn('w:val'), 'Heading1')
                    else:
                        lvl0.append(parse_xml(r'<w:pStyle xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="Heading1"/>'))

                    num_fmt0 = lvl0.find('w:numFmt', ns)
                    if num_fmt0 is not None:
                        num_fmt0.set(qn('w:val'), 'upperRoman')
                    else:
                        lvl0.append(parse_xml(r'<w:numFmt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="upperRoman"/>'))
                    
                    lvl_text.set(qn('w:val'), 'BAB %1')

                    suff0 = lvl0.find('w:suff', ns)
                    if suff0 is not None:
                        suff0.set(qn('w:val'), 'nothing')
                    else:
                        lvl0.append(parse_xml(r'<w:suff xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="nothing"/>'))

                    lvlJc = lvl0.find('w:lvlJc', ns)
                    if lvlJc is not None:
                        lvlJc.set(qn('w:val'), 'center')
                    else:
                        lvl0.append(parse_xml(r'<w:lvlJc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))

                    pPr0 = lvl0.find('w:pPr', ns)
                    if pPr0 is not None:
                        ind0 = pPr0.find('w:ind', ns)
                        if ind0 is not None:
                            ind0.set(qn('w:left'), '0')
                            ind0.set(qn('w:hanging'), '0')
                    else:
                        lvl0.append(parse_xml(r'<w:pPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:ind w:left="0" w:hanging="0"/></w:pPr>'))

                    # Level 1 (1.1): pStyle=Heading2, suff=tab, lvlRestart=1, isLgl, ind left=567 hanging=567, tab pos=567
                    lvl1 = abs_num.find('w:lvl[@w:ilvl="1"]', ns)
                    if lvl1 is not None:
                        pStyle1 = lvl1.find('w:pStyle', ns)
                        if pStyle1 is not None:
                            pStyle1.set(qn('w:val'), 'Heading2')
                        else:
                            lvl1.append(parse_xml(r'<w:pStyle xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="Heading2"/>'))

                        restart1 = lvl1.find('w:lvlRestart', ns)
                        if restart1 is not None:
                            restart1.set(qn('w:val'), '1')
                        else:
                            lvl1.append(parse_xml(r'<w:lvlRestart xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="1"/>'))
                        
                        if lvl1.find('w:isLgl', ns) is None:
                            lvl1.append(parse_xml(r'<w:isLgl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))

                        lt1 = lvl1.find('w:lvlText', ns)
                        if lt1 is not None:
                            lt1.set(qn('w:val'), '%1.%2')

                        suff1 = lvl1.find('w:suff', ns)
                        if suff1 is not None:
                            suff1.set(qn('w:val'), 'tab')
                        else:
                            lvl1.append(parse_xml(r'<w:suff xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="tab"/>'))

                        pPr1 = lvl1.find('w:pPr', ns)
                        if pPr1 is not None:
                            ind1 = pPr1.find('w:ind', ns)
                            if ind1 is not None:
                                ind1.set(qn('w:left'), '720')
                                ind1.set(qn('w:hanging'), '720')
                            tabs1 = pPr1.find('w:tabs', ns)
                            if tabs1 is not None:
                                pPr1.remove(tabs1)
                            pPr1.append(parse_xml(r'<w:tabs xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:tab w:val="num" w:pos="720"/></w:tabs>'))

                    # Level 2 (1.1.1): pStyle=Heading3, suff=tab, lvlRestart=2, isLgl, ind left=720 hanging=720, tab pos=720 (1.27 cm)
                    lvl2 = abs_num.find('w:lvl[@w:ilvl="2"]', ns)
                    if lvl2 is not None:
                        pStyle2 = lvl2.find('w:pStyle', ns)
                        if pStyle2 is not None:
                            pStyle2.set(qn('w:val'), 'Heading3')
                        else:
                            lvl2.append(parse_xml(r'<w:pStyle xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="Heading3"/>'))

                        restart2 = lvl2.find('w:lvlRestart', ns)
                        if restart2 is not None:
                            restart2.set(qn('w:val'), '2')
                        else:
                            lvl2.append(parse_xml(r'<w:lvlRestart xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="2"/>'))

                        if lvl2.find('w:isLgl', ns) is None:
                            lvl2.append(parse_xml(r'<w:isLgl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))

                        lt2 = lvl2.find('w:lvlText', ns)
                        if lt2 is not None:
                            lt2.set(qn('w:val'), '%1.%2.%3')

                        suff2 = lvl2.find('w:suff', ns)
                        if suff2 is not None:
                            suff2.set(qn('w:val'), 'tab')
                        else:
                            lvl2.append(parse_xml(r'<w:suff xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="tab"/>'))

                        pPr2 = lvl2.find('w:pPr', ns)
                        if pPr2 is not None:
                            ind2 = pPr2.find('w:ind', ns)
                            if ind2 is not None:
                                ind2.set(qn('w:left'), '720')
                                ind2.set(qn('w:hanging'), '720')
                            tabs2 = pPr2.find('w:tabs', ns)
                            if tabs2 is not None:
                                pPr2.remove(tabs2)
                            pPr2.append(parse_xml(r'<w:tabs xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:tab w:val="num" w:pos="720"/></w:tabs>'))

                    abs_id = abs_num.attrib.get(qn('w:abstractNumId'))
                    for num in numbering_elm.findall('w:num', ns):
                        ref_abs = num.find('w:abstractNumId', ns)
                        if ref_abs is not None and ref_abs.attrib.get(qn('w:val')) == abs_id:
                            return str(num.attrib.get(qn('w:numId')))
                    existing_num_ids = [int(n.attrib.get(qn('w:numId'), '0')) for n in numbering_elm.findall('w:num', ns) if n.attrib.get(qn('w:numId'), '0').isdigit()]
                    new_num_id = max(existing_num_ids + [0]) + 1
                    num_elm = parse_xml(f'<w:num {nsdecls("w")} w:numId="{new_num_id}"><w:abstractNumId w:val="{abs_id}"/></w:num>')
                    numbering_elm.append(num_elm)
                    return str(new_num_id)

        # 2. Jika belum ada, buat abstractNum baru sesuai standar emas Template Tugas Akhir UEU
        existing_abs_ids = [int(a.attrib.get(qn('w:abstractNumId'), '0')) for a in numbering_elm.findall('w:abstractNum', ns) if a.attrib.get(qn('w:abstractNumId'), '0').isdigit()]
        existing_num_ids = [int(n.attrib.get(qn('w:numId'), '0')) for n in numbering_elm.findall('w:num', ns) if n.attrib.get(qn('w:numId'), '0').isdigit()]

        new_abs_id = max(existing_abs_ids + [0]) + 1
        new_num_id = max(existing_num_ids + [0]) + 1

        abstract_xml = f'''
        <w:abstractNum {nsdecls("w")} w:abstractNumId="{new_abs_id}">
            <w:nsid w:val="23A70725"/>
            <w:multiLevelType w:val="multilevel"/>
            <w:tmpl w:val="4F725FCE"/>
            <w:lvl w:ilvl="0">
                <w:start w:val="1"/>
                <w:numFmt w:val="upperRoman"/>
                <w:lvlText w:val="BAB %1"/>
                <w:lvlJc w:val="center"/>
                <w:suff w:val="nothing"/>
                <w:pPr>
                    <w:jc w:val="center"/>
                    <w:ind w:left="0" w:hanging="0"/>
                </w:pPr>
            </w:lvl>
            <w:lvl w:ilvl="1">
                <w:start w:val="1"/>
                <w:numFmt w:val="decimal"/>
                <w:lvlRestart w:val="1"/>
                <w:isLgl/>
                <w:lvlText w:val="%1.%2"/>
                <w:lvlJc w:val="left"/>
                <w:suff w:val="tab"/>
                <w:pPr>
                    <w:tabs>
                        <w:tab w:val="num" w:pos="720"/>
                    </w:tabs>
                    <w:ind w:left="720" w:hanging="720"/>
                </w:pPr>
            </w:lvl>
            <w:lvl w:ilvl="2">
                <w:start w:val="1"/>
                <w:numFmt w:val="decimal"/>
                <w:lvlRestart w:val="2"/>
                <w:isLgl/>
                <w:lvlText w:val="%1.%2.%3"/>
                <w:lvlJc w:val="left"/>
                <w:suff w:val="tab"/>
                <w:pPr>
                    <w:tabs>
                        <w:tab w:val="num" w:pos="720"/>
                    </w:tabs>
                    <w:ind w:left="720" w:hanging="720"/>
                </w:pPr>
                <w:rPr>
                    <w:b/>
                    <w:sz w:val="24"/>
                </w:rPr>
            </w:lvl>
            <w:lvl w:ilvl="3">
                <w:start w:val="1"/>
                <w:numFmt w:val="decimal"/>
                <w:lvlRestart w:val="3"/>
                <w:isLgl/>
                <w:lvlText w:val="%1.%2.%3.%4"/>
                <w:lvlJc w:val="left"/>
                <w:suff w:val="tab"/>
                <w:pPr>
                    <w:ind w:left="864" w:hanging="864"/>
                </w:pPr>
            </w:lvl>
        </w:abstractNum>
        '''

        num_xml = f'''
        <w:num {nsdecls("w")} w:numId="{new_num_id}">
            <w:abstractNumId w:val="{new_abs_id}"/>
        </w:num>
        '''

        abs_elm = parse_xml(abstract_xml)
        num_elm = parse_xml(num_xml)

        first_num = numbering_elm.find(qn('w:num'))
        if first_num is not None:
            first_num.addprevious(abs_elm)
        else:
            numbering_elm.append(abs_elm)

        numbering_elm.append(num_elm)
        return str(new_num_id)


    @staticmethod
    def _to_title_case(s: str) -> str:
        """Mengubah teks judul menjadi Title Case (Kapital Awal Kata) dengan aturan baku bahasa Indonesia."""
        if not s:
            return s
        small_words = {"dan", "atau", "yang", "di", "ke", "dari", "pada", "untuk", "dengan", "terhadap", "dalam", "tentang", "oleh", "sebagai", "atas"}
        words = s.split()
        res = []
        for idx, w in enumerate(words):
            if '-' in w:
                subparts = [p.capitalize() for p in w.split('-')]
                res.append('-'.join(subparts))
            elif idx > 0 and w.lower() in small_words:
                res.append(w.lower())
            else:
                res.append(w.capitalize())
        return ' '.join(res)

    def _reset_paragraph_indents(self, p, left_cm: float = 0.0, right_cm: float = 0.0, first_line_cm: float = 0.0, keep_numPr: bool = False):
        """Menghapus seluruh indentasi, tab, dan numPr bawaan openxml (kecuali jika keep_numPr=True) lalu menetapkan indentasi presisi."""
        pPr = p._p.get_or_add_pPr()
        existing_ind = pPr.find(qn('w:ind'))
        if existing_ind is not None:
            pPr.remove(existing_ind)
        existing_tabs = pPr.find(qn('w:tabs'))
        if existing_tabs is not None:
            pPr.remove(existing_tabs)
        if not keep_numPr:
            existing_num = pPr.find(qn('w:numPr'))
            if existing_num is not None:
                pPr.remove(existing_num)
        
        p.paragraph_format.left_indent = Cm(left_cm)
        p.paragraph_format.right_indent = Cm(right_cm)
        p.paragraph_format.first_line_indent = Cm(first_line_cm)

    def _is_template_comment(self, text: str) -> bool:
        """Mendeteksi apakah sebuah paragraf adalah teks instruksi/komentar placeholder template."""
        t = text.strip()
        if not t:
            return False
        if t.startswith('{') and any(k in t.lower() for k in [
            'komentar', 'hapus untuk dokumen final', 'berisi', 'menunjukkan', 
            'metode', 'menjelaskan', 'formulir', 'petunjuk'
        ]):
            return True
        if t.startswith('{') and t.endswith('}') and len(t) > 15:
            return True
        if t.startswith('Petunjuk:') or t.startswith('Petunjuk :'):
            return True
        low = t.lower()
        if 'update seluruh daftar' in low or 'update entire table' in low:
            return True
        if 'untuk insert daftar isi' in low or 'untuk update daftar gambar' in low or 'untuk insert daftar gambar' in low:
            return True
        if 'lihat petunjuk di daftar gambar' in low:
            return True
        if 'lakukan hal serupa untuk menambahkan daftar tabel' in low:
            return True
        if 'contoh pemberian caption' in low and 'petunjuk:' in low:
            return True
        return False

    def _set_para_tabs(self, p, tab_positions_cm: List[float]):
        """Menetapkan posisi Tab Stop pada paragraf secara presisi melalui OpenXML."""
        pPr = p._p.get_or_add_pPr()
        existing_tabs = pPr.find(qn('w:tabs'))
        if existing_tabs is not None:
            pPr.remove(existing_tabs)
        tabs_el = parse_xml(r'<w:tabs xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
        for pos_cm in tab_positions_cm:
            dxa = int(round(pos_cm * 567.0))
            t = parse_xml(f'<w:tab xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="left" w:pos="{dxa}"/>')
            tabs_el.append(t)
        pPr.append(tabs_el)

    def _align_metadata_field(self, p, text: str, context: str = '') -> bool:
        """
        Merapikan baris metadata (Nama, NIM, Program Studi, Judul, Tim Penguji, Tanggal, dll.)
        dengan Tab Stop presisi sesuai standar Template Emas UEU.
        """
        clean_line = re.sub(r'[\t\s]+', ' ', text).strip()
        if not clean_line:
            return False

        # Tangani baris subordinat seperti "Fakultas Ilmu Komputer - Universitas Esa Unggul" di bawah Program Studi
        if clean_line.lower().startswith('fakultas ') and 'universitas' in clean_line.lower() and ':' not in clean_line:
            p.text = f"\t\t{clean_line}"
            self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
            self._set_para_tabs(p, [4.0, 4.5])
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.font.color.rgb = RGBColor(0, 0, 0)
            return True

        # Deteksi metadata bilingual (Indonesia & Inggris)
        m = re.match(
            r'^(Nama|Name|NIM|Student\s*ID|Program\s*Studi|Study\s*Program|Fakultas|Faculty|Jurusan|Department|Konsentrasi|Concentration|Judul\s*(?:Tugas\s*Akhir|Skripsi)?|Title|Jenis\s*Karya\s*Ilmiah|Tanda\s*Tangan|Signature|Tanggal|Date|Dibuat\s*di|Pada\s*tanggal|Pembimbing.*|Advisor.*|Supervisor.*|Penguji.*|Examiner.*|Ketua\s*Program\s*Studi|Head\s*of\s*Study\s*Program|Ditetapkan\s*di|Keywords?|Kata\s*kunci)\s*[:：]\s*(.*)$',
            clean_line,
            flags=re.IGNORECASE
        )
        if not m:
            return False

        key = m.group(1).strip()
        val = m.group(2).strip()
        val = re.sub(r'^\s*[:：]\s*', '', val).strip()
        key_low = key.lower()

        # 1. Grup Tim Penguji & Pengesahan Ujian (Pembimbing, Penguji I/II, Ketua Program Studi, Ditetapkan di, Tanggal)
        if any(k in key_low for k in ['pembimbing', 'penguji', 'ketua program studi', 'ditetapkan di']) or (key_low == 'tanggal' and 'penguji' in context):
            sig_m = re.search(r'(\([\.…\s]*tanda\s+tangan[\.…\s]*\))', val, flags=re.IGNORECASE)
            if sig_m:
                sig_text = sig_m.group(1)
                val_clean = val[:sig_m.start()].strip()
                p.text = f"{key}\t: {val_clean}\t{sig_text}"
            else:
                p.text = f"{key}\t: {val}"
            self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
            self._set_para_tabs(p, [3.75, 10.0])

        # 2. Grup Pernyataan Keaslian (di atas Box Materai)
        elif 'pernyataan' in context or (key_low in ['nama', 'nim', 'tanda tangan', 'tanggal'] and 'materai' in context):
            p.text = f"{key}\t:\t{val}"
            self._reset_paragraph_indents(p, left_cm=3.75, right_cm=0.0, first_line_cm=0.0)
            self._set_para_tabs(p, [6.5, 7.0])

        # 3. Grup Penutup Lokasi & Tanggal (Dibuat di, Pada tanggal)
        elif any(k in key_low for k in ['dibuat di', 'pada tanggal']):
            p.text = f"{key}\t: {val}"
            self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
            self._set_para_tabs(p, [3.75])

        # 4. Grup Abstrak & Abstract (Template Baku UEU: tab colon 3.0 cm, text 3.5 cm)
        elif 'abstract' in context or 'abstrak' in context:
            if 'judul' in key_low or key_low == 'title':
                p.text = f"{key}\t:\t{val}"
                self._reset_paragraph_indents(p, left_cm=3.5, right_cm=0.0, first_line_cm=-3.5)
                self._set_para_tabs(p, [3.0, 3.5])
            elif 'kata kunci' in key_low or 'keyword' in key_low:
                p.text = f"{key}\t: {val}"
                self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
                self._set_para_tabs(p, [3.0])
            else:
                p.text = f"{key}\t:\t{val}"
                self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
                self._set_para_tabs(p, [3.0, 3.5])

        # 5. Judul Tugas Akhir / Title di Pengesahan (Hanging indent presisi 4.0 cm)
        elif 'judul' in key_low or key_low == 'title':
            p.text = f"{key}\t:\t{val}"
            self._reset_paragraph_indents(p, left_cm=4.0, right_cm=0.0, first_line_cm=-4.0)
            self._set_para_tabs(p, [3.5, 4.0])

        # 6. Metadata Standar (Pengesahan Identitas, Persetujuan Publikasi)
        else:
            p.text = f"{key}\t:\t{val}"
            self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
            self._set_para_tabs(p, [3.5, 4.0])

        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)

        # Standar Tipografi: Di bagian ABSTRACT bahasa Inggris, seluruh metadata dicetak miring (Italic=True, Bold=False)
        # Di bagian lain (Indonesia), seluruh metadata seragam dicetak tegak (Italic=False, Bold=False)
        is_english_abstract = ('abstract' in context) or (key_low in ['title', 'name', 'study program', 'keywords', 'keyword', 'faculty', 'department', 'advisor', 'supervisor', 'examiner'])
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
            r.bold = False
            r.italic = True if is_english_abstract else False
            r.font.color.rgb = RGBColor(0, 0, 0)
        return True

    def _italicize_foreign_terms(self, p):
        """Mencetak miring (italic) istilah/kata asing dalam paragraf bahasa Indonesia sesuai pedoman EYD."""
        if not hasattr(self, '_foreign_pattern'):
            foreign_terms = [
                # AI / ML / Data Science
                "machine learning", "deep learning", "artificial intelligence",
                "multi-agent system", "multi-agent systems", "multi-agent", "natural language processing",
                "large language model", "large language models", "neural network", "neural networks",
                "convolutional neural network", "recurrent neural network", "transformer", "transformers",
                "reinforcement learning", "supervised learning", "unsupervised learning", "semi-supervised learning",
                "transfer learning", "fine-tuning", "fine tuning", "prompt engineering", "zero-shot", "few-shot",
                "ground truth", "overfitting", "underfitting", "hyperparameter", "hyperparameters",
                "gradient descent", "backpropagation", "loss function", "cross-validation",
                "random forest", "decision tree", "support vector machine", "naive bayes",
                "confusion matrix", "accuracy", "precision", "recall", "f1-score", "f1 score",
                "mean squared error", "root mean squared error", "dataset", "datasets",
                "data warehouse", "data mining", "data mart", "data lake",
                "preprocessing", "tokenization", "lemmatization", "stemming", "stopword", "stopwords",
                "word embedding", "word embeddings", "vectorization", "feature extraction", "feature selection",
                "benchmark", "benchmarks", "baseline", "epoch", "epochs", "batch size", "learning rate",
                "state-of-the-art", "state of the art",
                # Software Engineering / IT / Cloud
                "user interface", "user experience", "cloud computing",
                "open source", "real-time", "real time", "web server", "web service",
                "client-server", "middleware", "pipeline", "pipelines", "framework", "frameworks",
                "frontend", "backend", "full stack", "software", "hardware",
                "database", "databases", "online", "offline", "bug", "bugs", "debugging",
                "use case", "use cases", "class diagram", "sequence diagram", "activity diagram",
                "flowchart", "entity relationship diagram", "data flow diagram",
                "mockup", "wireframe", "scrum", "agile", "sprint", "backlog", "waterfall",
                "continuous integration", "continuous deployment", "version control",
                "repository", "repositories", "endpoint", "endpoints", "request", "response",
                "payload", "microservice", "microservices", "docker", "container", "containers",
                "api", "rest api", "crud", "query", "syntax", "runtime", "compile", "compiler",
                "deploy", "deployment",
                # Academic / Scientific / Latin
                "et al.", "et al", "ibid.", "ibid", "op. cit.", "loc. cit.",
                "ad hoc", "vice versa", "de facto", "de jure", "in vitro", "in vivo",
                "per se", "a priori", "a posteriori"
            ]
            self._foreign_pattern = re.compile(
                r'\b(' + '|'.join(re.escape(term) for term in sorted(foreign_terms, key=len, reverse=True)) + r')\b',
                re.IGNORECASE
            )

        full_text = p.text
        if not full_text or not self._foreign_pattern.search(full_text):
            return

        tokens = []
        last_idx = 0
        for match in self._foreign_pattern.finditer(full_text):
            start, end = match.span()
            if start > last_idx:
                tokens.append((full_text[last_idx:start], False))
            tokens.append((full_text[start:end], True))
            last_idx = end
        if last_idx < len(full_text):
            tokens.append((full_text[last_idx:], False))

        p.text = ''
        for text_part, is_it in tokens:
            r = p.add_run(text_part)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(12)
            r.bold = False
            r.italic = is_it
            r.font.color.rgb = RGBColor(0, 0, 0)

    def _format_materai_box(self, table):
        """Format kotak materai pada Halaman Pernyataan Keaslian sesuai template resmi UEU (di sebelah kanan titik dua)."""
        tblPr = table._tbl.tblPr

        # Hapus perataan center pada tabel agar indentasi tblInd aktif
        tbl_jc = tblPr.find(qn('w:jc'))
        if tbl_jc is not None:
            tblPr.remove(tbl_jc)

        # Atur lebar kotak (~5.0 cm / 2835 dxa) dan indentasi kiri presisi ke kanan titik dua (~7.19 cm / 4076 dxa)
        tbl_w_xml = parse_xml(r'<w:tblW xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:w="2835" w:type="dxa"/>')
        existing_w = tblPr.find(qn('w:tblW'))
        if existing_w is not None:
            tblPr.remove(existing_w)
        tblPr.append(tbl_w_xml)

        tbl_ind_xml = parse_xml(r'<w:tblInd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:w="4076" w:type="dxa"/>')
        existing_ind = tblPr.find(qn('w:tblInd'))
        if existing_ind is not None:
            tblPr.remove(existing_ind)
        tblPr.append(tbl_ind_xml)

        # Border 4 sisi (single line hitam tipis)
        borders_xml = parse_xml(r'''
            <w:tblBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                <w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:insideH w:val="none"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
        ''')
        existing_borders = tblPr.find(qn('w:tblBorders'))
        if existing_borders is not None:
            tblPr.remove(existing_borders)
        tblPr.append(borders_xml)

        # Format teks di dalam sel
        for r in table.rows:
            for cell in r.cells:
                tcPr = cell._tc.get_or_add_tcPr()
                tc_w_xml = parse_xml(r'<w:tcW xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:w="2835" w:type="dxa"/>')
                existing_tc_w = tcPr.find(qn('w:tcW'))
                if existing_tc_w is not None:
                    tcPr.remove(existing_tc_w)
                tcPr.append(tc_w_xml)

                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(10)
                        run.font.color.rgb = RGBColor(0, 0, 0)

    def _format_table_apa7(self, table):
        """Menerapkan standar APA 7 termodifikasi pada tabel: garis horizontal di setiap baris, tanpa garis vertikal, TNR 10 pt spasi 1.0."""
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = table._tbl.tblPr

        borders_xml = parse_xml(r'''
            <w:tblBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                <w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>
                <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>
                <w:left w:val="none"/>
                <w:right w:val="none"/>
                <w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
        ''')
        existing_borders = tblPr.find(qn('w:tblBorders'))
        if existing_borders is not None:
            tblPr.remove(existing_borders)
        tblPr.append(borders_xml)

        if len(table.rows) == 0:
            return

        header_row = table.rows[0]
        for cell in header_row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            # Shading abu-abu standar template (#D9D9D9)
            existing_shd = tcPr.find(qn('w:shd'))
            if existing_shd is not None:
                tcPr.remove(existing_shd)
            tcPr.append(parse_xml(r'<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="clear" w:color="auto" w:fill="D9D9D9"/>'))

            tcBorders = parse_xml(r'''
                <w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                    <w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>
                    <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>
                    <w:left w:val="none"/>
                    <w:right w:val="none"/>
                </w:tcBorders>
            ''')
            existing_tc_b = tcPr.find(qn('w:tcBorders'))
            if existing_tc_b is not None:
                tcPr.remove(existing_tc_b)
            tcPr.append(tcBorders)

            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.0
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(10)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0, 0, 0)

        num_rows = len(table.rows)
        for r_idx in range(1, num_rows):
            row = table.rows[r_idx]
            is_last_row = (r_idx == num_rows - 1)
            for cell in row.cells:
                tcPr = cell._tc.get_or_add_tcPr()
                if is_last_row:
                    tcBorders = parse_xml(r'''
                        <w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                            <w:top w:val="none"/>
                            <w:left w:val="none"/>
                            <w:right w:val="none"/>
                            <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>
                        </w:tcBorders>
                    ''')
                else:
                    tcBorders = parse_xml(r'''
                        <w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                            <w:top w:val="none"/>
                            <w:left w:val="none"/>
                            <w:right w:val="none"/>
                            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                        </w:tcBorders>
                    ''')
                existing_tc_b = tcPr.find(qn('w:tcBorders'))
                if existing_tc_b is not None:
                    tcPr.remove(existing_tc_b)
                tcPr.append(tcBorders)

                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.0
                    for r in p.runs:
                        r.font.name = "Times New Roman"
                        r.font.size = Pt(10)
                        r.font.color.rgb = RGBColor(0, 0, 0)

        # Standar Integritas Tabel Akademik: Mencegah baris terpotong terbelah (cantSplit)
        # dan memastikan baris header otomatis berulang jika tabel lintas halaman (tblHeader)
        for r_idx, row in enumerate(table.rows):
            trPr = row._tr.get_or_add_trPr()
            if trPr.find(qn('w:cantSplit')) is None:
                trPr.append(parse_xml(r'<w:cantSplit xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
            if r_idx == 0 and trPr.find(qn('w:tblHeader')) is None:
                trPr.append(parse_xml(r'<w:tblHeader xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))

    def _add_seq_caption_field(self, p, seq_name: str, bab_num: int, item_num: int, title_text: str):
        """
        Menyisipkan dynamic Word Fields untuk nomor caption gambar/tabel:
        - { STYLEREF 1 \\s } -> Nomor bab otomatis (Word field shading abu-abu)
        - .                  -> Pemisah titik
        - { SEQ <seq_name> \\* ARABIC \\s 1 } -> Nomor urut otomatis (Word field shading abu-abu)
        - title_text         -> Judul caption (misal ' Lorem Ipsum')
        """
        # Field 1: STYLEREF 1 \s
        r1_begin = parse_xml(r'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>')
        r1_instr = parse_xml(r'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:instrText xml:space="preserve"> STYLEREF 1 \s </w:instrText></w:r>')
        r1_sep = parse_xml(r'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>')
        r1_val = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/><w:noProof/></w:rPr><w:t>{bab_num}</w:t></w:r>')
        r1_end = parse_xml(r'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>')

        # Separator '.'
        r_dot = parse_xml(r'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:t>.</w:t></w:r>')

        # Field 2: SEQ <seq_name> \* ARABIC \s 1
        r2_begin = parse_xml(r'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>')
        r2_instr = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:instrText xml:space="preserve"> SEQ {seq_name} \\* ARABIC \\s 1 </w:instrText></w:r>')
        r2_sep = parse_xml(r'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>')
        r2_val = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/><w:noProof/></w:rPr><w:t>{item_num}</w:t></w:r>')
        r2_end = parse_xml(r'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>')

        for el in [r1_begin, r1_instr, r1_sep, r1_val, r1_end, r_dot, r2_begin, r2_instr, r2_sep, r2_val, r2_end]:
            p._p.append(el)

        if title_text:
            r_title = p.add_run(title_text)
            r_title.font.name = "Times New Roman"
            r_title.font.size = Pt(12)
            r_title.font.bold = True
            r_title.font.color.rgb = RGBColor(0, 0, 0)

    def _enforce_a4_and_margins(self, doc: Document):
        """
        Memastikan SELURUH section di dokumen 100% berukuran A4 Portrait (21.0 cm x 29.7 cm)
        dan memiliki margin resmi UEU: Kiri 4 cm, Atas 3 cm, Kanan 3 cm, Bawah 3 cm,
        serta membersihkan orientasi landscape dan ukuran kertas non-A4 (misal Letter/Legal).
        """
        # 1. Atur via python-docx API
        for section in doc.sections:
            try:
                section.orientation = WD_ORIENTATION.PORTRAIT
            except Exception:
                pass
            section.page_width = Cm(21.0)
            section.page_height = Cm(29.7)
            section.top_margin = Cm(3.0)
            section.bottom_margin = Cm(3.0)
            section.left_margin = Cm(4.0)
            section.right_margin = Cm(3.0)
            section.header_distance = Cm(2.0)
            section.footer_distance = Cm(2.0)

        # 2. Atur via OpenXML secara absolut pada seluruh tag w:sectPr yang ada di tubuh dokumen
        for sectPr in doc._element.body.iter(qn('w:sectPr')):
            pgSz = sectPr.find(qn('w:pgSz'))
            if pgSz is None:
                pgSz = parse_xml(r'<w:pgSz xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:w="11906" w:h="16838" w:orient="portrait" w:code="9"/>')
                sectPr.append(pgSz)
            else:
                pgSz.set(qn('w:w'), '11906')       # A4 Width (210 mm)
                pgSz.set(qn('w:h'), '16838')       # A4 Height (297 mm)
                pgSz.set(qn('w:orient'), 'portrait')
                pgSz.set(qn('w:code'), '9')        # ISO A4 code di Word

            pgMar = sectPr.find(qn('w:pgMar'))
            if pgMar is None:
                pgMar = parse_xml(r'<w:pgMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:top="1701" w:right="1701" w:bottom="1701" w:left="2268" w:header="1134" w:footer="1134" w:gutter="0"/>')
                sectPr.append(pgMar)
            else:
                pgMar.set(qn('w:top'), '1701')      # 3.0 cm
                pgMar.set(qn('w:bottom'), '1701')   # 3.0 cm
                pgMar.set(qn('w:left'), '2268')     # 4.0 cm
                pgMar.set(qn('w:right'), '1701')    # 3.0 cm
                pgMar.set(qn('w:header'), '1134')   # 2.0 cm
                pgMar.set(qn('w:footer'), '1134')   # 2.0 cm
                pgMar.set(qn('w:gutter'), '0')

    def _create_section_break_xml(self):
        """Membuat elemen XML sectPr pemisah halaman lengkap dengan ukuran A4 dan margin baku UEU (Kiri 4 cm, Atas 3 cm, Kanan 3 cm, Bawah 3 cm)."""
        return parse_xml(r'''
            <w:sectPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                <w:type w:val="nextPage"/>
                <w:pgSz w:w="11906" w:h="16838" w:orient="portrait" w:code="9"/>
                <w:pgMar w:top="1701" w:right="1701" w:bottom="1701" w:left="2268" w:header="1134" w:footer="1134" w:gutter="0"/>
            </w:sectPr>
        ''')

    def _setup_dual_page_numbering(self, doc: Document, first_bab_para_id: int):
        """
        Menyusun pemisahan section dan penomoran ganda yang langsung ter-render di Word:
        - Section 0 (Cover): Tanpa Header, Tanpa Nomor Halaman.
        - Section 1 (Frontmatter): Header UEU, Nomor Romawi kecil di tengah bawah 2 cm.
        - Section 2 (Bab Isi): Header UEU, Nomor Latin di tengah bawah 2 cm mulai dari 1.
        """
        # Cari paragraf pertama BAB ISI secara akurat dan dinamis pada doc.paragraphs terkini
        target_bab_idx = -1
        for idx, p in enumerate(doc.paragraphs):
            lbl = p._p.get('approved_label')
            txt = p.text.strip().upper()
            if lbl == "JUDUL_BAB" or (p.style and 'Heading 1' in p.style.name and any(txt.startswith(k) for k in ["BAB ", "BAB I", "BAB 1", "PENDAHULUAN"])):
                target_bab_idx = idx
                break

        if target_bab_idx == -1 and first_bab_para_id > 0 and first_bab_para_id < len(doc.paragraphs):
            target_bab_idx = first_bab_para_id

        if target_bab_idx > 0:
            prev_p = doc.paragraphs[target_bab_idx - 1]
            prev_p._p.set('is_section_break_carrier', 'true')
            pPr = prev_p._p.get_or_add_pPr()
            if not prev_p._p.xpath('./w:pPr/w:sectPr'):
                sect_break = self._create_section_break_xml()
                pPr.append(sect_break)

        def inject_page_number_field(footer, alignment=WD_ALIGN_PARAGRAPH.CENTER, default_char="1"):
            footer.is_linked_to_previous = False
            p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            p.text = ""
            p.alignment = alignment
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            fld_xml = parse_xml(f'''
                <w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr="PAGE">
                    <w:r>
                        <w:rPr>
                            <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
                            <w:sz w:val="24"/>
                        </w:rPr>
                        <w:t>{default_char}</w:t>
                    </w:r>
                </w:fldSimple>
            ''')
            p._p.append(fld_xml)

        def set_section_pgnum_type(section, fmt="decimal", start=None):
            sectPr = section._sectPr
            existing = sectPr.find(qn('w:pgNumType'))
            if existing is not None:
                sectPr.remove(existing)
            if start is not None:
                xml = f'<w:pgNumType xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fmt="{fmt}" w:start="{start}"/>'
            else:
                xml = f'<w:pgNumType xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fmt="{fmt}"/>'
            sectPr.append(parse_xml(xml))

        def inject_header_ueu(header):
            header.is_linked_to_previous = False
            p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            p.text = "UNIVERSITAS ESA UNGGUL"
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            for r in p.runs:
                r.font.name = "Arial"
                r.font.size = Pt(10)
                r.font.bold = True
                r.font.color.rgb = RGBColor(0, 0, 0)

        for sec in doc.sections:
            sec.footer_distance = Cm(2.0)

        has_cover = getattr(self, 'has_cover', True)
        total_sections = len(doc.sections)

        if has_cover and total_sections >= 3:
            # Section 0: Cover (bersih tanpa header dan nomor)
            sec_cover = doc.sections[0]
            sec_cover.footer.is_linked_to_previous = False
            if sec_cover.footer.paragraphs:
                sec_cover.footer.paragraphs[0].text = ""
            sec_cover.header.is_linked_to_previous = False
            if sec_cover.header.paragraphs:
                sec_cover.header.paragraphs[0].text = ""

            # Section 1: Frontmatter (Romawi kecil di tengah bawah 2 cm, Header UEU)
            sec_front = doc.sections[1]
            set_section_pgnum_type(sec_front, fmt="lowerRoman", start=1)
            inject_page_number_field(sec_front.footer, default_char="i")
            inject_header_ueu(sec_front.header)

            # Section 2+: Bab Isi (Angka Latin mulai 1 di tengah bawah 2 cm, Header UEU)
            for s_idx, sec_body in enumerate(doc.sections[2:]):
                set_section_pgnum_type(sec_body, fmt="decimal", start=1 if s_idx == 0 else None)
                inject_page_number_field(sec_body.footer, default_char="1")
                inject_header_ueu(sec_body.header)
        elif has_cover and total_sections == 2:
            # Cover + Bab Isi
            sec_cover = doc.sections[0]
            sec_cover.footer.is_linked_to_previous = False
            if sec_cover.footer.paragraphs:
                sec_cover.footer.paragraphs[0].text = ""
            sec_cover.header.is_linked_to_previous = False
            if sec_cover.header.paragraphs:
                sec_cover.header.paragraphs[0].text = ""

            sec_body = doc.sections[1]
            set_section_pgnum_type(sec_body, fmt="decimal", start=1)
            inject_page_number_field(sec_body.footer, default_char="1")
            inject_header_ueu(sec_body.header)
        elif not has_cover and total_sections >= 2:
            # Frontmatter + Bab Isi
            sec_front = doc.sections[0]
            set_section_pgnum_type(sec_front, fmt="lowerRoman", start=1)
            inject_page_number_field(sec_front.footer, default_char="i")
            inject_header_ueu(sec_front.header)

            for s_idx, sec_body in enumerate(doc.sections[1:]):
                set_section_pgnum_type(sec_body, fmt="decimal", start=1 if s_idx == 0 else None)
                inject_page_number_field(sec_body.footer, default_char="1")
                inject_header_ueu(sec_body.header)
        else:
            sec = doc.sections[0]
            set_section_pgnum_type(sec, fmt="decimal", start=1)
            inject_page_number_field(sec.footer, default_char="1")
            inject_header_ueu(sec.header)

    def _protect_original_cover(self, doc: Document, blueprint_paras: List[Dict[str, Any]]):
        """
        Menangani Halaman Sampul (Cover):
        Cover asli dokumen DIPERTAHANKAN 100% UTUH APA ADANYA!
        Tidak mengubah isi, layout, teks, gambar/logo, atau susunan cover asli.
        Menandai seluruh paragraf cover sebagai COVER_PARAGRAPH agar tidak terpengaruh format isi naskah,
        serta memastikan adanya pemisah Section Break setelah cover agar halaman cover tidak memuat nomor halaman.
        """
        first_fm_idx = -1
        first_bab_idx = -1
        for p_info in blueprint_paras:
            lbl = p_info["approved_label"]
            p_id = p_info["para_id"]
            if lbl == "FRONTMATTER_TITLE" and first_fm_idx == -1:
                first_fm_idx = p_id
            if lbl == "JUDUL_BAB" and first_bab_idx == -1:
                first_bab_idx = p_id

        cover_end_idx = first_fm_idx if first_fm_idx != -1 else first_bab_idx
        self.has_cover = bool(cover_end_idx is not None and cover_end_idx > 2)

        if not self.has_cover:
            print("[Agent 3 - Formatter Actuator] Dokumen tidak memiliki halaman cover tersendiri. Memformat langsung isi naskah...")
            return

        print(f"[Agent 3 - Formatter Actuator] Mempertahankan cover asli dokumen 100% utuh (paragraf 0 sampai {cover_end_idx - 1}).")
        for i in range(min(cover_end_idx, len(doc.paragraphs))):
            doc.paragraphs[i]._p.set('approved_label', "COVER_PARAGRAPH")

        # Pastikan ada pemisah section break setelah cover agar halaman cover bersih dari header/footer
        if cover_end_idx > 0 and cover_end_idx < len(doc.paragraphs):
            p_last_cover = doc.paragraphs[cover_end_idx - 1]
            pPr = p_last_cover._p.get_or_add_pPr()
            if not p_last_cover._p.xpath('./w:pPr/w:sectPr'):
                sect_break = self._create_section_break_xml()
                pPr.append(sect_break)
        return

    def _generate_table_of_contents(self, doc: Document, blueprint_paras: List[Dict[str, Any]], has_frontmatter: bool = True):
        """
        Menyusun otomatis Daftar Isi, Daftar Gambar, dan Daftar Tabel
        dengan tab leader titik-titik (dot), nomor halaman dinamis berbasis estimasi layout akurat,
        dan field PAGEREF Word yang terhubung ke bookmark heading di naskah dokumen.
        """
        print("[Agent 3 - Formatter Actuator] Menyusun otomatis Daftar Isi, Daftar Tabel, dan Daftar Gambar dengan penomoran dinamis...")

        def to_roman(n: int) -> str:
            val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
            syb = ["m", "cm", "d", "cd", "c", "xc", "l", "xl", "x", "ix", "v", "iv", "i"]
            res = ""
            for i in range(len(val)):
                while n >= val[i]:
                    res += syb[i]
                    n -= val[i]
            return res or "i"

        romawi_map_inv = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}
        bm_counter = 100
        fm_page_count = 0
        body_page = 1
        accum_lines = 0
        current_bab = 0
        current_sub = 0
        current_subsub = 0

        toc_entries = []
        figure_entries = []
        table_entries = []
        seen_figures = set()
        seen_tables = set()

        # Helper menambah baris TOC dengan titik-titik dan PAGEREF field
        def add_toc_item(p_target, text, page_str, bm_id, indent_lvl=0, is_bold=False):
            p = p_target.insert_paragraph_before()
            p._p.set('approved_label', "TOC_PARAGRAPH")
            try:
                p.style = doc.styles['Normal']
            except Exception:
                pass

            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Cm(0.5 * indent_lvl)
            p.paragraph_format.right_indent = Cm(0)
            p.paragraph_format.first_line_indent = Cm(0)

            pPr = p._p.get_or_add_pPr()
            numPr = pPr.find(qn('w:numPr'))
            if numPr is not None:
                pPr.remove(numPr)
            ol = pPr.find(qn('w:outlineLvl'))
            if ol is not None:
                pPr.remove(ol)

            # Tab stop kanan pada 14.0 cm (7937 dxa) dengan titik-titik (dot leader)
            tabs_xml = parse_xml(r'''
                <w:tabs xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                    <w:tab w:val="right" w:leader="dot" w:pos="7937"/>
                </w:tabs>
            ''')
            pPr.append(tabs_xml)

            r1 = p.add_run(text)
            r1.font.name = "Times New Roman"
            r1.font.size = Pt(12)
            r1.font.bold = is_bold
            r1.font.color.rgb = RGBColor(0, 0, 0)

            r_tab = p.add_run('\t')

            r2 = p.add_run(page_str)
            r2.font.name = "Times New Roman"
            r2.font.size = Pt(12)
            r2.font.bold = is_bold
            r2.font.color.rgb = RGBColor(0, 0, 0)

        # Single-pass: Ambil seluruh entri dokumen dari awal hingga akhir secara kronologis
        in_body = False
        body_ended = False
        current_fig_num = 0
        current_tbl_num = 0

        for idx, p in enumerate(doc.paragraphs):
            lbl = p._p.get('approved_label')
            text = p.text.strip()
            if not text:
                continue

            # A. Frontmatter (sebelum Bab 1): Halaman Romawi (i, ii, iii, iv...)
            if lbl == "FRONTMATTER_TITLE" and not in_body and not body_ended:
                if any(k in text.upper() for k in ["PENGESAHAN", "PERSETUJUAN", "PUBLIKASI", "PERNYATAAN", "KATA PENGANTAR", "PRAKATA", "ABSTRAK", "ABSTRACT", "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR", "DAFTAR SIMBOL"]):
                    if not any(k in text.upper() for k in ["NAMA", "NIM", "WAKTU", "TANDA TANGAN", "TANGGAL"]):
                        clean_fm = re.sub(r'^(BAB\s*(\d+|[IVXLCDM]+)[\s:\.\-]*)+', '', text, flags=re.IGNORECASE).strip()
                        clean_fm = re.sub(r'^\d+(\.\d+)*\s*', '', clean_fm).strip()
                        if clean_fm and clean_fm.upper() != "UNTUK KEPENTINGAN AKADEMIS":
                            fm_page_count += 1
                            page_str = to_roman(fm_page_count)
                            bm_id = f"_Toc{bm_counter}"
                            bm_counter += 1

                            bm_start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{bm_counter}" w:name="{bm_id}"/>')
                            bm_end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{bm_counter}"/>')
                            p._p.insert(0, bm_start)
                            p._p.append(bm_end)

                            toc_title = clean_fm.split('\n')[0].strip().upper()
                            toc_entries.append((toc_title, page_str, bm_id, 0, False))

            # B. Judul Bab: Halaman Latin (1, 2, 3...)
            elif lbl == "JUDUL_BAB":
                in_body = True
                current_bab += 1
                current_sub = 0
                current_subsub = 0
                current_fig_num = 0
                current_tbl_num = 0
                if current_bab == 1:
                    body_page = 1
                    accum_lines = 0
                else:
                    body_page += 1
                    accum_lines = 0

                clean_title = re.sub(r'^(BAB\s*(\d+|[IVXLCDM]+)[\s:\.\-]*)+', '', text, flags=re.IGNORECASE).strip()
                clean_title = f"BAB {self._to_roman(current_bab)} {clean_title.upper()}"
                bm_id = f"_Toc{bm_counter}"
                bm_counter += 1

                bm_start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{bm_counter}" w:name="{bm_id}"/>')
                bm_end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{bm_counter}"/>')
                p._p.insert(0, bm_start)
                p._p.append(bm_end)

                toc_entries.append((clean_title, str(body_page), bm_id, 0, False))
                accum_lines += 3

            # C. Sub-Bab & Sub-Sub-Bab
            elif lbl == "SUB_BAB" and in_body:
                is_subsub = bool(
                    p._p.get('is_subsub') == 'true' or
                    re.match(r'^\d+\.\d+\.\d+', text) or
                    p.style.name in ["Heading 3", "Heading3"]
                )
                clean_sub = re.sub(r'^((\d+|[A-Za-z])\.)+(\d+)*\s*', '', text).strip()
                clean_sub = re.sub(r'^\d+(\.\d+)*\s*', '', clean_sub).strip()

                if is_subsub:
                    current_subsub += 1
                    sub_idx = current_sub if current_sub > 0 else 1
                    sub_title = f"{current_bab}.{sub_idx}.{current_subsub} {clean_sub}"
                    indent_lvl = 2
                else:
                    current_sub += 1
                    current_subsub = 0
                    sub_title = f"{current_bab}.{current_sub} {clean_sub}"
                    indent_lvl = 1

                bm_id = f"_Toc{bm_counter}"
                bm_counter += 1

                bm_start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{bm_counter}" w:name="{bm_id}"/>')
                bm_end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{bm_counter}"/>')
                p._p.insert(0, bm_start)
                p._p.append(bm_end)

                toc_entries.append((sub_title, str(body_page), bm_id, indent_lvl, False))
                accum_lines += 2
                if accum_lines >= 26:
                    body_page += 1
                    accum_lines = 0

            # D. Backmatter (setelah Bab selesai: DAFTAR PUSTAKA, LAMPIRAN 1..N): Halaman Latin Lanjutan
            elif lbl == "FRONTMATTER_TITLE" and in_body:
                body_ended = True
                clean_fm = re.sub(r'^(BAB\s*(\d+|[IVXLCDM]+)[\s:\.\-]*)+', '', text, flags=re.IGNORECASE).strip().upper()
                body_page += 1
                accum_lines = 0
                bm_id = f"_Toc{bm_counter}"
                bm_counter += 1

                bm_start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{bm_counter}" w:name="{bm_id}"/>')
                bm_end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{bm_counter}"/>')
                p._p.insert(0, bm_start)
                p._p.append(bm_end)

                toc_entries.append((clean_fm, str(body_page), bm_id, 0, False))

            # E. Caption Gambar
            elif lbl == "CAPTION_GAMBAR":
                current_fig_num += 1
                clean_cap = re.sub(r'^(Gambar|Figure)\s*([\d\.\-]+\s*[:\.]?|\.\s*[:\.]?|[:\.]\s*)', '', text, flags=re.IGNORECASE).strip()
                if not clean_cap or clean_cap == text.strip():
                    clean_cap = re.sub(r'^(Gambar|Figure)\s*(\.\s*)?', '', text, flags=re.IGNORECASE).strip()
                clean_cap = re.sub(r'^\.\s*', '', clean_cap).strip()
                clean_cap = re.sub(r'\t\d+$', '', clean_cap).strip()
                fig_title = f"Gambar {current_bab if current_bab > 0 else 1}.{current_fig_num} {clean_cap}"
                if fig_title not in seen_figures and len(clean_cap.split()) <= 25:
                    seen_figures.add(fig_title)
                    bm_id = f"_Toc{bm_counter}"
                    bm_counter += 1
                    bm_start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{bm_counter}" w:name="{bm_id}"/>')
                    bm_end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{bm_counter}"/>')
                    pPr_exist = p._p.find(qn('w:pPr'))
                    if pPr_exist is not None:
                        pPr_exist.addnext(bm_start)
                    else:
                        p._p.insert(0, bm_start)
                    p._p.append(bm_end)
                    figure_entries.append((fig_title, str(body_page if in_body else 1), bm_id))

            # F. Caption Tabel
            elif lbl == "CAPTION_TABEL":
                current_tbl_num += 1
                clean_cap = re.sub(r'^(Tabel|Table)\s*([\d\.\-]+\s*[:\.]?|\.\s*[:\.]?|[:\.]\s*)', '', text, flags=re.IGNORECASE).strip()
                if not clean_cap or clean_cap == text.strip():
                    clean_cap = re.sub(r'^(Tabel|Table)\s*(\.\s*)?', '', text, flags=re.IGNORECASE).strip()
                clean_cap = re.sub(r'^\.\s*', '', clean_cap).strip()
                clean_cap = re.sub(r'\t\d+$', '', clean_cap).strip()
                tbl_title = f"Tabel {current_bab if current_bab > 0 else 1}.{current_tbl_num} {clean_cap}"
                if tbl_title not in seen_tables and len(clean_cap.split()) <= 25:
                    seen_tables.add(tbl_title)
                    bm_id = f"_Toc{bm_counter}"
                    bm_counter += 1
                    bm_start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{bm_counter}" w:name="{bm_id}"/>')
                    bm_end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{bm_counter}"/>')
                    pPr_exist = p._p.find(qn('w:pPr'))
                    if pPr_exist is not None:
                        pPr_exist.addnext(bm_start)
                    else:
                        p._p.insert(0, bm_start)
                    p._p.append(bm_end)
                    table_entries.append((tbl_title, str(body_page if in_body else 1), bm_id))

            elif in_body and lbl == "BODY_PARAGRAPH":
                words = len(text.split())
                lines = max(1, (words + 11) // 12) + 1
                accum_lines += lines
                while accum_lines >= 26:
                    body_page += 1
                    accum_lines -= 26

        # Cek apakah dokumen SUDAH memiliki Native Word TOC (w:sdt dengan Table of Contents)
        existing_toc_sdt = None
        for sdt in doc._body._element.xpath('.//w:sdt'):
            sdt_text = ''.join(sdt.itertext()).upper()
            if any(k in sdt_text for k in ["TABLE OF CONTENTS", "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR"]):
                existing_toc_sdt = sdt
                break

        # Jika naskah SUDAH memiliki Native TOC Word (w:sdt), PERTAHANKAN 100% dan JANGAN HAPUS!
        # Hanya bersihkan sdt rusak atau sdt yang tidak memiliki konten valid.
        if existing_toc_sdt is not None:
            print("[Agent 3 - Formatter Actuator] Dokumen memiliki Native Word TOC (w:sdt). Mempertahankan 100% blok TOC asli...")
            # Cukup aktifkan updateFields di settings agar Word otomatis merefresh halaman saat dibuka
            try:
                settings_elm = doc.settings.element
                if settings_elm.find(qn('w:updateFields')) is None:
                    settings_elm.append(parse_xml(r'<w:updateFields xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="true"/>'))
            except Exception:
                pass
            return

        # Temukan paragraf pertama BAB 1 naskah asli (anchor point sebelum Bab Isi)
        anchor_bab_p = None
        for p in doc.paragraphs:
            if p._p.get('approved_label') == "TOC_PARAGRAPH":
                continue
            up_t = p.text.strip().upper()
            if p._p.get('approved_label') == "JUDUL_BAB" or any(up_t.startswith(k) for k in ["BAB 1", "BAB I", "PENDAHULUAN"]):
                anchor_bab_p = p
                break

        # Pastikan DAFTAR ISI, DAFTAR TABEL, DAFTAR GAMBAR masuk ke Daftar Isi sebagai entri halaman awal (Romawi)
        first_bab_idx = next((i for i, e in enumerate(toc_entries) if e[0].startswith("BAB ")), len(toc_entries))
        extra_fm = []
        if not any(e[0] == "DAFTAR ISI" for e in toc_entries):
            fm_page_count += 1
            extra_fm.append(("DAFTAR ISI", to_roman(fm_page_count), f"_Toc{bm_counter}", 0, False))
            bm_counter += 1
        if table_entries and not any(e[0] == "DAFTAR TABEL" for e in toc_entries):
            fm_page_count += 1
            extra_fm.append(("DAFTAR TABEL", to_roman(fm_page_count), f"_Toc{bm_counter}", 0, False))
            bm_counter += 1
        if figure_entries and not any(e[0] == "DAFTAR GAMBAR" for e in toc_entries):
            fm_page_count += 1
            extra_fm.append(("DAFTAR GAMBAR", to_roman(fm_page_count), f"_Toc{bm_counter}", 0, False))
            bm_counter += 1

        for item in reversed(extra_fm):
            toc_entries.insert(first_bab_idx, item)

        # 3. Sisipkan item pada DAFTAR ISI, DAFTAR TABEL, DAFTAR GAMBAR (Sesuai urutan baku UEU)
        frontmatter_targets = [("DAFTAR ISI", toc_entries)]
        if table_entries:
            frontmatter_targets.append(("DAFTAR TABEL", table_entries))
        if figure_entries:
            frontmatter_targets.append(("DAFTAR GAMBAR", figure_entries))

        for target_title, entries in frontmatter_targets:
            target_p = None
            for p in doc.paragraphs:
                if p._p.get('approved_label') == "TOC_PARAGRAPH":
                    continue
                if p.text.strip().upper() == target_title:
                    target_p = p
                    break

            was_created = False
            if target_p is None:
                if len(entries) > 0 and anchor_bab_p is not None:
                    target_p = anchor_bab_p.insert_paragraph_before()
                    target_p._p.set('approved_label', "FRONTMATTER_TITLE")
                    r_tp = target_p.add_run(target_title)
                    r_tp.font.name = "Times New Roman"
                    r_tp.font.size = Pt(14)
                    r_tp.font.bold = True
                    r_tp.font.color.rgb = RGBColor(0, 0, 0)
                    was_created = True
                else:
                    continue

            # Terapkan Heading 1 resmi UEU agar muncul di Navigation Word & terdaftar di hierarki
            try:
                target_p.style = doc.styles['Heading 1']
            except Exception:
                pass

            target_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            target_p.paragraph_format.line_spacing = 1.0
            target_p.paragraph_format.space_before = Pt(0)
            target_p.paragraph_format.space_after = Pt(12)
            if not has_frontmatter and target_title == "DAFTAR ISI":
                target_p.paragraph_format.page_break_before = False
            else:
                target_p.paragraph_format.page_break_before = True
            target_p.paragraph_format.keep_with_next = True

            pPr_tgt = target_p._p.get_or_add_pPr()

            # Pastikan outlineLvl=0 untuk Heading 1 (Word Navigation Pane)
            ex_ol = pPr_tgt.find(qn('w:outlineLvl'))
            if ex_ol is not None:
                pPr_tgt.remove(ex_ol)
            pPr_tgt.append(parse_xml(r'<w:outlineLvl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="0"/>'))

            # Pastikan jc=center
            ex_jc = pPr_tgt.find(qn('w:jc'))
            if ex_jc is not None:
                pPr_tgt.remove(ex_jc)
            pPr_tgt.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))

            # Hapus numPr agar tidak ada nomor otomatis atau peluru bullet pada judul daftar
            numPr_tgt = pPr_tgt.find(qn('w:numPr'))
            if numPr_tgt is not None:
                pPr_tgt.remove(numPr_tgt)

            # Bersihkan indents dan pastikan left=0, right=0, firstLine=0 (center mutlak tanpa pergeseran)
            ex_ind = pPr_tgt.find(qn('w:ind'))
            if ex_ind is not None:
                pPr_tgt.remove(ex_ind)
            pPr_tgt.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="0" w:right="0" w:firstLine="0"/>'))

            if not has_frontmatter and target_title == "DAFTAR ISI":
                ex_pb = pPr_tgt.find(qn('w:pageBreakBefore'))
                if ex_pb is not None:
                    pPr_tgt.remove(ex_pb)
            else:
                if pPr_tgt.find(qn('w:pageBreakBefore')) is None:
                    pPr_tgt.append(parse_xml(r'<w:pageBreakBefore xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
            if pPr_tgt.find(qn('w:keepNext')) is None:
                pPr_tgt.append(parse_xml(r'<w:keepNext xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))

            if not was_created:
                # Halaman sudah ada di template lama, bersihkan sampah teks manual lama di bawahnya
                parent = target_p._p.getparent()
                all_p_elements = list(parent.iterchildren(qn('w:p')))
                if target_p._p not in all_p_elements:
                    continue
                tgt_idx = all_p_elements.index(target_p._p)

                next_heading_p = None
                del_idx = tgt_idx + 1
                while del_idx < len(all_p_elements):
                    elem = all_p_elements[del_idx]
                    curr_p_list = [p for p in doc.paragraphs if p._p == elem]
                    if curr_p_list:
                        cp = curr_p_list[0]
                        ct = cp.text.strip().upper()
                        is_boundary = (
                            cp._p.get('approved_label') != "TOC_PARAGRAPH" and
                            (cp.style.name in ["Heading 1", "Heading1"] or cp._p.get('approved_label') == "JUDUL_BAB" or any(ct == k for k in ["DAFTAR ISI", "DAFTAR GAMBAR", "DAFTAR TABEL", "BAB 1", "BAB 1 PENDAHULUAN", "BAB I PENDAHULUAN", "PENDAHULUAN"]))
                        )
                        if is_boundary and cp._p != target_p._p:
                            next_heading_p = cp
                            break
                    parent.remove(elem)
                    del_idx += 1

                if next_heading_p is not None:
                    for entry in entries:
                        if len(entry) == 5:
                            item_text, item_page, item_bm, item_lvl, item_bold = entry
                            add_toc_item(next_heading_p, item_text, item_page, item_bm, indent_lvl=item_lvl, is_bold=item_bold)
                        elif len(entry) == 3:
                            item_text, item_page, item_bm = entry
                            add_toc_item(next_heading_p, item_text, item_page, item_bm, indent_lvl=0, is_bold=False)
            else:
                # Halaman baru dibuat: masukkan seluruh item sebelum anchor_bab_p
                for entry in entries:
                    if len(entry) == 5:
                        item_text, item_page, item_bm, item_lvl, item_bold = entry
                        add_toc_item(anchor_bab_p, item_text, item_page, item_bm, indent_lvl=item_lvl, is_bold=item_bold)
                    elif len(entry) == 3:
                        item_text, item_page, item_bm = entry
                        add_toc_item(anchor_bab_p, item_text, item_page, item_bm, indent_lvl=0, is_bold=False)

        # Pastikan updateFields TIDAK ada di settings agar Word tidak memunculkan popup dialog
        # 'This document contains fields that may refer to other files'
        try:
            settings_elm = doc.settings.element
            existing_up = settings_elm.find(qn('w:updateFields'))
            if existing_up is not None:
                settings_elm.remove(existing_up)
        except Exception:
            pass

    def _deep_clone_paragraph_to_doc(self, p_src_elem, doc_src, doc_out, label: str = "BODY_PARAGRAPH", after_elem=None):
        """
        Melakukan deep-clone PENUH elemen paragraf XML dari dokumen sumber ke dokumen output.
        Mempertahankan 100% konten: gambar, rumus OpenXML (m:oMath), OLE objects, field codes,
        hyperlinks, bookmarks, dan semua elemen XML lainnya tanpa perubahan apapun.
        Hanya me-remap relationship ID gambar agar file gambar ikut tersalin.
        """
        clone = copy.deepcopy(p_src_elem)
        clone.set('approved_label', label)

        # Re-map relationship ID untuk setiap gambar/blip yang ditemukan
        for blip in clone.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
            rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            if rid and rid in doc_src.part.rels:
                try:
                    img_blob = doc_src.part.rels[rid].target_part.blob
                    img_part = doc_out.part.package.get_or_add_image_part(io.BytesIO(img_blob))
                    new_rid = doc_out.part.relate_to(img_part, docx.opc.constants.RELATIONSHIP_TYPE.IMAGE)
                    blip.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed', new_rid)
                except Exception:
                    pass

        # Re-map relationship ID untuk OLE objects dan imagedata (w:pict)
        for imagedata in clone.findall('.//{urn:schemas-microsoft-com:vml}imagedata'):
            rid = imagedata.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            if rid and rid in doc_src.part.rels:
                try:
                    target_part = doc_src.part.rels[rid].target_part
                    img_blob = target_part.blob
                    img_part = doc_out.part.package.get_or_add_image_part(io.BytesIO(img_blob))
                    new_rid = doc_out.part.relate_to(img_part, docx.opc.constants.RELATIONSHIP_TYPE.IMAGE)
                    imagedata.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', new_rid)
                except Exception:
                    pass

        # Re-map hyperlink relationships
        for hyperlink in clone.findall('.//' + qn('w:hyperlink')):
            rid = hyperlink.attrib.get(qn('r:id'))
            if not rid:
                rid = hyperlink.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            if rid and rid in doc_src.part.rels:
                try:
                    rel = doc_src.part.rels[rid]
                    if rel.is_external:
                        from docx.opc.constants import RELATIONSHIP_TYPE as RT
                        new_rid = doc_out.part.rels._get_matching(RT.HYPERLINK, rel.target_ref) or \
                                  doc_out.part.rels.get_or_add_ext_rel(RT.HYPERLINK, rel.target_ref)
                        if hasattr(new_rid, 'rId'):
                            new_rid = new_rid.rId
                        hyperlink.set(qn('r:id'), str(new_rid))
                except Exception:
                    pass

        # Sisipkan elemen deep-clone ke body dokumen output
        if after_elem is not None:
            after_elem.addnext(clone)
        else:
            sectPr = doc_out.element.body.find(qn('w:sectPr'))
            if sectPr is not None:
                sectPr.addprevious(clone)
            else:
                doc_out.element.body.append(clone)
        return clone

    def _deep_clone_table_to_doc(self, tbl_src_elem, doc_src, doc_out, after_elem=None):
        """
        Melakukan deep-clone PENUH elemen tabel XML dari dokumen sumber ke dokumen output.
        Mempertahankan 100% konten sel termasuk gambar, rumus, dan format asli.
        """
        clone = copy.deepcopy(tbl_src_elem)

        # Re-map gambar dalam sel tabel
        for blip in clone.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
            rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            if rid and rid in doc_src.part.rels:
                try:
                    img_blob = doc_src.part.rels[rid].target_part.blob
                    img_part = doc_out.part.package.get_or_add_image_part(io.BytesIO(img_blob))
                    new_rid = doc_out.part.relate_to(img_part, docx.opc.constants.RELATIONSHIP_TYPE.IMAGE)
                    blip.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed', new_rid)
                except Exception:
                    pass

        if after_elem is not None:
            after_elem.addnext(clone)
        else:
            sectPr = doc_out.element.body.find(qn('w:sectPr'))
            if sectPr is not None:
                sectPr.addprevious(clone)
            else:
                doc_out.element.body.append(clone)
        return clone

    def _para_has_rich_content(self, p_elem):
        """
        Mendeteksi apakah paragraf mengandung konten kaya (gambar, rumus, OLE, field codes)
        meskipun teks biasa-nya kosong.
        """
        # Gambar (drawing / pict)
        if p_elem.findall('.//' + qn('w:drawing')) or p_elem.findall('.//' + qn('w:pict')):
            return True
        # Rumus OpenXML (Office Math)
        ns_m = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
        if p_elem.findall(f'.//{{{ns_m}}}oMath') or p_elem.findall(f'.//{{{ns_m}}}oMathPara'):
            return True
        # OLE Objects
        if p_elem.findall('.//{urn:schemas-microsoft-com:office:office}OLEObject'):
            return True
        # Field codes (fldSimple atau fldChar)
        if p_elem.findall('.//' + qn('w:fldSimple')) or p_elem.findall('.//' + qn('w:fldChar')):
            return True
        return False

    def format_via_cloned_template(self, input_docx_path: str, approved_blueprint: Dict[str, Any], output_docx_path: str = "output/hasil_skripsi_rapi.docx", cover_data: Dict[str, str] = None) -> str:
        """
        Mengeksekusi pemformatan naskah dengan metode Cloned Template Seed resmi UEU (P1).
        Menjamin 100% kompatibilitas Multilevel List native Word (BAB I, 1.1, 1.2, 2.1)
        dengan blok abu-abu solid saat diklik, margin presisi 4-3-3-3 cm, preservasi 100%
        semua elemen (zero-content loss), dan struktur halaman depan - bab isi - daftar isi yang paripurna.
        """
        print(f"\n[Agent 3 - Formatter Actuator] Memulai kloning template resmi UEU untuk: {input_docx_path}...")
        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "template_clean_ueu.docx")
        if not os.path.exists(template_path):
            template_path = "data/template_clean_ueu.docx"

        doc_src = Document(input_docx_path)
        doc_out = Document(template_path)

        # Pastikan Multilevel List di doc_out memakai upperRoman untuk Level 0 (BAB I, II, III...) dan isLgl untuk Level 1-2
        try:
            self._ensure_heading_multilevel_list(doc_out)
            num_part = doc_out.part.numbering_part
            for anum in num_part._element.findall(qn('w:abstractNum')):
                if anum.attrib.get(qn('w:abstractNumId')) == '2':
                    lvl0 = anum.find(qn('w:lvl'))
                    if lvl0 is not None:
                        suff = lvl0.find(qn('w:suff'))
                        if suff is None:
                            lvl0.append(parse_xml(r'<w:suff xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="none"/>'))
                        else:
                            suff.set(qn('w:val'), 'none')
                        lvlJc = lvl0.find(qn('w:lvlJc'))
                        if lvlJc is not None:
                            lvlJc.set(qn('w:val'), 'center')
                        num_fmt0 = lvl0.find(qn('w:numFmt'))
                        if num_fmt0 is not None:
                            num_fmt0.set(qn('w:val'), 'upperRoman')
        except Exception:
            pass

        # Cek paragraf pertama Bab 1 (JUDUL_BAB)
        first_bab_src_idx = None
        for i, p in enumerate(doc_src.paragraphs):
            up = p.text.strip().upper()
            if any(up.startswith(k) for k in ["BAB 1", "BAB I", "PENDAHULUAN", "BAB 01"]) or p._p.get('approved_label') == "JUDUL_BAB":
                first_bab_src_idx = i
                break

        has_frontmatter = (first_bab_src_idx is not None and first_bab_src_idx > 0)

        body_elem = doc_out.element.body
        # Simpan sectPr resmi untuk Section 0 (Cover - tanpa nomor), Section 1 (Frontmatter - lowerRoman) dan Section 2 (Bab Isi - decimal)
        sec0_sect_pr = copy.deepcopy(doc_out.sections[0]._sectPr) if len(doc_out.sections) > 0 else None
        sec1_sect_pr = copy.deepcopy(doc_out.sections[1]._sectPr) if len(doc_out.sections) > 1 else None
        sec2_sect_pr = copy.deepcopy(doc_out.sections[2]._sectPr) if len(doc_out.sections) > 2 else copy.deepcopy(doc_out.sections[-1]._sectPr)

        # Bersihkan elemen paragraf/tabel dummy bawaan template (pertahankan sectPr akhir)
        for c in list(body_elem):
            if c.tag != qn('w:sectPr'):
                body_elem.remove(c)

        # === ZERO-LOSS TABLE MAPPING ===
        # Petakan setiap w:tbl ke indeks paragraf (para_id) yang mendahuluinya di dokumen sumber
        table_after_para = {}
        current_para_count = 0
        for child in doc_src.element.body:
            if child.tag == qn('w:p'):
                current_para_count += 1
            elif child.tag == qn('w:tbl'):
                pred_p_idx = max(0, current_para_count - 1)
                if pred_p_idx not in table_after_para:
                    table_after_para[pred_p_idx] = []
                table_after_para[pred_p_idx].append(child)
        inserted_tables = set()

        src_tables = list(doc_src.tables)
        current_bab = 0
        current_sub = 0
        current_subsub = 0
        current_gambar = 0
        current_tabel = 0

        # Inisialisasi generator numId untuk numbered list independen per sub-bab
        num_part = doc_out.part.numbering_part
        existing_nums = num_part._element.findall(qn('w:num'))
        next_list_num_id = max([int(n.attrib.get(qn('w:numId'), 0)) for n in existing_nums] or [0]) + 1
        src_to_out_numid = {}
        last_was_list = False

        # === INJEKSI KONTEN LENGKAP (FRONTMATTER + BAB ISI + BACKMATTER) ===
        for item in approved_blueprint.get("paragraphs", []):
            lbl = item["approved_label"]
            txt = item.get("text", "").strip()
            meta = item.get("metadata", {})
            orig_idx = item.get("para_id", 0)
            p_src = doc_src.paragraphs[orig_idx] if orig_idx < len(doc_src.paragraphs) else None

            # -------------------------------------------------------------
            # A. FRONTMATTER TITLE (ABSTRAK, ABSTRACT, KATA PENGANTAR, dll.)
            # -------------------------------------------------------------
            if lbl == "FRONTMATTER_TITLE":
                p = doc_out.add_paragraph()
                p._p.set('approved_label', 'FRONTMATTER_TITLE')
                try:
                    p.style = doc_out.styles['Heading 1']
                except Exception:
                    pass
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pPr = p._p.get_or_add_pPr()
                pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))
                if len(doc_out.paragraphs) > 1:
                    pPr.append(parse_xml(r'<w:pageBreakBefore xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                pPr.append(parse_xml(r'<w:keepNext xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="480" w:after="240" w:line="240" w:lineRule="auto"/>'))
                pPr.append(parse_xml(r'<w:outlineLvl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="0"/>'))
                clean_fm = re.sub(r'^(BAB\s*(\d+|[IVXLCDM]+)[\s:\.\-]*)+', '', txt, flags=re.IGNORECASE).strip().upper()
                r_txt = p.add_run(clean_fm if clean_fm else txt.upper())
                r_txt.font.name = "Times New Roman"
                r_txt.font.size = Pt(14)
                r_txt.font.bold = True
                r_txt.font.color.rgb = RGBColor(0, 0, 0)

            # -------------------------------------------------------------
            # B. COVER METADATA (Judul Skripsi, Nama, NIM, Logo)
            # -------------------------------------------------------------
            elif lbl == "COVER_METADATA":
                if p_src is not None and self._para_has_rich_content(p_src._p):
                    self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label='COVER_METADATA')
                elif txt:
                    p = doc_out.add_paragraph()
                    p._p.set('approved_label', 'COVER_METADATA')
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    pPr = p._p.get_or_add_pPr()
                    pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))
                    pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="120" w:line="276" w:lineRule="auto"/>'))
                    r = p.add_run(txt)
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(14 if orig_idx == 0 else 12)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0, 0, 0)

            # -------------------------------------------------------------
            # C. JUDUL BAB (Heading 1 + BAB I / II / III + Outline Level 0)
            # -------------------------------------------------------------
            elif lbl == "JUDUL_BAB":
                current_bab += 1
                current_sub = 0
                current_subsub = 0
                current_gambar = 0
                current_tabel = 0
                src_to_out_numid.clear()
                last_was_list = False

                clean_title = re.sub(r'^(BAB\s*(\d+|[IVXLCDM]+)[\s:\.\-]*)+', '', txt, flags=re.IGNORECASE).strip()
                if not clean_title:
                    clean_title = "PENDAHULUAN" if current_bab == 1 else f"BAB {self._to_roman(current_bab)}"

                p = doc_out.add_paragraph()
                p._p.set('approved_label', 'JUDUL_BAB')
                p.style = doc_out.styles['Heading 1']
                pPr = p._p.get_or_add_pPr()

                numPr = parse_xml(r'<w:numPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>')
                pPr.append(numPr)
                pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))
                if current_bab > 1:
                    pPr.append(parse_xml(r'<w:pageBreakBefore xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                pPr.append(parse_xml(r'<w:keepNext xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="240" w:line="240" w:lineRule="auto"/>'))
                pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="0" w:right="0" w:firstLine="284"/>'))
                pPr.append(parse_xml(r'<w:outlineLvl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="0"/>'))

                r_br = p.add_run()
                r_br._r.append(parse_xml(r'<w:br xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                r_br.font.name = "Times New Roman"
                r_br.font.size = Pt(14)
                r_br.font.bold = True
                r_txt = p.add_run(clean_title.upper())
                r_txt.font.name = "Times New Roman"
                r_txt.font.size = Pt(14)
                r_txt.font.bold = True
                r_txt.font.color.rgb = RGBColor(0, 0, 0)

            # -------------------------------------------------------------
            # D. SUB-BAB & SUB-SUB-BAB (Heading 2 / Heading 3)
            # -------------------------------------------------------------
            elif lbl == "SUB_BAB":
                src_to_out_numid.clear()
                last_was_list = False
                is_subsub = bool(meta.get("is_subsub") or re.match(r'^\d+\.\d+\.\d+', txt))
                clean_sub = re.sub(r'^((\d+|[A-Za-z])\.)+(\d+)*\s*', '', txt).strip()
                clean_sub = re.sub(r'^\d+(\.\d+)*\s*', '', clean_sub).strip()
                clean_title = self._to_title_case(clean_sub)

                p = doc_out.add_paragraph()
                p._p.set('approved_label', 'SUB_BAB')
                p._p.set('is_subsub', 'true' if is_subsub else 'false')
                pPr = p._p.get_or_add_pPr()

                if is_subsub:
                    current_subsub += 1
                    p.style = doc_out.styles['Heading 3']
                    ilvl_val = "2"
                    lvl_val = "2"
                    pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="160" w:after="120" w:line="240" w:lineRule="auto"/>'))
                    pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="720" w:hanging="720"/>'))
                    pPr.append(parse_xml(r'<w:tabs xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:tab w:val="left" w:pos="720"/></w:tabs>'))
                else:
                    current_sub += 1
                    current_subsub = 0
                    p.style = doc_out.styles['Heading 2']
                    ilvl_val = "1"
                    lvl_val = "1"
                    pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="240" w:after="120" w:line="240" w:lineRule="auto"/>'))
                    pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="720" w:hanging="720"/>'))
                    pPr.append(parse_xml(r'<w:tabs xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:tab w:val="left" w:pos="720"/></w:tabs>'))

                numPr = parse_xml(f'<w:numPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:ilvl w:val="{ilvl_val}"/><w:numId w:val="1"/></w:numPr>')
                pPr.append(numPr)
                pPr.append(parse_xml(r'<w:keepNext xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                pPr.append(parse_xml(f'<w:outlineLvl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="{lvl_val}"/>'))

                r_txt = p.add_run(clean_title)
                r_txt.font.name = "Times New Roman"
                r_txt.font.size = Pt(12)
                r_txt.font.bold = True
                r_txt.font.color.rgb = RGBColor(0, 0, 0)

            # -------------------------------------------------------------
            # E. BODY PARAGRAPH
            # -------------------------------------------------------------
            elif lbl == "BODY_PARAGRAPH":
                has_drawings = bool(p_src._p.findall('.//' + qn('w:drawing')) or p_src._p.findall('.//' + qn('w:pict'))) if p_src is not None else False
                has_rich = self._para_has_rich_content(p_src._p) if p_src is not None else False

                # Jika berada di Frontmatter (sebelum Bab 1):
                if current_bab == 0:
                    if p_src is not None and has_rich:
                        self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label='BODY_PARAGRAPH')
                    elif txt:
                        p = doc_out.add_paragraph()
                        p._p.set('approved_label', 'BODY_PARAGRAPH')
                        pPr = p._p.get_or_add_pPr()
                        is_kw = any(txt.lower().startswith(k) for k in ["kata kunci", "keywords", "kata kunci:", "keywords:"])
                        if is_kw and ":" in txt:
                            pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="both"/>'))
                            pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="120" w:after="120" w:line="276" w:lineRule="auto"/>'))
                            parts = txt.split(":", 1)
                            r1 = p.add_run(parts[0].strip() + ": ")
                            r1.font.name = "Times New Roman"
                            r1.font.size = Pt(12)
                            r1.font.bold = True
                            r2 = p.add_run(parts[1].strip())
                            r2.font.name = "Times New Roman"
                            r2.font.size = Pt(12)
                            r2.font.italic = True
                        else:
                            pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="both"/>'))
                            pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="120" w:line="276" w:lineRule="auto"/>'))
                            r = p.add_run(txt)
                            r.font.name = "Times New Roman"
                            r.font.size = Pt(12)
                    elif p_src is not None and len(list(p_src._p)) > (1 if p_src._p.find(qn('w:pPr')) is not None else 0):
                        self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label='BODY_PARAGRAPH')

                # Jika berada di Bab Isi (Bab 1+):
                elif has_drawings or meta.get("has_img"):
                    clone = self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label='BODY_PARAGRAPH')
                    clone_pPr = clone.get_or_add_pPr()
                    old_numPr = clone_pPr.find(qn('w:numPr'))
                    if old_numPr is not None:
                        clone_pPr.remove(old_numPr)
                    old_jc = clone_pPr.find(qn('w:jc'))
                    if old_jc is not None:
                        clone_pPr.remove(old_jc)
                    clone_pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))
                    old_sp = clone_pPr.find(qn('w:spacing'))
                    if old_sp is not None:
                        clone_pPr.remove(old_sp)
                    clone_pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="120" w:after="60"/>'))

                elif has_rich and not txt:
                    print(f"[Agent 3 - Formatter] Zero-Loss: Deep-cloning paragraf kaya #{orig_idx} (rumus/OLE/field)")
                    self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label='BODY_PARAGRAPH')

                elif txt:
                    if p_src is not None and has_rich:
                        clone = self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label='BODY_PARAGRAPH')
                        clone_pPr = clone.get_or_add_pPr()
                        old_jc = clone_pPr.find(qn('w:jc'))
                        if old_jc is not None:
                            clone_pPr.remove(old_jc)
                        clone_pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="both"/>'))
                        old_sp = clone_pPr.find(qn('w:spacing'))
                        if old_sp is not None:
                            clone_pPr.remove(old_sp)
                        clone_pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="120" w:line="276" w:lineRule="auto"/>'))
                        old_ind = clone_pPr.find(qn('w:ind'))
                        if old_ind is not None:
                            clone_pPr.remove(old_ind)
                        clone_pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="0" w:right="0" w:firstLine="720"/>'))
                    else:
                        p = doc_out.add_paragraph()
                        p._p.set('approved_label', 'BODY_PARAGRAPH')
                        pPr = p._p.get_or_add_pPr()

                        src_pPr = p_src._p.find(qn('w:pPr')) if p_src is not None else None
                        src_numPr = src_pPr.find(qn('w:numPr')) if src_pPr is not None else None

                        if src_numPr is not None:
                            src_nid_el = src_numPr.find(qn('w:numId'))
                            src_nid = src_nid_el.attrib.get(qn('w:val'), '0') if src_nid_el is not None else '0'

                            if src_nid not in src_to_out_numid:
                                new_nid = str(next_list_num_id)
                                next_list_num_id += 1
                                target_abs_id = "1"
                                new_num_el = parse_xml(f'<w:num xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:numId="{new_nid}"><w:abstractNumId w:val="{target_abs_id}"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride><w:lvlOverride w:ilvl="1"><w:startOverride w:val="1"/></w:lvlOverride><w:lvlOverride w:ilvl="2"><w:startOverride w:val="1"/></w:lvlOverride></w:num>')
                                num_part._element.append(new_num_el)
                                src_to_out_numid[src_nid] = new_nid
                            out_numId = src_to_out_numid[src_nid]

                            src_ilvl = src_numPr.find(qn('w:ilvl')).attrib.get(qn('w:val'), '0') if src_numPr.find(qn('w:ilvl')) is not None else '0'

                            numPr_out = parse_xml(f'<w:numPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:ilvl w:val="{src_ilvl}"/><w:numId w:val="{out_numId}"/></w:numPr>')
                            pPr.append(numPr_out)
                            pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="both"/>'))
                            pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="60" w:line="276" w:lineRule="auto"/>'))
                            pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="720" w:hanging="360"/>'))
                            last_was_list = True
                        else:
                            last_was_list = False
                            p.style = doc_out.styles['Normal']
                            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                            pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="both"/>'))
                            pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="120" w:line="276" w:lineRule="auto"/>'))
                            pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="0" w:right="0" w:firstLine="720"/>'))

                        r = p.add_run(txt)
                        r.font.name = "Times New Roman"
                        r.font.size = Pt(12)
                        r.font.color.rgb = RGBColor(0, 0, 0)
                        self._italicize_foreign_terms(p)

                elif p_src is not None and len(list(p_src._p)) > (1 if p_src._p.find(qn('w:pPr')) is not None else 0):
                    self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label='BODY_PARAGRAPH')

            # -------------------------------------------------------------
            # F. CAPTION GAMBAR
            # -------------------------------------------------------------
            elif lbl == "CAPTION_GAMBAR":
                current_gambar += 1
                cap_clean = re.sub(r'^(Gambar|Figure)\s*[\.\d\s:\-]+', '', txt, flags=re.IGNORECASE).strip()
                cap_title = f" {self._to_title_case(cap_clean)}" if cap_clean else ""

                p = doc_out.add_paragraph()
                p._p.set('approved_label', 'CAPTION_GAMBAR')
                p.style = doc_out.styles['Caption']
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pPr = p._p.get_or_add_pPr()
                pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))
                pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="60" w:after="180"/>'))

                r_label = p.add_run("Gambar ")
                r_label.font.name = "Times New Roman"
                r_label.font.size = Pt(12)
                r_label.font.bold = True
                r_label.font.color.rgb = RGBColor(0, 0, 0)

                self._add_seq_caption_field(p, "Gambar", current_bab if current_bab > 0 else 1, current_gambar, cap_title)

            # -------------------------------------------------------------
            # G. CAPTION TABEL
            # -------------------------------------------------------------
            elif lbl == "CAPTION_TABEL":
                current_tabel += 1
                cap_clean = re.sub(r'^(Tabel|Table)\s*[\.\d\s:\-]+', '', txt, flags=re.IGNORECASE).strip()
                cap_title = f" {self._to_title_case(cap_clean)}" if cap_clean else ""

                p = doc_out.add_paragraph()
                p._p.set('approved_label', 'CAPTION_TABEL')
                p.style = doc_out.styles['Caption']
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pPr = p._p.get_or_add_pPr()
                pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))
                pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="180" w:after="60"/>'))

                r_label = p.add_run("Tabel ")
                r_label.font.name = "Times New Roman"
                r_label.font.size = Pt(12)
                r_label.font.bold = True
                r_label.font.color.rgb = RGBColor(0, 0, 0)

                self._add_seq_caption_field(p, "Tabel", current_bab if current_bab > 0 else 1, current_tabel, cap_title)

            # -------------------------------------------------------------
            # H. DAFTAR PUSTAKA ITEM
            # -------------------------------------------------------------
            elif lbl == "DAFTAR_PUSTAKA_ITEM":
                if p_src is not None and (p_src._p.findall('.//' + qn('w:hyperlink')) or p_src._p.findall('.//' + qn('w:fldSimple'))):
                    clone = self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label='DAFTAR_PUSTAKA_ITEM')
                    clone_pPr = clone.get_or_add_pPr()
                    old_ind = clone_pPr.find(qn('w:ind'))
                    if old_ind is not None:
                        clone_pPr.remove(old_ind)
                    clone_pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="720" w:hanging="720"/>'))
                    old_sp = clone_pPr.find(qn('w:spacing'))
                    if old_sp is not None:
                        clone_pPr.remove(old_sp)
                    clone_pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="120" w:line="276" w:lineRule="auto"/>'))
                elif txt:
                    p = doc_out.add_paragraph()
                    p._p.set('approved_label', 'DAFTAR_PUSTAKA_ITEM')
                    pPr = p._p.get_or_add_pPr()
                    pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="both"/>'))
                    pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="120" w:line="276" w:lineRule="auto"/>'))
                    pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="720" w:hanging="720"/>'))
                    r = p.add_run(txt)
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
                    r.font.color.rgb = RGBColor(0, 0, 0)

            # -------------------------------------------------------------
            # I. ZERO-LOSS FALLBACK (Label tak dikenal / custom)
            # -------------------------------------------------------------
            else:
                if p_src is not None:
                    src_text = p_src.text.strip()
                    has_any_content = bool(src_text) or self._para_has_rich_content(p_src._p)
                    if has_any_content:
                        print(f"[Agent 3 - Formatter] Zero-Loss: Label '{lbl}' tidak dikenali, deep-clone paragraf #{orig_idx} apa adanya.")
                        self._deep_clone_paragraph_to_doc(p_src._p, doc_src, doc_out, label=lbl)

            # === INSERT TABLES MAPPED AFTER THIS PARAGRAPH ===
            if orig_idx in table_after_para:
                insert_cursor = doc_out.paragraphs[-1]._p if doc_out.paragraphs else None
                for tbl_elem in table_after_para[orig_idx]:
                    if tbl_elem not in inserted_tables:
                        cloned_tbl = self._deep_clone_table_to_doc(tbl_elem, doc_src, doc_out, after_elem=insert_cursor)
                        insert_cursor = cloned_tbl
                        from docx.table import Table
                        tbl_obj = Table(cloned_tbl, doc_out)
                        try:
                            tbl_text = " ".join(c.text.strip().lower() for r in tbl_obj.rows for c in r.cells)
                            if "materai" in tbl_text:
                                self._format_materai_box(tbl_obj)
                            else:
                                self._format_table_apa7(tbl_obj)
                        except Exception:
                            pass
                        inserted_tables.add(tbl_elem)

        # === ZERO-LOSS: Salin tabel sisa yang belum tersalin ===
        for src_tbl in doc_src.tables:
            if src_tbl._tbl not in inserted_tables:
                cloned_tbl = self._deep_clone_table_to_doc(src_tbl._tbl, doc_src, doc_out)
                from docx.table import Table
                tbl_obj = Table(cloned_tbl, doc_out)
                try:
                    tbl_text = " ".join(c.text.strip().lower() for r in tbl_obj.rows for c in r.cells)
                    if "materai" in tbl_text:
                        self._format_materai_box(tbl_obj)
                    else:
                        self._format_table_apa7(tbl_obj)
                except Exception:
                    pass
                inserted_tables.add(src_tbl._tbl)

        # === ZERO-LOSS: Salin elemen body non-paragraf dan non-tabel (w:sdt, dll.) ===
        src_body_children = list(doc_src.element.body)
        for child in src_body_children:
            tag = child.tag
            # Skip paragraf, tabel, dan sectPr
            if tag == qn('w:p') or tag == qn('w:tbl') or tag == qn('w:sectPr'):
                continue
            clone = copy.deepcopy(child)
            for blip in clone.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
                rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if rid and rid in doc_src.part.rels:
                    try:
                        img_blob = doc_src.part.rels[rid].target_part.blob
                        img_part = doc_out.part.package.get_or_add_image_part(io.BytesIO(img_blob))
                        new_rid = doc_out.part.relate_to(img_part, docx.opc.constants.RELATIONSHIP_TYPE.IMAGE)
                        blip.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed', new_rid)
                    except Exception:
                        pass
            sectPr = doc_out.element.body.find(qn('w:sectPr'))
            if sectPr is not None:
                sectPr.addprevious(clone)
            else:
                doc_out.element.body.append(clone)
            print(f"[Agent 3 - Formatter] Zero-Loss: Menyalin elemen body non-standar <{tag.split('}')[-1] if '}' in tag else tag}>")

        # Generate otomatis Daftar Isi, Daftar Tabel, Daftar Gambar secara dinamis
        self._generate_table_of_contents(doc_out, approved_blueprint.get("paragraphs", []), has_frontmatter=has_frontmatter)

        # Pasang sectPr Section 1 pada paragraf terakhir frontmatter/Daftar Isi sebelum Bab 1
        if sec1_sect_pr is not None:
            anchor_bab_p = None
            for p in doc_out.paragraphs:
                if p._p.get('approved_label') == "JUDUL_BAB":
                    anchor_bab_p = p
                    break
            if anchor_bab_p is not None:
                parent = anchor_bab_p._p.getparent()
                all_children = list(parent)
                bab_idx = all_children.index(anchor_bab_p._p)
                if bab_idx > 0:
                    for k in range(bab_idx - 1, -1, -1):
                        prev_elem = all_children[k]
                        if prev_elem.tag == qn('w:p'):
                            prev_pPr = prev_elem.get_or_add_pPr()
                            old_sect = prev_pPr.find(qn('w:sectPr'))
                            if old_sect is not None:
                                prev_pPr.remove(old_sect)
                            prev_pPr.append(copy.deepcopy(sec1_sect_pr))
                            break

        # Pasang root sectPr naskah untuk Section 2 (decimal, start=1, Header UEU)
        if sec2_sect_pr is not None:
            body_sect = doc_out.element.body.find(qn('w:sectPr'))
            if body_sect is not None:
                doc_out.element.body.remove(body_sect)
            doc_out.element.body.append(copy.deepcopy(sec2_sect_pr))

        # Pastikan TIDAK ADA updateFields di settings agar Word tidak memunculkan dialog security warning
        try:
            settings_elm = doc_out.settings.element
            for uf in settings_elm.findall(qn('w:updateFields')):
                settings_elm.remove(uf)
        except Exception:
            pass

        # === AUDIT: Content Integrity Check ===
        src_para_count = len(doc_src.paragraphs)
        src_table_count = len(doc_src.tables)
        out_para_count = len(doc_out.paragraphs)
        out_table_count = len(doc_out.tables)
        print(f"\n[Agent 3 - Content Audit] Sumber: {src_para_count} paragraf, {src_table_count} tabel")
        print(f"[Agent 3 - Content Audit] Output: {out_para_count} paragraf, {out_table_count} tabel")
        if out_table_count < src_table_count:
            print(f"[Agent 3 - Content Audit] ⚠️ PERINGATAN: {src_table_count - out_table_count} tabel mungkin belum tersalin!")

        out_dir = os.path.dirname(output_docx_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        doc_out.save(output_docx_path)
        print(f"[Agent 3 - Formatter Actuator] Selesai! Berkas tersimpan dengan sempurna di: {output_docx_path}")
        return output_docx_path

    def format_document(self, input_docx_path: str, approved_blueprint: Dict[str, Any], output_docx_path: str = "output/hasil_skripsi_rapi.docx", cover_data: Dict[str, str] = None) -> str:
        """
        Mengeksekusi formatting dokumen secara otonom berdasarkan Approved Blueprint.
        Menggunakan Clean Template Cloning Seed resmi UEU untuk menjamin Multilevel List
        (BAB 1, 1.1, 1.2, 2.1) 100% native Word dengan blok abu-abu solid dan integritas layout sempurna.
        """
        return self.format_via_cloned_template(input_docx_path, approved_blueprint, output_docx_path, cover_data)

    def _format_document_in_place(self, input_docx_path: str, approved_blueprint: Dict[str, Any], output_docx_path: str = "output/hasil_skripsi_rapi.docx", cover_data: Dict[str, str] = None) -> str:
        """
        Implementasi in-place lawas (fallback).
        """
        print(f"\n[Agent 3 - Formatter Actuator] Memulai operasi bedah OpenXML pada: {input_docx_path}...")
        doc = Document(input_docx_path)
        blueprint_paras = approved_blueprint["paragraphs"]

        # 0. Direct 1-to-1 binding of Agent 2 approved labels onto persistent XML nodes BEFORE any paragraphs are removed
        for idx, p in enumerate(doc.paragraphs):
            if idx < len(blueprint_paras):
                p._p.set('approved_label', blueprint_paras[idx]["approved_label"])
                p._p.set('has_num', 'true' if blueprint_paras[idx]["metadata"]["has_num"] else 'false')
                p._p.set('is_subsub', 'true' if blueprint_paras[idx]["metadata"].get("is_subsub") else 'false')
                p._p.set('is_formula', 'true' if blueprint_paras[idx]["metadata"].get("is_formula") else 'false')
                target_bab = blueprint_paras[idx]["metadata"].get("target_caption_bab")
                if target_bab:
                    p._p.set('target_caption_bab', str(target_bab))
                p._p.set('orig_style', str(blueprint_paras[idx]["metadata"].get("style", p.style.name)))
            else:
                p._p.set('approved_label', "BODY_PARAGRAPH")
                p._p.set('has_num', 'false')
                p._p.set('is_subsub', 'false')
                p._p.set('is_formula', 'false')
                p._p.set('orig_style', p.style.name)

        # 1. Bersihkan style bawaan template dari cacat indentasi
        self._sanitize_styles(doc)

        # Inisialisasi Multilevel List Heading (BAB 1, 1.1, 1.1.1)
        heading_num_id = self._ensure_heading_multilevel_list(doc)

        # 2. Proteksi Halaman Cover asli dokumen 100% tanpa diubah
        self._protect_original_cover(doc, blueprint_paras)

        # 3. Enforce Standar Ukuran Kertas A4 Portrait (21.0 x 29.7 cm) & Margin Baku (4 3 3 3)
        self._enforce_a4_and_margins(doc)

        # Cari paragraf pertama BAB I untuk pemisah Section
        first_bab_idx = -1
        for p_info in blueprint_paras:
            if p_info["approved_label"] == "JUDUL_BAB":
                first_bab_idx = p_info["para_id"]
                break

        # 4. Setup Dual Page Numbering (Romawi Depan & Angka Latin Isi)
        self._setup_dual_page_numbering(doc, first_bab_idx)

        # 5. Header bersih tanpa injeksi teks kampus lain
        for s_idx, section in enumerate(doc.sections):
            header = section.header
            header.is_linked_to_previous = False
            if header.paragraphs:
                hp = header.paragraphs[0]
                hp.text = ""

        def apply_run_font(p_elem, font_name="Times New Roman", size_pt=12, bold=False, italic=False):
            for run in p_elem.runs:
                run.font.name = font_name
                run.font.size = Pt(size_pt)
                run.font.bold = bold
                run.font.italic = italic
                run.font.color.rgb = RGBColor(0, 0, 0)

        paras_to_remove = []

        # 6. Format Setiap Paragraf Berdasarkan Approved Blueprint (Direct Binding dari Agen 2)
        current_bab_num = 0
        current_sub_num = 0
        current_subsub_num = 0
        current_gambar_num = 0
        current_tabel_num = 0
        current_context = ""
        in_abstrak = False
        in_abstract = False
        in_kata_pengantar = False
        is_under_heading3 = False
        romawi_map_inv = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}

        for p_idx, p in enumerate(doc.paragraphs):
            item_label = p._p.get('approved_label') or "BODY_PARAGRAPH"
            has_num = p._p.get('has_num') == 'true'

            if item_label in ["COVER_PARAGRAPH", "TOC_PARAGRAPH"]:
                continue

            text = p.text.strip()
            upper_text = text.upper()
            low_text = text.lower()
            has_image = bool(p._p.findall('.//' + qn('w:drawing')) or p._p.findall('.//' + qn('w:pict')))

            # Bersihkan komentar/petunjuk template
            if not has_image and self._is_template_comment(text):
                paras_to_remove.append(p._p)
                continue

            # Tangani baris kosong:
            if not has_image and not text:
                # Pertahankan baris kosong untuk ruang tanda tangan fisik di halaman pernyataan, pengesahan, & publikasi
                if current_bab_num == 0 and current_context in ['pernyataan', 'pengesahan', 'penguji', 'publikasi']:
                    self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.line_spacing = 1.0
                    continue
                else:
                    paras_to_remove.append(p._p)
                    continue

            # Jika paragraf memuat gambar (drawing/pict), format rata tengah proporsional dan pertahankan 100%
            if has_image:
                self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.line_spacing = 1.0
                pPr = p._p.get_or_add_pPr()
                numPr = pPr.find(qn('w:numPr'))
                if numPr is not None:
                    pPr.remove(numPr)
                jc_el = pPr.find(qn('w:jc'))
                if jc_el is not None:
                    pPr.remove(jc_el)
                pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))
                continue

            # Update konteks halaman dokumen untuk penyesuaian tab metadata & tipografi
            if 'kata pengantar' in low_text or 'prakata' in low_text:
                in_kata_pengantar = True
                in_abstrak = False
                in_abstract = False
                current_context = 'kata_pengantar'
            elif 'pernyataan' in low_text or 'keaslian' in low_text:
                in_kata_pengantar = False
                current_context = 'pernyataan'
            elif 'pengesahan' in low_text:
                in_kata_pengantar = False
                current_context = 'pengesahan'
            elif 'tim penguji' in low_text:
                in_kata_pengantar = False
                current_context = 'penguji'
            elif 'publikasi' in low_text or 'bebas royalti' in low_text:
                in_kata_pengantar = False
                current_context = 'publikasi'
            elif low_text == 'abstrak' or (low_text.startswith('abstrak') and len(low_text) < 15):
                in_kata_pengantar = False
                in_abstrak = True
                in_abstract = False
                current_context = 'abstrak_id'
            elif low_text == 'abstract' or (low_text.startswith('abstract') and len(low_text) < 15):
                in_kata_pengantar = False
                in_abstract = True
                in_abstrak = False
                current_context = 'abstract_en'
            elif 'daftar isi' in low_text or current_bab_num > 0:
                in_kata_pengantar = False
                in_abstrak = False
                in_abstract = False

            # Prioritas Metadata: Rapikan format titik dua (Nama, NIM, Tim Penguji, Tanggal, dll.) dengan Tab Stop presisi UEU
            if current_bab_num == 0:
                ctx = 'abstract_en' if in_abstract else ('abstrak_id' if in_abstrak else current_context)
                if self._align_metadata_field(p, text, ctx):
                    continue

            if item_label in ["COVER_METADATA", "LAINNYA"]:
                continue

            # --- A. FORMAT JUDUL BAB (Heading 1 + BAB I/II/III + Outline Level 0) ---
            if item_label == "JUDUL_BAB":
                in_abstrak = False
                in_abstract = False
                is_under_heading3 = False
                current_bab_num += 1
                current_sub_num = 0
                current_subsub_num = 0
                current_gambar_num = 0
                current_tabel_num = 0

                roman_map = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X'}
                bab_roman = roman_map.get(current_bab_num, str(current_bab_num))

                # Hapus prefix BAB lama yang mungkin dobel/rusak
                clean_t = re.sub(r'^(BAB\s*(\d+|[IVXLCDM]+)[\s:\.\-]*)+', '', text, flags=re.IGNORECASE).strip()
                clean_t = clean_t.strip('\n').strip()

                # Jika pengguna memisahkan 'BAB 1' dan 'PENDAHULUAN' di dua paragraf berbeda
                if not clean_t and p_idx + 1 < len(doc.paragraphs):
                    next_p = doc.paragraphs[p_idx + 1]
                    next_txt = next_p.text.strip()
                    if next_txt and len(next_txt.split()) <= 10:
                        clean_t = next_txt
                        paras_to_remove.append(next_p._p)

                # Format Persis Template Acuan UEU:
                # Baris 1: BAB 1 (Center murni)
                # Baris 2: PENDAHULUAN (Center murni)
                p.text = ""
                roman_bab = self._to_roman(current_bab_num)
                r_bab = p.add_run(f"BAB {roman_bab}\n")
                r_bab.font.name = "Times New Roman"
                r_bab.font.size = Pt(14)
                r_bab.font.bold = True
                r_bab.font.color.rgb = RGBColor(0, 0, 0)

                r_txt = p.add_run(clean_t.upper())
                r_txt.font.name = "Times New Roman"
                r_txt.font.size = Pt(14)
                r_txt.font.bold = True
                r_txt.font.color.rgb = RGBColor(0, 0, 0)

                try:
                    p.style = doc.styles['Heading 1']
                except Exception:
                    pass

                self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(12)
                p.paragraph_format.page_break_before = True
                p.paragraph_format.keep_with_next = True

                pPr = p._p.get_or_add_pPr()

                # Hapus numPr agar TIDAK ADA offset bullet list di Word (Center Murni)
                numPr = pPr.find(qn('w:numPr'))
                if numPr is not None:
                    pPr.remove(numPr)

                if pPr.find(qn('w:pageBreakBefore')) is None:
                    pPr.append(parse_xml(r'<w:pageBreakBefore xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))

                if pPr.find(qn('w:keepNext')) is None:
                    pPr.append(parse_xml(r'<w:keepNext xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))

                # Heading 1 CENTERED MUTLAK tanpa offset
                jc_elm = pPr.find(qn('w:jc'))
                if jc_elm is not None:
                    pPr.remove(jc_elm)
                pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="center"/>'))

                ind_elm = pPr.find(qn('w:ind'))
                if ind_elm is not None:
                    pPr.remove(ind_elm)
                pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="0" w:right="0" w:firstLine="0" w:hanging="0"/>'))

                existing_lvl = pPr.find(qn('w:outlineLvl'))
                if existing_lvl is not None:
                    pPr.remove(existing_lvl)
                pPr.append(parse_xml(r'<w:outlineLvl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="0"/>'))

                existing_sp = pPr.find(qn('w:spacing'))
                if existing_sp is not None:
                    pPr.remove(existing_sp)
                pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="240" w:line="240" w:lineRule="auto" w:beforeAutospacing="0" w:afterAutospacing="0"/>'))

            # --- B. FORMAT SUB-BAB (Heading 2 / Heading 3 + Nomor Eksplisit 1.1 + Tab 1.27 cm) ---
            elif item_label == "SUB_BAB":
                orig_style = p._p.get('orig_style') or p.style.name
                is_subsub = bool(
                    p._p.get('is_subsub') == 'true' or
                    re.match(r'^\d+\.\d+\.\d+', text.strip()) or
                    'Heading 3' in orig_style or
                    'Heading3' in orig_style or
                    p.style.name in ['Heading 3', 'Heading3']
                )
                is_under_heading3 = is_subsub
                style_name = 'Heading 3' if is_subsub else 'Heading 2'
                lvl_val = '2' if is_subsub else '1'

                # Hapus nomor numerik lama yang menempel di awal teks (misal: "1.1 ", "1.2.1 ", "A. ")
                clean_sub = re.sub(r'^((\d+|[A-Za-z])\.)+(\d+)*\s*', '', text).strip()
                clean_sub = re.sub(r'^\d+(\.\d+)*\s*', '', clean_sub).strip()
                clean_title = self._to_title_case(clean_sub)

                if current_bab_num == 0:
                    current_bab_num = 1

                if is_subsub:
                    current_subsub_num += 1
                    if current_sub_num == 0:
                        current_sub_num = 1
                    num_prefix = f"{current_bab_num}.{current_sub_num}.{current_subsub_num}"
                    tab_pos = "720" # 1.27 cm (sejajar alinea alinea paragraf)
                else:
                    current_sub_num += 1
                    current_subsub_num = 0
                    num_prefix = f"{current_bab_num}.{current_sub_num}"
                    tab_pos = "720" # 1.27 cm (hanging indent Heading 2 UEU)

                # Format Sub-Bab: Pastikan nomor bab/sub-bab (1.1, 1.2, 2.1) selalu muncul jelas dan rapi
                p.text = ""
                r_num = p.add_run(f"{num_prefix}\t")
                r_num.font.name = "Times New Roman"
                r_num.font.size = Pt(12)
                r_num.font.bold = True
                r_num.font.color.rgb = RGBColor(0, 0, 0)

                r_txt = p.add_run(clean_title)
                r_txt.font.name = "Times New Roman"
                r_txt.font.size = Pt(12)
                r_txt.font.bold = True
                r_txt.font.color.rgb = RGBColor(0, 0, 0)

                try:
                    p.style = doc.styles[style_name]
                except Exception:
                    pass

                self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_before = Pt(12 if not is_subsub else 8)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.keep_with_next = True

                pPr = p._p.get_or_add_pPr()

                # Hapus numPr agar tidak konflik dengan nomor eksplisit teks dan tidak hilang di Word
                numPr = pPr.find(qn('w:numPr'))
                if numPr is not None:
                    pPr.remove(numPr)

                if pPr.find(qn('w:keepNext')) is None:
                    pPr.append(parse_xml(r'<w:keepNext xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))

                # Tab stop pada tab_pos (576 dxa / 1.0 cm untuk Heading 2, 720 dxa / 1.27 cm untuk Heading 3)
                tabs_elm = pPr.find(qn('w:tabs'))
                if tabs_elm is not None:
                    pPr.remove(tabs_elm)
                pPr.append(parse_xml(f'<w:tabs xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:tab w:val="left" w:pos="{tab_pos}"/></w:tabs>'))

                existing_ind = pPr.find(qn('w:ind'))
                if existing_ind is not None:
                    pPr.remove(existing_ind)
                # Hanging indent: nomor di margin kiri (0.0 cm), teks judul mulai di tab_pos
                pPr.append(parse_xml(f'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="{tab_pos}" w:hanging="{tab_pos}"/>'))

                existing_lvl = pPr.find(qn('w:outlineLvl'))
                if existing_lvl is not None:
                    pPr.remove(existing_lvl)
                pPr.append(parse_xml(f'<w:outlineLvl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="{lvl_val}"/>'))

                # Spasi Heading: Before 12/8 pt, After 6 pt, Line Single (240 dxa)
                existing_sp = pPr.find(qn('w:spacing'))
                if existing_sp is not None:
                    pPr.remove(existing_sp)
                pPr.append(parse_xml(f'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="{"240" if not is_subsub else "160"}" w:after="120" w:line="240" w:lineRule="auto" w:beforeAutospacing="0" w:afterAutospacing="0"/>'))

                apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=True, italic=False)
                for r in p.runs:
                    r.font.color.rgb = RGBColor(0, 0, 0)

            # --- C. FORMAT PARAGRAF GAMBAR, PARAGRAF ISI BIASA & DAFTAR LIST ---
            elif item_label == "BODY_PARAGRAPH":
                pPr = p._p.get_or_add_pPr()
                has_numPr = pPr.find(qn('w:numPr')) is not None
                has_image = bool(p._p.findall('.//' + qn('w:drawing')) or p._p.findall('.//' + qn('w:pict')))

                if in_abstract and not has_image and not has_numPr:
                    # Paragraf tubuh di ABSTRACT bahasa Inggris: 100% Italic, 12 pt TNR, spasi 1.0, Not Bold
                    self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=1.0, keep_numPr=False)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(6)
                    apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=True)
                elif in_abstrak and not has_image and not has_numPr:
                    # Paragraf tubuh di ABSTRAK bahasa Indonesia: Tegak, 12 pt TNR, spasi 1.0, Not Bold
                    self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=1.0, keep_numPr=False)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(6)
                    apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=False)
                elif has_image:
                    # Gambar harus rata tengah (Center) tanpa inden, jarak sebelum/sesudah proporsional
                    self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before = Pt(6)
                    p.paragraph_format.space_after = Pt(6)
                    p.paragraph_format.line_spacing = 1.0
                elif has_num or has_numPr:
                    # Pertahankan numPr bawaan untuk list nomor/bullet dengan hanging indent presisi
                    self._reset_paragraph_indents(p, left_cm=1.75, right_cm=0.0, first_line_cm=-0.75, keep_numPr=True)
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(6)
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.line_spacing = 1.15 if (in_kata_pengantar or current_bab_num > 0) else 1.0
                    apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=False)
                elif current_bab_num == 0 and not in_kata_pengantar:
                    # Bukan Kata Pengantar dan Bukan Isi Bab (Halaman Pengesahan, Pernyataan Keaslian, Persetujuan Publikasi):
                    # Rata kiri (LEFT), tanpa inden paragraf (first_line_indent = 0, left = 0), spasi tunggal (line_spacing = 1.0)
                    self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(6)
                    p.paragraph_format.line_spacing = 1.0
                    apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=False)
                    self._italicize_foreign_terms(p)
                else:
                    # Cek jenis paragraf khusus dalam Bab:
                    is_numbered_list = bool(re.match(r'^(\d+|[a-zA-Z])[\.\)]\s*', text))
                    is_hypo = bool(re.match(r'^(HA?\d*|H0|H\d+)\s*[:\.]', text, re.IGNORECASE))
                    is_formula_legend = bool(re.match(r'^(Keterangan|Dimana|Di mana|Notasi)\s*[:=]?', text, re.IGNORECASE))
                    is_variable_item = bool(re.match(r'^[a-zA-Zα-ωΑ-Ω0-9_]{1,3}\s*[:=]\s*', text)) and not is_hypo
                    is_source_note = bool(re.match(r'^(Sumber|Source|Catatan|Note)\s*[:=]', text, re.IGNORECASE))
                    is_formula = bool(
                        re.search(r'\(\d+\.\d+\)\s*$', text) or
                        (any(op in text for op in [' = ', ' / ', ' * ', ' + ']) and re.search(r'\(\d+(\.\d+)?\)', text)) or
                        any(k in text for k in ['Accuracy =', 'Precision =', 'Recall =', 'F1-Score =', 'F1 =', 'MAE =', 'MSE =', 'RMSE =']) or
                        bool(p._p.findall('.//' + qn('m:oMath')))
                    )
                    is_code_snippet = bool(
                        re.match(r'^(def |import |from |class |public |void |const |let |var |//|#include|<html)', text) or
                        any(k in text for k in ['return ', 'print(', 'console.log']) or
                        (p.runs and p.runs[0].font.name in ['Consolas', 'Courier New', 'Monospace'])
                    )

                    if is_formula:
                        eq_match = re.search(r'^(.*?)\s*(\(\d+\.\d+\))\s*$', text)
                        if eq_match:
                            eq_body = eq_match.group(1).strip()
                            eq_num = eq_match.group(2).strip()

                            self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                            p.paragraph_format.space_before = Pt(6)
                            p.paragraph_format.space_after = Pt(6)
                            p.paragraph_format.line_spacing = 1.15
                            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                            pPr = p._p.get_or_add_pPr()
                            existing_tabs = pPr.find(qn('w:tabs'))
                            if existing_tabs is not None:
                                pPr.remove(existing_tabs)
                            # Center tab di 3969 dxa (7.0 cm) & Right tab di 7937 dxa (14.0 cm / tepi margin kanan)
                            pPr.append(parse_xml(r'''
                                <w:tabs xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                                    <w:tab w:val="center" w:pos="3969"/>
                                    <w:tab w:val="right" w:pos="7937"/>
                                </w:tabs>
                            '''))

                            p.text = ""
                            r_tab1 = p.add_run("\t")
                            r_body = p.add_run(eq_body)
                            r_body.font.name = "Times New Roman"
                            r_body.font.size = Pt(12)
                            r_body.font.italic = True
                            r_body.font.color.rgb = RGBColor(0, 0, 0)

                            r_tab2 = p.add_run("\t")
                            r_num = p.add_run(eq_num)
                            r_num.font.name = "Times New Roman"
                            r_num.font.size = Pt(12)
                            r_num.font.bold = False
                            r_num.font.italic = False
                            r_num.font.color.rgb = RGBColor(0, 0, 0)
                        else:
                            self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            p.paragraph_format.space_before = Pt(6)
                            p.paragraph_format.space_after = Pt(6)
                            p.paragraph_format.line_spacing = 1.15
                            apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=True)

                    elif is_code_snippet:
                        self._reset_paragraph_indents(p, left_cm=1.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(2)
                        p.paragraph_format.line_spacing = 1.0
                        apply_run_font(p, font_name="Consolas", size_pt=10, bold=False, italic=False)

                    elif is_hypo:
                        # Hipotesis Penelitian (HA1:, H1:):
                        self._reset_paragraph_indents(p, left_cm=1.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(6)
                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        p.paragraph_format.line_spacing = 1.15
                        apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=False)
                        if p.runs:
                            p.runs[0].font.bold = True
                    elif is_formula_legend:
                        # Judul keterangan rumus ('Keterangan:')
                        self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(6)
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        p.paragraph_format.line_spacing = 1.15
                        p.paragraph_format.keep_with_next = True
                        apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=False)
                    elif is_variable_item:
                        # Item variabel rumus ('n : jumlah sampel')
                        self._reset_paragraph_indents(p, left_cm=1.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(3)
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        p.paragraph_format.line_spacing = 1.15
                        apply_run_font(p, font_name="Times New Roman", size_pt=11, bold=False, italic=False)
                    elif is_source_note:
                        # Sumber di bawah tabel atau gambar ('Sumber: ...')
                        self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0, keep_numPr=False)
                        p.paragraph_format.space_before = Pt(3)
                        p.paragraph_format.space_after = Pt(6)
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        p.paragraph_format.line_spacing = 1.0
                        apply_run_font(p, font_name="Times New Roman", size_pt=10, bold=False, italic=False)
                    elif is_numbered_list:
                        # Rincian butir penomoran (1. ..., a. ..., 1) ...)
                        if re.match(r'^(\d+|[a-zA-Z])\.(\S)', p.text):
                            p.text = re.sub(r'^(\d+|[a-zA-Z])\.(\S)', r'\1. \2', p.text)
                        
                        # Sesuai acuan UEU & screenshot user: Nomor di margin kiri (0 cm), teks menggantung rapi sejajar alinea (1.27 cm / 720 dxa)
                        self._reset_paragraph_indents(p, left_cm=1.27, right_cm=0.0, first_line_cm=-1.27, keep_numPr=False)
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(6)
                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        p.paragraph_format.line_spacing = 1.15
                        if len(p.text.split()) <= 12 or p.text.strip().endswith(':'):
                            p.paragraph_format.keep_with_next = True
                        apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=False)
                        if re.match(r'^(\d+|[a-zA-Z])[\.\)]\s+[A-Z\s\(\)]+$', p.text.strip()) or re.match(r'^[a-z]\.\s+[A-Z]', p.text.strip()):
                            if p.runs:
                                 p.runs[0].font.bold = True
                        
                        pPr = p._p.get_or_add_pPr()
                        numPr = pPr.find(qn('w:numPr'))
                        if numPr is not None:
                            pPr.remove(numPr)
                        existing_ind = pPr.find(qn('w:ind'))
                        if existing_ind is not None:
                            pPr.remove(existing_ind)
                        pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="720" w:hanging="720"/>'))
                    else:
                        # Paragraf tubuh standar (Kata Pengantar dan Isi Bab 1-N):
                        # Alinea baris pertama (first-line indent) TEPAT SEJAJAR VERTIKAL 1.27 cm (720 dxa) dengan judul Sub-bab
                        self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=1.27, keep_numPr=False)
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(6)
                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        p.paragraph_format.line_spacing = 1.15
                        
                        try:
                            p.style = doc.styles['Normal']
                        except Exception:
                            pass

                        pPr = p._p.get_or_add_pPr()
                        numPr = pPr.find(qn('w:numPr'))
                        if numPr is not None:
                            pPr.remove(numPr)

                        existing_sp = pPr.find(qn('w:spacing'))
                        if existing_sp is not None:
                            pPr.remove(existing_sp)
                        pPr.append(parse_xml(r'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="120" w:line="276" w:lineRule="auto" w:beforeAutospacing="0" w:afterAutospacing="0"/>'))

                        existing_ind = pPr.find(qn('w:ind'))
                        if existing_ind is not None:
                            pPr.remove(existing_ind)
                        pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="0" w:right="0" w:firstLine="720"/>'))

                        existing_jc = pPr.find(qn('w:jc'))
                        if existing_jc is not None:
                            pPr.remove(existing_jc)
                        pPr.append(parse_xml(r'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="both"/>'))

                        apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False, italic=False)
                        self._italicize_foreign_terms(p)


            # --- D. FORMAT CAPTION GAMBAR & TABEL ---
            elif item_label in ["CAPTION_GAMBAR", "CAPTION_TABEL"]:
                self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
                p.paragraph_format.line_spacing = 1.0

                active_bab = current_bab_num if current_bab_num > 0 else 1
                raw_cap = re.sub(r'\s+', ' ', p.text).strip()

                if item_label == "CAPTION_GAMBAR":
                    current_gambar_num += 1
                    p.paragraph_format.space_before = Pt(6)
                    p.paragraph_format.space_after = Pt(12)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    jc_val = "center"
                    prefix_word = "Gambar"
                    seq_val = current_gambar_num

                    clean_title = re.sub(r'^(Gambar|Figure)\s*([\d\.\-]+\s*[:\.]?|\.\s*[:\.]?|[:\.]\s*)', '', raw_cap, flags=re.IGNORECASE).strip()
                    if not clean_title:
                        clean_title = raw_cap

                    # Garansi Posisi Fisik: Gambar selalu di BAWAH gambar/drawing
                    if p_idx + 1 < len(doc.paragraphs):
                        next_p = doc.paragraphs[p_idx + 1]
                        if bool(next_p._p.findall('.//' + qn('w:drawing')) or next_p._p.findall('.//' + qn('w:pict'))):
                            next_p._p.addnext(p._p)

                else:  # CAPTION_TABEL
                    current_tabel_num += 1
                    p.paragraph_format.space_before = Pt(12)
                    p.paragraph_format.space_after = Pt(6)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    jc_val = "center"
                    prefix_word = "Tabel"
                    seq_val = current_tabel_num

                    clean_title = re.sub(r'^(Tabel|Table)\s*([\d\.\-]+\s*[:\.]?|\.\s*[:\.]?|[:\.]\s*)', '', raw_cap, flags=re.IGNORECASE).strip()
                    if not clean_title:
                        clean_title = raw_cap

                    # Garansi Posisi Fisik: Tabel selalu di ATAS tabel
                    prev_elm = p._p.getprevious()
                    if prev_elm is not None and prev_elm.tag.endswith('tbl'):
                        prev_elm.addprevious(p._p)

                # Bersihkan isi teks lama (HANYA run, field, hyperlink, proofErr - JANGAN hapus pPr atau bookmark!)
                run_tags = {qn('w:r'), qn('w:fldSimple'), qn('w:hyperlink'), qn('w:proofErr')}
                for child in list(p._p):
                    if child.tag in run_tags:
                        p._p.remove(child)

                # Pastikan pPr ada di posisi pertama
                pPr = p._p.get_or_add_pPr()
                if p._p.index(pPr) != 0:
                    p._p.remove(pPr)
                    p._p.insert(0, pPr)

                existing_ind = pPr.find(qn('w:ind'))
                if existing_ind is not None:
                    pPr.remove(existing_ind)
                pPr.append(parse_xml(r'<w:ind xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:left="0" w:right="0" w:firstLine="0" w:hanging="0"/>'))

                jc_elm = pPr.find(qn('w:jc'))
                if jc_elm is not None:
                    pPr.remove(jc_elm)
                pPr.append(parse_xml(f'<w:jc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="{jc_val}"/>'))

                existing_sp = pPr.find(qn('w:spacing'))
                if existing_sp is not None:
                    pPr.remove(existing_sp)
                sp_before = "120" if item_label == "CAPTION_GAMBAR" else "240"
                sp_after = "240" if item_label == "CAPTION_GAMBAR" else "120"
                pPr.append(parse_xml(f'<w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="{sp_before}" w:after="{sp_after}" w:line="240" w:lineRule="auto"/>'))

                # Format Dynamic Field Baku Word & UEU (dengan shading field otomatis seperti Gambar 2):
                p.text = ""
                # 1. Prefix ("Gambar " / "Tabel ")
                r_pre = p.add_run(f"{prefix_word} ")
                r_pre.font.name = "Times New Roman"
                r_pre.font.size = Pt(12)
                r_pre.font.bold = True
                r_pre.font.color.rgb = RGBColor(0, 0, 0)

                # 2. Dynamic Field STYLEREF 1 \s (Nomor Bab aktif otomatis Word)
                fld_bab = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr=" STYLEREF 1 \\s "><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/><w:b/><w:color w:val="000000"/><w:noProof/></w:rPr><w:t>{active_bab}</w:t></w:r></w:fldSimple>')
                p._p.append(fld_bab)

                # 3. Separator Titik (".")
                r_dot = p.add_run(".")
                r_dot.font.name = "Times New Roman"
                r_dot.font.size = Pt(12)
                r_dot.font.bold = True
                r_dot.font.color.rgb = RGBColor(0, 0, 0)

                # 4. Dynamic Field SEQ (Nomor Urut Gambar/Tabel otomatis Word per Bab)
                fld_seq = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr=" SEQ {prefix_word} \\* ARABIC \\s 1 "><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/><w:b/><w:color w:val="000000"/><w:noProof/></w:rPr><w:t>{seq_val}</w:t></w:r></w:fldSimple>')
                p._p.append(fld_seq)

                # 5. Judul Caption
                r_title = p.add_run(f" {clean_title}")
                r_title.font.name = "Times New Roman"
                r_title.font.size = Pt(12)
                r_title.font.bold = False
                r_title.font.color.rgb = RGBColor(0, 0, 0)

            # --- E. FORMAT DAFTAR PUSTAKA ---
            elif item_label == "DAFTAR_PUSTAKA_ITEM":
                self._reset_paragraph_indents(p, left_cm=1.27, right_cm=0.0, first_line_cm=-1.27)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(6)
                apply_run_font(p, font_name="Times New Roman", size_pt=12, bold=False)

            # --- F. FORMAT JUDUL AWAL (Frontmatter: Abstrak, Pengesahan, Persetujuan Publikasi, Daftar Isi) ---
            # --- F. FORMAT JUDUL AWAL (Frontmatter: Abstrak, Pengesahan, Persetujuan Publikasi, Daftar Isi) ---
            elif item_label == "FRONTMATTER_TITLE":
                # Jika sudah ditandai untuk dihapus karena digabung ke judul sebelumnya, lewati
                if p._p in paras_to_remove:
                    continue

                is_persetujuan_main = any(k in upper_text for k in ["PERSETUJUAN", "PUBLIKASI"])
                is_sub_akademis = ("UNTUK KEPENTINGAN AKADEMIS" in upper_text) and not is_persetujuan_main

                # Jika menemukan baris subordinat yang berdiri sendiri, jadikan Normal style (BUKAN Heading 1) tanpa outlineLvl
                if is_sub_akademis:
                    try:
                        p.style = doc.styles['Normal']
                    except Exception:
                        pass
                    self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.line_spacing = 1.15
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(12)
                    p.paragraph_format.page_break_before = False
                    pPr = p._p.get_or_add_pPr()
                    numPr = pPr.find(qn('w:numPr'))
                    if numPr is not None:
                        pPr.remove(numPr)
                    existing_lvl = pPr.find(qn('w:outlineLvl'))
                    if existing_lvl is not None:
                        pPr.remove(existing_lvl)
                    apply_run_font(p, font_name="Times New Roman", size_pt=14, bold=True)
                    continue

                # Pastikan tidak ada "BAB" atau nomor tidak sengaja menempel
                clean_fm = re.sub(r'^(BAB\s*(\d+|[IVXLCDM]+)[\s:\.\-]*)+', '', text, flags=re.IGNORECASE).strip()
                clean_fm = re.sub(r'^\d+(\.\d+)*\s*', '', clean_fm).strip().upper()

                # Cek jika judul frontmatter diikuti oleh sub-judul subordinat (misal: "UNTUK KEPENTINGAN AKADEMIS" atau "TUGAS AKHIR")
                # Gabungkan menjadi 1 kesatuan dalam 1 paragraf Heading 1 agar di Word hanya ada 1 Heading & 1 tanda panah lipat (collapse arrow)
                if p_idx + 1 < len(doc.paragraphs):
                    next_p = doc.paragraphs[p_idx + 1]
                    next_txt = next_p.text.strip().upper()
                    if is_persetujuan_main and "UNTUK KEPENTINGAN AKADEMIS" in next_txt:
                        clean_fm = f"{clean_fm}\n{next_txt}"
                        paras_to_remove.append(next_p._p)
                    elif ("PENGESAHAN" in clean_fm) and (next_txt in ["TUGAS AKHIR", "SKRIPSI"]):
                        clean_fm = f"{clean_fm}\n{next_txt}"
                        paras_to_remove.append(next_p._p)

                p.text = clean_fm

                try:
                    p.style = doc.styles['Heading 1']
                except Exception:
                    pass

                self._reset_paragraph_indents(p, left_cm=0.0, right_cm=0.0, first_line_cm=0.0)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_before = Pt(24)
                p.paragraph_format.space_after = Pt(12)
                p.paragraph_format.page_break_before = True

                pPr = p._p.get_or_add_pPr()
                if pPr.find(qn('w:pageBreakBefore')) is None:
                    pPr.append(parse_xml(r'<w:pageBreakBefore xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'))
                numPr = pPr.find(qn('w:numPr'))
                if numPr is not None:
                    pPr.remove(numPr)
                existing_lvl = pPr.find(qn('w:outlineLvl'))
                if existing_lvl is not None:
                    pPr.remove(existing_lvl)
                pPr.append(parse_xml(r'<w:outlineLvl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="0"/>'))

                is_abstract_en = "ABSTRACT" in clean_fm
                if is_abstract_en:
                    apply_run_font(p, font_name="Times New Roman", size_pt=14, bold=True, italic=True)
                else:
                    apply_run_font(p, font_name="Times New Roman", size_pt=14, bold=True, italic=False)
                for r in p.runs:
                    r.text = r.text.upper()

        # 7. Bersihkan Komentar Template (dengan proteksi mutlak gambar dan section break)
        if paras_to_remove:
            paras_to_remove = [
                p_elem for p_elem in paras_to_remove
                if not (p_elem.findall('.//' + qn('w:drawing')) or 
                        p_elem.findall('.//' + qn('w:pict')) or 
                        p_elem.xpath('.//w:sectPr') or 
                        p_elem.get('is_section_break_carrier') == 'true')
            ]
            print(f"[Agent 3 - Formatter Actuator] Membersihkan {len(paras_to_remove)} baris komentar/petunjuk template...")
            for p_elem in paras_to_remove:
                parent = p_elem.getparent()
                if parent is not None:
                    parent.remove(p_elem)

        # 8. Otomatisasi Daftar Isi, Daftar Tabel, Daftar Gambar
        self._generate_table_of_contents(doc, blueprint_paras)

        # 9. Format Seluruh Tabel (Standar APA 7 atau Kotak Materai)
        print(f"[Agent 3 - Formatter Actuator] Menerapkan format standar pada {len(doc.tables)} tabel...")
        for tbl in doc.tables:
            tbl_text = " ".join(c.text.strip().lower() for r in tbl.rows for c in r.cells)
            if "materai" in tbl_text:
                self._format_materai_box(tbl)
            else:
                self._format_table_apa7(tbl)

        # 9.5. Setup Dual Page Numbering (Romawi Depan & Angka Latin Isi)
        self._setup_dual_page_numbering(doc, first_bab_idx)

        # 10. Enforce Mutlak Ukuran Kertas A4 Portrait (21.0 x 29.7 cm) & Margin Baku UEU (4 3 3 3) pada Seluruh Section
        print(f"[Agent 3 - Formatter Actuator] Menerapkan ukuran kertas A4 Portrait dan margin baku UEU (Kiri 4 cm, Atas 3 cm, Kanan 3 cm, Bawah 3 cm) pada seluruh {len(doc.sections)} section...")
        self._enforce_a4_and_margins(doc)

        # 11. Bersihkan atribut sementara dan Simpan Dokumen Rapi
        for p in doc.paragraphs:
            p._p.attrib.pop('approved_label', None)
            p._p.attrib.pop('has_num', None)

        os.makedirs(os.path.dirname(output_docx_path), exist_ok=True)
        doc.save(output_docx_path)
        print(f"[Agent 3 - Formatter Actuator] Selesai! Berkas rapi tersimpan di: {output_docx_path}")
        return output_docx_path
