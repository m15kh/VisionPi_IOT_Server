from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import aiofiles
import time
import os

app = FastAPI(title="Frame Ingest Server")

# Adjust this to the IP/domain of your frontend if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(os.getenv("FRAME_SAVE_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload_frame")
async def upload_frame(
    file: UploadFile = File(...),
    camera_id: str = Form("default"),
    ts_ms: str = Form(None),
):
    """
    Receives one image frame and writes it to data/<camera_id>/<timestamp>.jpg
    """
    # timestamp in ms (client-provided or server-generated)
    if ts_ms is None:
        ts_ms = str(int(time.time() * 1000))

    # sanitize camera_id to a folder-safe name
    camera_id = "".join(c for c in camera_id if c.isalnum() or c in ("-", "_")) or "default"
    cam_dir = DATA_DIR / camera_id
    cam_dir.mkdir(parents=True, exist_ok=True)

    # name file with monotonic-ish timestamp
    out_path = cam_dir / f"{ts_ms}.jpg"

    try:
        async with aiofiles.open(out_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await f.write(chunk)
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

    return {"ok": True, "saved": str(out_path)}
