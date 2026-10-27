"""Deep-clone elemen XML lintas dokumen tanpa kehilangan gambar, rumus, OLE, maupun hyperlink."""

import copy
import io

from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from lxml import etree

from src.ooxml.xml import DRAWING_NS, MATH_NS, OFFICE_NS, REL_NS, VML_NS

_REL_EMBED = f"{{{REL_NS}}}embed"
_REL_ID = f"{{{REL_NS}}}id"


def _copy_image_relationship(rid: str, doc_src, doc_out):
    """Menyalin part gambar `rid` ke dokumen output; mengembalikan rId baru atau None."""
    if not rid or rid not in doc_src.part.rels:
        return None
    try:
        blob = doc_src.part.rels[rid].target_part.blob
        image_part = doc_out.part.package.get_or_add_image_part(io.BytesIO(blob))
        return doc_out.part.relate_to(image_part, RT.IMAGE)
    except Exception:  # gambar eksternal/rusak: biarkan rId asli
        return None


def _remap_images(clone, doc_src, doc_out, include_vml: bool = False) -> None:
    targets = [(blip, _REL_EMBED) for blip in clone.findall(f".//{{{DRAWING_NS}}}blip")]
    if include_vml:
        targets += [(img, _REL_ID) for img in clone.findall(f".//{{{VML_NS}}}imagedata")]
    for element, attr in targets:
        new_rid = _copy_image_relationship(element.attrib.get(attr), doc_src, doc_out)
        if new_rid:
            element.set(attr, new_rid)


def _remap_hyperlinks(clone, doc_src, doc_out) -> None:
    for hyperlink in clone.findall(".//" + qn("w:hyperlink")):
        rid = hyperlink.attrib.get(qn("r:id"))
        if not rid or rid not in doc_src.part.rels:
            continue
        rel = doc_src.part.rels[rid]
        if rel.is_external:
            new_rid = doc_out.part.rels.get_or_add_ext_rel(RT.HYPERLINK, rel.target_ref)
            hyperlink.set(qn("r:id"), str(new_rid))


# (tag referensi, relasi part catatan, tag isi catatan)
_NOTE_KINDS = (
    ("w:footnoteReference", RT.FOOTNOTES, "w:footnote"),
    ("w:endnoteReference", RT.ENDNOTES, "w:endnote"),
)
# Komentar reviewer tidak ikut dipindahkan (template tidak punya part komentar).
_COMMENT_TAGS = ("w:commentRangeStart", "w:commentRangeEnd", "w:commentReference")


def _related_part(doc, reltype):
    try:
        return doc.part.part_related_by(reltype)
    except KeyError:
        return None


def _copy_notes(clone, doc_src, doc_out) -> None:
    """Menyalin isi footnote/endnote yang dirujuk paragraf ke part catatan output dengan id baru."""
    for ref_tag, reltype, note_tag in _NOTE_KINDS:
        refs = clone.findall(".//" + qn(ref_tag))
        if not refs:
            continue
        src_part, out_part = _related_part(doc_src, reltype), _related_part(doc_out, reltype)
        src_notes, out_root, next_id = {}, None, 1
        if src_part is not None and out_part is not None:
            src_notes = {n.get(qn("w:id")): n for n in parse_xml(src_part.blob).findall(qn(note_tag))}
            out_root = parse_xml(out_part.blob)
            next_id = max((int(n.get(qn("w:id"))) for n in out_root.findall(qn(note_tag))), default=0) + 1

        for ref in refs:
            note = src_notes.get(ref.get(qn("w:id")))
            if note is None:  # catatan tak ditemukan: buang rujukan agar dokumen tidak rusak
                ref.getparent().remove(ref)
                continue
            new_note = copy.deepcopy(note)
            new_note.set(qn("w:id"), str(next_id))
            out_root.append(new_note)
            ref.set(qn("w:id"), str(next_id))
            next_id += 1
        if out_root is not None:
            out_part._blob = etree.tostring(out_root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _remove_comment_marks(clone) -> None:
    for tag in _COMMENT_TAGS:
        for mark in clone.findall(".//" + qn(tag)):
            mark.getparent().remove(mark)


def append_to_body(doc_out, element, after=None) -> None:
    """Menyisipkan elemen setelah `after`, atau sebelum sectPr akhir dokumen."""
    if after is not None:
        after.addnext(element)
        return
    body = doc_out.element.body
    sect_pr = body.find(qn("w:sectPr"))
    if sect_pr is not None:
        sect_pr.addprevious(element)
    else:
        body.append(element)


def clone_paragraph(p_src_elem, doc_src, doc_out, label: str):
    """Deep-clone paragraf apa adanya (termasuk gambar, VML, hyperlink) ke akhir dokumen output."""
    clone = copy.deepcopy(p_src_elem)
    clone.set("approved_label", label)
    _remap_images(clone, doc_src, doc_out, include_vml=True)
    _remap_hyperlinks(clone, doc_src, doc_out)
    _copy_notes(clone, doc_src, doc_out)
    _remove_comment_marks(clone)
    append_to_body(doc_out, clone)
    return clone


def clone_table(tbl_src_elem, doc_src, doc_out, after=None):
    """Deep-clone tabel beserta gambar di dalam selnya."""
    clone = copy.deepcopy(tbl_src_elem)
    _remap_images(clone, doc_src, doc_out)
    append_to_body(doc_out, clone, after=after)
    return clone


def clone_body_element(element, doc_src, doc_out, after=None):
    """Deep-clone elemen body non-paragraf/non-tabel (mis. w:sdt) setelah `after` atau ke akhir dokumen."""
    clone = copy.deepcopy(element)
    _remap_images(clone, doc_src, doc_out)
    append_to_body(doc_out, clone, after=after)
    return clone


def has_drawing(p_elem) -> bool:
    return bool(p_elem.findall(".//" + qn("w:drawing")) or p_elem.findall(".//" + qn("w:pict")))


def has_rich_content(p_elem) -> bool:
    """True jika paragraf memuat gambar, rumus Office Math, OLE object, atau field code."""
    return bool(
        has_drawing(p_elem)
        or p_elem.findall(f".//{{{MATH_NS}}}oMath")
        or p_elem.findall(f".//{{{MATH_NS}}}oMathPara")
        or p_elem.findall(f".//{{{OFFICE_NS}}}OLEObject")
        or p_elem.findall(".//" + qn("w:fldSimple"))
        or p_elem.findall(".//" + qn("w:fldChar"))
    )


def has_content_besides_ppr(p_elem) -> bool:
    """True jika paragraf punya child selain `w:pPr` (run kosong, bookmark, dll.)."""
    ppr_count = 1 if p_elem.find(qn("w:pPr")) is not None else 0
    return len(p_elem) > ppr_count
