"""Bersihkan data/template_clean_ueu.docx (Sesi 30).

1. Urutkan anak w:pPr (styles.xml, document.xml) dan w:lvl (numbering.xml) sesuai skema OOXML; Word diam-diam
   membuang elemen yang urutannya salah.
2. w:suff w:val="none" -> "nothing" (nilai "none" tidak sah).
3. Hapus style sisa LibreOffice yang tidak dipakai dan tidak dirujuk style lain
   (ListLabel 1-20, Index, Index Link, Heading, Default, Normal2).
4. Samakan style TOC 1-3 dan table of figures dengan format daftar Asdoku
   (TNR 12, spasi 1,15, 2 pt sebelum/sesudah, indentasi 0,5 cm per tingkat, tab titik di 14 cm).

Penggunaan: python3 tools/clean_template.py data/template_clean_ueu.docx
"""
import re
import shutil
import sys
import zipfile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
q = lambda tag: f"{{{W}}}{tag}"

PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
             "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
             "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
             "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr",
             "sectPr", "pPrChange"]
LVL_ORDER = ["start", "numFmt", "lvlRestart", "pStyle", "isLgl", "suff", "lvlText", "lvlPicBulletId",
             "legacy", "lvlJc", "pPr", "rPr"]
LEGACY_STYLE_RE = re.compile(r"^(ListLabel\d+|Index|IndexLink|Heading|Default|Normal2)$")
LIST_STYLES = {"TOC1": 0, "TOC2": 1, "TOC3": 2, "TableofFigures": 0}
RIGHT_TAB = "7937"  # 14 cm = lebar area teks (21 - 4 - 3)


def reorder(root, tag, order):
    changed = 0
    for el in root.iter(q(tag)):
        kids = list(el)
        key = lambda c: order.index(etree.QName(c).localname) if etree.QName(c).localname in order else len(order)
        new = sorted(kids, key=key)
        if new != kids:
            changed += 1
            for c in kids:
                el.remove(c)
            el.extend(new)
    return changed


def referenced_style_ids(zf):
    used = set()
    for name in zf.namelist():
        if name.endswith(".xml") and name != "word/styles.xml":
            used.update(m.decode() for m in re.findall(rb'w:(?:pStyle|rStyle|tblStyle) w:val="([^"]+)"', zf.read(name)))
    return used


def set_list_style(style, level):
    ppr = style.find(q("pPr"))
    if ppr is None:
        ppr = etree.SubElement(style, q("pPr"))
    for child in list(ppr):
        ppr.remove(child)
    tabs = etree.SubElement(ppr, q("tabs"))
    etree.SubElement(tabs, q("tab"), {q("val"): "right", q("leader"): "dot", q("pos"): RIGHT_TAB})
    etree.SubElement(ppr, q("spacing"), {q("before"): "40", q("after"): "40", q("line"): "276", q("lineRule"): "auto"})
    etree.SubElement(ppr, q("ind"), {q("left"): str(284 * level), q("right"): "0"})
    etree.SubElement(ppr, q("jc"), {q("val"): "left"})
    rpr = style.find(q("rPr"))
    if rpr is not None:
        style.remove(rpr)
    rpr = etree.SubElement(style, q("rPr"))
    etree.SubElement(rpr, q("rFonts"), {q(k): "Times New Roman" for k in ("ascii", "hAnsi", "cs", "eastAsia")})
    etree.SubElement(rpr, q("sz"), {q("val"): "24"})
    etree.SubElement(rpr, q("szCs"), {q("val"): "24"})


def main(path):
    zin = zipfile.ZipFile(path)
    used = referenced_style_ids(zin)
    out = path + ".tmp"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "word/styles.xml":
                root = etree.fromstring(data)
                depends = {c.get(q("val")) for s in root.iter(q("style"))
                           for c in s if c.tag in (q("basedOn"), q("link"), q("next"))}
                removed = []
                for s in list(root.iter(q("style"))):
                    sid = s.get(q("styleId"))
                    if LEGACY_STYLE_RE.match(sid or "") and sid not in used and sid not in depends:
                        s.getparent().remove(s)
                        removed.append(sid)
                for s in root.iter(q("style")):
                    if s.get(q("styleId")) in LIST_STYLES:
                        set_list_style(s, LIST_STYLES[s.get(q("styleId"))])
                print(f"styles.xml: {len(removed)} style dihapus, {reorder(root, 'pPr', PPR_ORDER)} pPr diurutkan")
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            elif info.filename == "word/document.xml":
                root = etree.fromstring(data)
                print(f"document.xml: {reorder(root, 'pPr', PPR_ORDER)} pPr diurutkan")
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            elif info.filename == "word/numbering.xml":
                data = data.replace(b'w:suff w:val="none"', b'w:suff w:val="nothing"')
                root = etree.fromstring(data)
                print(f"numbering.xml: {reorder(root, 'lvl', LVL_ORDER)} lvl diurutkan")
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(info, data)
    zin.close()
    shutil.move(out, path)


if __name__ == "__main__":
    main(sys.argv[1])
