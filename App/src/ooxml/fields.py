"""Field dinamis Word (STYLEREF/SEQ), bookmark, dan pencetakan miring istilah asing."""

import re

from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from src.ooxml.xml import W_NS, style_run

_CAPTION_RPR = (
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
    '<w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="000000"/>'
)

FOREIGN_TERMS = (
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
    "per se", "a priori", "a posteriori",
)

_FOREIGN_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in sorted(FOREIGN_TERMS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def _caption_run(content: str, no_proof: bool = False):
    rpr = _CAPTION_RPR + ("<w:noProof/>" if no_proof else "")
    return parse_xml(f'<w:r xmlns:w="{W_NS}"><w:rPr>{rpr}</w:rPr>{content}</w:r>')


def _field_runs(instruction: str, display_value) -> list:
    """Urutan run sebuah complex field: begin, instrText, separate, nilai tampilan, end."""
    return [
        _caption_run('<w:fldChar w:fldCharType="begin"/>'),
        _caption_run(f'<w:instrText xml:space="preserve">{instruction}</w:instrText>'),
        _caption_run('<w:fldChar w:fldCharType="separate"/>'),
        _caption_run(f"<w:t>{display_value}</w:t>", no_proof=True),
        _caption_run('<w:fldChar w:fldCharType="end"/>'),
    ]


def add_seq_caption_field(p, seq_name: str, bab_num: int, item_num: int, title_text: str) -> None:
    """Menyisipkan '{STYLEREF 1 \\s}.{SEQ <seq_name> \\* ARABIC \\s 1}' lalu judul caption."""
    runs = (
        _field_runs(" STYLEREF 1 \\s ", bab_num)
        + [_caption_run("<w:t>.</w:t>")]
        + _field_runs(f" SEQ {seq_name} \\* ARABIC \\s 1 ", item_num)
    )
    for run in runs:
        p._p.append(run)
    if title_text:
        style_run(p.add_run(title_text), 12, bold=True)


def bookmark_pair(bookmark_id: int, name: str):
    """Pasangan elemen bookmarkStart/bookmarkEnd."""
    start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{bookmark_id}" w:name="{name}"/>')
    end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{bookmark_id}"/>')
    return start, end


def italicize_foreign_terms(p) -> None:
    """Mencetak miring istilah asing dalam paragraf bahasa Indonesia (pedoman EYD)."""
    full_text = p.text
    if not full_text or not _FOREIGN_PATTERN.search(full_text):
        return

    segments = []
    last_idx = 0
    for match in _FOREIGN_PATTERN.finditer(full_text):
        start, end = match.span()
        if start > last_idx:
            segments.append((full_text[last_idx:start], False))
        segments.append((full_text[start:end], True))
        last_idx = end
    if last_idx < len(full_text):
        segments.append((full_text[last_idx:], False))

    p.text = ""
    for text_part, is_foreign in segments:
        style_run(p.add_run(text_part), 12, bold=False, italic=is_foreign)
