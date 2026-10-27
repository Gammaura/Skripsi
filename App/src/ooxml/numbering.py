"""Pengelolaan definisi multilevel list (BAB I, 1.1, 1.1.1) di `word/numbering.xml`."""

from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

from src.ooxml.xml import NS, upsert_val, w_el

SUB_LEVEL_INDENT = "720"  # 1.27 cm

_NEW_HEADING_ABSTRACT_NUM = """
<w:abstractNum {nsdecls} w:abstractNumId="{abs_id}">
    <w:nsid w:val="23A70725"/>
    <w:multiLevelType w:val="multilevel"/>
    <w:tmpl w:val="4F725FCE"/>
    <w:lvl w:ilvl="0">
        <w:start w:val="1"/>
        <w:numFmt w:val="upperRoman"/>
        <w:lvlText w:val="BAB %1"/>
        <w:lvlJc w:val="center"/>
        <w:suff w:val="nothing"/>
        <w:pPr><w:jc w:val="center"/><w:ind w:left="0" w:hanging="0"/></w:pPr>
    </w:lvl>
    <w:lvl w:ilvl="1">
        <w:start w:val="1"/>
        <w:numFmt w:val="decimal"/>
        <w:lvlRestart w:val="1"/>
        <w:isLgl/>
        <w:lvlText w:val="%1.%2"/>
        <w:lvlJc w:val="left"/>
        <w:suff w:val="tab"/>
        <w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="720"/></w:pPr>
    </w:lvl>
    <w:lvl w:ilvl="2">
        <w:start w:val="1"/>
        <w:numFmt w:val="decimal"/>
        <w:lvlRestart w:val="2"/>
        <w:isLgl/>
        <w:lvlText w:val="%1.%2.%3"/>
        <w:lvlJc w:val="left"/>
        <w:suff w:val="tab"/>
        <w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="720"/></w:pPr>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
    </w:lvl>
    <w:lvl w:ilvl="3">
        <w:start w:val="1"/>
        <w:numFmt w:val="decimal"/>
        <w:lvlRestart w:val="3"/>
        <w:isLgl/>
        <w:lvlText w:val="%1.%2.%3.%4"/>
        <w:lvlJc w:val="left"/>
        <w:suff w:val="tab"/>
        <w:pPr><w:ind w:left="864" w:hanging="864"/></w:pPr>
    </w:lvl>
</w:abstractNum>
"""


def _int_ids(elements, attr: str) -> list:
    values = (el.attrib.get(qn(attr), "0") for el in elements)
    return [int(v) for v in values if v.isdigit()]


def _configure_bab_level(lvl0, lvl_text) -> None:
    """Level 0 (BAB I): Heading1, upperRoman, tanpa suffix, rata tengah, tanpa indentasi."""
    upsert_val(lvl0, "w:pStyle", "Heading1")
    upsert_val(lvl0, "w:numFmt", "upperRoman")
    lvl_text.set(qn("w:val"), "BAB %1")
    upsert_val(lvl0, "w:suff", "nothing")
    upsert_val(lvl0, "w:lvlJc", "center")

    pPr = lvl0.find("w:pPr", NS)
    if pPr is None:
        lvl0.append(w_el("pPr", inner='<w:ind w:left="0" w:hanging="0"/>'))
        return
    ind = pPr.find("w:ind", NS)
    if ind is not None:
        ind.set(qn("w:left"), "0")
        ind.set(qn("w:hanging"), "0")


def _configure_sub_level(lvl, style_id: str, restart: str, text: str) -> None:
    """Level 1/2 (1.1 / 1.1.1): penomoran legal, restart per level induk, tab stop 1.27 cm."""
    upsert_val(lvl, "w:pStyle", style_id)
    upsert_val(lvl, "w:lvlRestart", restart)
    if lvl.find("w:isLgl", NS) is None:
        lvl.append(w_el("isLgl"))
    lvl_text = lvl.find("w:lvlText", NS)
    if lvl_text is not None:
        lvl_text.set(qn("w:val"), text)
    upsert_val(lvl, "w:suff", "tab")

    pPr = lvl.find("w:pPr", NS)
    if pPr is None:
        return
    ind = pPr.find("w:ind", NS)
    if ind is not None:
        ind.set(qn("w:left"), SUB_LEVEL_INDENT)
        ind.set(qn("w:hanging"), SUB_LEVEL_INDENT)
    tabs = pPr.find("w:tabs", NS)
    if tabs is not None:
        pPr.remove(tabs)
    pPr.append(w_el("tabs", inner=f'<w:tab w:val="num" w:pos="{SUB_LEVEL_INDENT}"/>'))


def _ensure_num_for_abstract(numbering_elm, abs_id: str) -> None:
    for num in numbering_elm.findall("w:num", NS):
        ref = num.find("w:abstractNumId", NS)
        if ref is not None and ref.attrib.get(qn("w:val")) == abs_id:
            return
    new_num_id = max(_int_ids(numbering_elm.findall("w:num", NS), "w:numId") + [0]) + 1
    numbering_elm.append(parse_xml(f'<w:num {nsdecls("w")} w:numId="{new_num_id}"><w:abstractNumId w:val="{abs_id}"/></w:num>'))


def ensure_heading_multilevel_list(numbering_elm) -> None:
    """Menormalkan abstractNum 'BAB %1' yang sudah ada, atau membuat yang baru sesuai template UEU."""
    for abs_num in numbering_elm.findall("w:abstractNum", NS):
        lvl0 = abs_num.find('w:lvl[@w:ilvl="0"]', NS)
        lvl_text = lvl0.find("w:lvlText", NS) if lvl0 is not None else None
        if lvl_text is None or "BAB" not in lvl_text.attrib.get(qn("w:val"), ""):
            continue

        _configure_bab_level(lvl0, lvl_text)
        for ilvl, style_id, restart, text in (("1", "Heading2", "1", "%1.%2"), ("2", "Heading3", "2", "%1.%2.%3")):
            lvl = abs_num.find(f'w:lvl[@w:ilvl="{ilvl}"]', NS)
            if lvl is not None:
                _configure_sub_level(lvl, style_id, restart, text)
        _ensure_num_for_abstract(numbering_elm, abs_num.attrib.get(qn("w:abstractNumId")))
        return

    new_abs_id = max(_int_ids(numbering_elm.findall("w:abstractNum", NS), "w:abstractNumId") + [0]) + 1
    new_num_id = max(_int_ids(numbering_elm.findall("w:num", NS), "w:numId") + [0]) + 1
    abs_elm = parse_xml(_NEW_HEADING_ABSTRACT_NUM.format(nsdecls=nsdecls("w"), abs_id=new_abs_id))
    first_num = numbering_elm.find(qn("w:num"))
    if first_num is not None:
        first_num.addprevious(abs_elm)
    else:
        numbering_elm.append(abs_elm)
    numbering_elm.append(parse_xml(f'<w:num {nsdecls("w")} w:numId="{new_num_id}"><w:abstractNumId w:val="{new_abs_id}"/></w:num>'))


def normalize_template_bab_level(numbering_elm, abstract_num_id: str = "2") -> None:
    """Memastikan level 0 abstractNum template (BAB I) memakai upperRoman, rata tengah, tanpa suffix."""
    for abs_num in numbering_elm.findall(qn("w:abstractNum")):
        if abs_num.attrib.get(qn("w:abstractNumId")) != abstract_num_id:
            continue
        lvl0 = abs_num.find(qn("w:lvl"))
        if lvl0 is None:
            continue
        upsert_val(lvl0, "w:suff", "none")
        for tag, value in (("w:lvlJc", "center"), ("w:numFmt", "upperRoman")):
            child = lvl0.find(qn(tag))
            if child is not None:
                child.set(qn("w:val"), value)


def next_num_id(numbering_elm) -> int:
    """numId berikutnya yang belum dipakai."""
    return max([int(n.attrib.get(qn("w:numId"), 0)) for n in numbering_elm.findall(qn("w:num"))] or [0]) + 1


def add_restarting_list_num(numbering_elm, num_id: str, abstract_num_id: str = "1") -> None:
    """Mendaftarkan numId baru yang selalu mulai dari 1 (list independen per sub-bab)."""
    overrides = "".join(f'<w:lvlOverride w:ilvl="{i}"><w:startOverride w:val="1"/></w:lvlOverride>' for i in range(3))
    numbering_elm.append(w_el("num", {"numId": num_id}, inner=f'<w:abstractNumId w:val="{abstract_num_id}"/>{overrides}'))
