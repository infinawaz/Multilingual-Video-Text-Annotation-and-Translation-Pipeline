"""
Multilingual Video Text Annotation and Translation Pipeline
============================================================
FastAPI web application for extracting, annotating, and translating
text from video frames using Tesseract OCR and LibreTranslate.
Optimized to minimize translation API calls via deduplication.
"""

import os
import io
import uuid
import base64
import logging
import tempfile
import shutil

from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pipeline.ocr import extract_text_from_frame
from pipeline.translate import translate_detections, clear_cache
from pipeline.overlay import create_annotated_frame

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multilingual Video Text Annotation & Translation Pipeline",
    description="Extract, annotate, and translate text from video frames",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Uploads directory
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "pipeline_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def image_to_base64(image: Image.Image) -> str:
    """Encode a PIL Image as a base64 JPEG string."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_frames_from_video(video_path: str, max_frames: int = 8) -> list:
    """
    Extract frames from a video file using imageio.
    """
    import imageio.v3 as iio

    try:
        frames_data = iio.imread(video_path, plugin="pyav")
        total_frames = len(frames_data)
    except Exception:
        frames_data = list(iio.imiter(video_path, plugin="pyav"))
        total_frames = len(frames_data)

    if total_frames == 0:
        return []

    interval = max(1, total_frames // max_frames)
    frames = []

    for i in range(0, total_frames, interval):
        if len(frames) >= max_frames:
            break
        frame_array = frames_data[i] if i < len(frames_data) else None
        if frame_array is not None:
            pil_image = Image.fromarray(frame_array)
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            frames.append((i, pil_image))

    return frames


def deduplicate_text(all_frame_detections: list) -> dict:
    """
    Collect all unique texts across all frames, so we only
    translate each unique string once.

    Returns:
        Dict mapping unique text -> list of (frame_idx, det_idx) positions.
    """
    text_map = {}
    for frame_idx, detections in enumerate(all_frame_detections):
        for det_idx, det in enumerate(detections):
            key = (det["text"].strip(), det.get("language", "eng"))
            if key not in text_map:
                text_map[key] = []
            text_map[key].append((frame_idx, det_idx))
    return text_map


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend UI."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h1>Pipeline API is running</h1><p>Place index.html in /static</p>"
    )


@app.get("/api/health")
async def health():
    """Health check endpoint for Render."""
    return {"status": "healthy", "service": "multilingual-video-pipeline"}


@app.post("/api/process")
async def process_video(
    file: UploadFile = File(...),
    target_lang: str = Query("en", description="Target language code (en, hi, bn, ta)"),
    max_frames: int = Query(8, description="Maximum frames to process", ge=1, le=30),
):
    """
    Process a video or image file.
    Deduplicates translation calls: identical text across frames
    is only sent to the translation API once.
    """
    allowed_video = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    allowed_image = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    ext = os.path.splitext(file.filename or "")[1].lower()

    if ext not in allowed_video and ext not in allowed_image:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {allowed_video | allowed_image}",
        )

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Clear translation cache for this new job
        clear_cache()

        is_image = ext in allowed_image

        # Step 1: Extract all frames
        if is_image:
            image = Image.open(file_path).convert("RGB")
            frames = [(0, image)]
        else:
            frames = extract_frames_from_video(file_path, max_frames=max_frames)
            if not frames:
                raise HTTPException(status_code=400, detail="No frames extracted from video")

        # Step 2: Run OCR on all frames
        all_detections = []
        for frame_num, frame in frames:
            detections = extract_text_from_frame(frame)
            all_detections.append(detections)

        # Step 3: Translate — cache ensures duplicates are NOT re-translated
        # The translate module's cache handles deduplication automatically.
        # If frame 1 has "Hello" and frame 5 also has "Hello",
        # the API is called only once.
        for detections in all_detections:
            translate_detections(detections, target_lang=target_lang)

        # Step 4: Generate annotated frames + build response
        results = []
        total_api_calls = len(set(
            d["text"].strip()
            for dets in all_detections
            for d in dets
            if d.get("translation_status") == "success"
        ))

        for (frame_num, frame), detections in zip(frames, all_detections):
            annotated = create_annotated_frame(frame, detections)
            results.append({
                "frame_number": frame_num,
                "detections": detections,
                "annotated_frame": image_to_base64(annotated),
                "original_frame": image_to_base64(frame),
            })

        total_detections = sum(len(r["detections"]) for r in results)
        languages_found = list(
            set(d["language"] for r in results for d in r["detections"])
        )

        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "frames_processed": len(results),
            "total_text_regions": total_detections,
            "unique_translations": total_api_calls,
            "languages_detected": languages_found,
            "target_language": target_lang,
            "frames": results,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.get("/api/languages")
async def get_languages():
    """Return supported languages."""
    return {
        "source_languages": [
            {"code": "eng", "name": "English", "lt_code": "en"},
            {"code": "hin", "name": "Hindi", "lt_code": "hi"},
            {"code": "ben", "name": "Bengali", "lt_code": "bn"},
            {"code": "tam", "name": "Tamil", "lt_code": "ta"},
        ],
        "target_languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "Hindi"},
            {"code": "bn", "name": "Bengali"},
            {"code": "ta", "name": "Tamil"},
        ],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
