"""
Aplikasi Web Multi-Page untuk Seminar Proposal & Pengujian Multi-Agent System (Asdoku).
Dibangun dengan FastAPI + Multi-Page Architecture (MPA) + Vanilla CSS Modern.

Halaman:
1. /          -> Home (Cover Seminar Proposal Elegan)
2. /alat      -> Alat (Studio Pengujian Multi-Agent .docx)
3. /data      -> Data (Metodologi Riset & Evaluasi Empiris Model)
4. /flowchart -> Pembahasan: Flowchart Sistem & Two-Tier SQA
5. /pipeline  -> Pembahasan: Arsitektur Tiga Agen Cerdas
6. /riwayat   -> Pembahasan: Kronologi 5 Babak Riset & Catatan Sempro
7. /info      -> Info (Glosarium 16 Istilah Teknis Akademik AI & OpenXML)
"""

import os
import re
import time
import uuid
import shutil
from collections import OrderedDict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

from src.agents.inspector import InspectorAgent
from src.agents.critic import QualityCriticAgent
from src.agents.formatter import FormattingActuatorAgent
from src.active_learning import SOURCE_MANUAL, ActiveLearningManager

app = FastAPI(
    title="Asdoku MAS Tester",
    description="Web Pengujian Multi-Agent System Dokumen Akademik UEU",
    redirect_slashes=False
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = bool(os.environ.get("VERCEL"))
UPLOAD_DIR = "/tmp/uploads" if IS_VERCEL else "data/uploads"
OUTPUT_DIR = "/tmp/output" if IS_VERCEL else "output"
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Inisialisasi Agen & Active Learning Manager
print("[SYSTEM] Menginisialisasi Multi-Agent System & Active Learning Loop...")
active_learning = ActiveLearningManager()
inspector = InspectorAgent()
critic = QualityCriticAgent(active_learning)  # satu pool feedback dipakai bersama
formatter = FormattingActuatorAgent()
print("[SYSTEM] Seluruh Agen & Self-Improvement Loop Siap Beroperasi!")

# Kueri Active Learning yang menunggu jawaban pengguna: review_id -> paragraf beserta fitur tipografinya.
# Disimpan di memori server (bukan dikirim balik oleh klien) agar fitur latih tidak dapat dimanipulasi.
REVIEW_CACHE_SIZE = 500
RETRAIN_EVERY_MANUAL_LABELS = 5  # retraining otomatis tiap 5 label manual baru
review_cache: "OrderedDict[str, dict]" = OrderedDict()


def _register_review_queue(queue: list) -> list:
    """Menyimpan kueri ke cache dan mengembalikan versi ringkas untuk UI."""
    public = []
    for item in queue:
        review_id = uuid.uuid4().hex
        review_cache[review_id] = item
        public.append({
            "review_id": review_id,
            "idx": item["para_id"],
            "text": item["text"][:160],
            "predicted_label": item["predicted_label"],
            "confidence": item["confidence"],
            "alternatives": item["alternatives"],
        })
    while len(review_cache) > REVIEW_CACHE_SIZE:
        review_cache.popitem(last=False)
    return public

# ============================================================
# TEMPLATE LOADER & MULTI-PAGE RENDERER
# ============================================================
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
NAV_PAGES = ("home", "alat", "data", "info")
PEMBAHASAN_PAGES = ("flowchart", "pipeline", "riwayat")


def load_template(filename: str) -> str:
    with open(os.path.join(TEMPLATE_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


def render_page(page_id: str, content_filename: str, pembahasan_label: str = "Pembahasan", scripts: str = "") -> str:
    replacements = {f"{{{{active_{p}}}}}": "active" if page_id == p else "" for p in NAV_PAGES}
    replacements["{{active_pembahasan}}"] = "active" if page_id in PEMBAHASAN_PAGES else ""
    replacements["{{pembahasan_label}}"] = pembahasan_label
    replacements.update({f"{{{{active_{p}}}}}": "active-item" if page_id == p else "" for p in PEMBAHASAN_PAGES})
    replacements["{{content}}"] = load_template(content_filename)
    replacements["{{scripts}}"] = scripts

    html = load_template("base.html")
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    return html


# ============================================================
# MULTI-PAGE ROUTES (Option 2: True MPA with unique URLs)
# ============================================================
# (paths, page_id, template, label menu Pembahasan)
_PAGES = (
    (("/",), "home", "home.html", "Pembahasan"),
    (("/data",), "data", "data.html", "Pembahasan"),
    (("/flowchart",), "flowchart", "flowchart.html", "Pembahasan: Flowchart"),
    (("/pipeline", "/agen"), "pipeline", "pipeline.html", "Pembahasan: 3 Agen"),
    (("/riwayat",), "riwayat", "riwayat.html", "Pembahasan: Kronologi"),
    (("/info",), "info", "info.html", "Pembahasan"),
)


def _register_page(paths, page_id: str, template: str, label: str) -> None:
    async def page() -> str:
        return render_page(page_id, template, pembahasan_label=label)

    for path in paths:
        app.add_api_route(path, page, methods=["GET"], response_class=HTMLResponse, name=f"page_{page_id}")


for _page in _PAGES:
    _register_page(*_page)


@app.get("/alat", response_class=HTMLResponse)
async def page_alat():
    alat_js = f"<script>\n{load_template('alat.js')}\n</script>"
    return render_page("alat", "alat.html", scripts=alat_js)


# ============================================================
# API ENDPOINTS (Format, Feedback, Retrain, & Assets)
# ============================================================

def run_auto_retrain():
    try:
        result = active_learning.retrain_agent_1()
        if result.get("accepted"):
            inspector.reload_model()
            print("[Active Learning] Background Retraining & Hot-Reload berhasil diselesaikan!")
    except Exception as e:
        print(f"[Active Learning] Background Retraining error: {e}")

@app.post("/api/format")
async def api_format_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Hanya berkas .docx yang didukung.")

    start_time = time.time()
    temp_input = os.path.join(UPLOAD_DIR, f"upload_{int(time.time())}_{file.filename}")
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    raw_name = file.filename
    clean_name = re.sub(r'^(?:rapi_\d+_|upload_\d+_|\(Asdoku\)\s*-\s*)+', '', raw_name)
    output_filename = f"(Asdoku) - {clean_name}"
    temp_output = os.path.join(OUTPUT_DIR, output_filename)

    # 1. SQA Tier 1 Loop: Agent 1 (Inspector) <-> Agent 2 (SQA Gatekeeper)
    draft = inspector.inspect(temp_input)
    approved = critic.coordinate_tier1_blueprint_loop(
        inspection_report=draft,
        inspector_agent=inspector,
        max_iterations=3
    )

    # 2. SQA Tier 2 Loop: Agent 3 (Formatter) <-> Agent 2 (SQA Acceptance Auditor)
    tier2_res = critic.coordinate_tier2_artifact_loop(
        input_docx_path=temp_input,
        approved_blueprint=approved,
        output_docx_path=temp_output,
        formatter_agent=formatter,
        max_iterations=3
    )
    qa_result = tier2_res["final_qa_result"]
    # Weak label Agent 2 tetap tercatat di pool, tetapi tidak memicu retraining: uji non-regresi
    # menunjukkan label tersebut menurunkan kinerja. Retraining dipicu oleh label manual (lihat feedback).

    elapsed_time = round(time.time() - start_time, 2)

    return {
        "status": "success",
        "output_filename": output_filename,
        "elapsed_time": elapsed_time,
        "total_paragraphs": draft["total_paragraphs"],
        "total_corrections": approved["total_corrections"],
        "corrections_log": [
            {
                "idx": c.get("para_id", c.get("idx", 0)),
                "text": c.get("text", ""),
                "agent1_pred": c.get("original_pred", c.get("agent1_pred", "")),
                "corrected_to": c.get("corrected_label", c.get("corrected_to", "")),
                "reason": c.get("reason", "")
            }
            for c in approved.get("corrections_log", [])
        ],
        "approved_chapters": approved.get("approved_chapters", []),
        "review_queue": _register_review_queue(approved.get("review_queue", [])),
        "sqa_score": qa_result.get("qa_score", qa_result.get("score", 100.0)),
        "sqa_status": qa_result.get("status", "PASS"),
        "sqa_defects": qa_result.get("defects", []),
        "sqa_tier1_iterations": approved.get("sqa_tier1_iterations", approved.get("iteration_count", 1)),
        "sqa_tier2_iterations": tier2_res.get("tier2_iterations", tier2_res.get("iterations", 1))
    }

@app.get("/api/download/{filename}")
async def api_download_file(filename: str):
    # Cegah path traversal: hanya nama berkas di dalam OUTPUT_DIR yang dilayani.
    safe_name = os.path.basename(filename)
    file_path = os.path.join(OUTPUT_DIR, safe_name)
    if safe_name != filename or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Berkas hasil tidak ditemukan.")
    return FileResponse(file_path, media_type=DOCX_MEDIA_TYPE, filename=safe_name)

@app.post("/api/active-learning/feedback")
async def api_al_feedback(
    background_tasks: BackgroundTasks,
    paragraph_idx: int = Form(...),
    paragraph_text: str = Form(...),
    correct_label: str = Form(...),
    review_id: str = Form("")
):
    # Jawaban atas kueri Active Learning memakai teks & fitur asli dari cache server
    cached = review_cache.get(review_id) if review_id else None
    try:
        saved = active_learning.record_manual_correction(
            idx=cached["para_id"] if cached else paragraph_idx,
            text=cached["text"] if cached else paragraph_text,
            correct_label=correct_label,
            raw_features=cached["raw_features"] if cached else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    review_cache.pop(review_id, None)
    message = "Label tersimpan ke Active Learning Pool." if saved else "Label yang sama sudah ada di pool."

    manual_total = active_learning.get_stats()["label_sources"].get(SOURCE_MANUAL, 0)
    retrain_scheduled = bool(saved) and manual_total % RETRAIN_EVERY_MANUAL_LABELS == 0
    if retrain_scheduled:
        print(f"[Active Learning] {manual_total} label manual terkumpul; menjadwalkan retraining di latar belakang...")
        background_tasks.add_task(run_auto_retrain)
    return {"status": "success", "saved": saved, "message": message, "retrain_scheduled": retrain_scheduled}

@app.post("/api/active-learning/retrain")
async def api_al_retrain():
    try:
        result = active_learning.retrain_agent_1()
        if result.get("accepted"):
            inspector.reload_model()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================
# STATIC IMAGE ASSETS
# ============================================================
# (URL alias, path relatif terhadap BASE_DIR, media type, label 404)
_STATIC_IMAGES = (
    (("/logo.png", "/AsdokuLogo.png", "/favicon.ico"), "AsdokuLogo.png", "image/png", "Logo"),
    (("/logo_ueu.png",), os.path.join("data", "logo_ueu.png"), "image/png", "UEU Logo"),
    (("/profil.jpeg", "/profil.jpg"), "profil.jpeg", "image/jpeg", "Profil image"),
    (("/agent1.png", "/Agent 1.png"), "Agent 1.png", "image/png", "Agent 1"),
    (("/agent2.png", "/Agent 2.png"), "Agent 2.png", "image/png", "Agent 2"),
    (("/agent3.png", "/Agent 3.png"), "Agent 3.png", "image/png", "Agent 3"),
)


def _register_static_image(urls, relative_path: str, media_type: str, label: str) -> None:
    path = os.path.join(BASE_DIR, relative_path)

    async def serve_image():
        if os.path.exists(path):
            return FileResponse(path, media_type=media_type)
        raise HTTPException(status_code=404, detail=f"{label} not found")

    for url in urls:
        app.add_api_route(url, serve_image, methods=["GET", "HEAD"], name=f"image_{label}")


for _image in _STATIC_IMAGES:
    _register_static_image(*_image)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
