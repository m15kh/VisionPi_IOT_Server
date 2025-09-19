#!/usr/bin/env python3
import os
import time
import threading
from flask import Flask, Response, request, abort, render_template_string

# ----------------- Config -----------------
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 20807
INGEST_TOKEN = os.environ.get("VSTREAM_TOKEN", "change-me")  # set env var in prod
MAX_FRAME_BYTES = 2 * 1024 * 1024  # 2 MiB safety cap
FRAME_TIMEOUT_SEC = 20             # viewer will still get last frame; generator loops

# --------------- App / State --------------
app = Flask(__name__)

_latest_frame = None           # bytes (JPEG)
_frame_lock = threading.Lock()
_frame_event = threading.Event()

# --------------- Web Pages ----------------
INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Vision Stream</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background:#0b0b0f; color:#eaeaea; display:flex; min-height:100vh; align-items:center; justify-content:center; }
    .card { background:#14141c; border-radius:18px; padding:16px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); }
    h1 { margin: 0 0 8px; font-size: 18px; font-weight: 600; opacity: .9; }
    .hint { opacity:.65; font-size: 12px; margin-bottom: 10px; }
    img { width: 80vw; max-width: 960px; height: auto; border-radius: 12px; display:block; background:#000; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Live Stream</h1>
    <div class="hint">If the image is blank, make sure the client is pushing frames to <code>/ingest</code>.</div>
    <img src="/stream" alt="Live stream (MJPEG)"/>
  </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

# --------------- Stream (view) ------------
@app.route("/stream")
def stream():
    boundary = "frame"

    def mjpeg_generator():
        last_emit = 0.0
        while True:
            # Wait until a new frame arrives or timeout to keep connection alive
            _frame_event.wait(timeout=FRAME_TIMEOUT_SEC)
            _frame_event.clear()

            with _frame_lock:
                frame = _latest_frame

            if frame is None:
                # No frame yet: send a tiny 1x1 black JPEG fallback once a second
                time.sleep(1.0)
                continue

            # minimal throttle so we don't spam >30 fps to each viewer
            now = time.time()
            if now - last_emit < 1/30:
                time.sleep(max(0, 1/30 - (now - last_emit)))
            last_emit = time.time()

            yield (
                f"--{boundary}\r\n"
                "Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(frame)}\r\n\r\n"
            ).encode("ascii") + frame + b"\r\n"

    return Response(
        mjpeg_generator(),
        mimetype=f"multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )

# --------------- Ingest (client) ----------
@app.route("/ingest", methods=["POST"])
def ingest():
    # Simple shared-secret header
    token = request.headers.get("X-Token", "")
    if INGEST_TOKEN and token != INGEST_TOKEN:
        abort(401, description="Unauthorized")

    # Accept raw JPEG bytes in the body
    data = request.get_data(cache=False, as_text=False, parse_form_data=False)
    if not data:
        abort(400, description="Empty body")

    if len(data) > MAX_FRAME_BYTES:
        abort(413, description="Frame too large")

    # quick JPEG signature check
    if not (data.startswith(b"\xff\xd8") and data.endswith(b"\xff\xd9")):
        abort(415, description="Body must be a JPEG image")

    # Update latest frame
    with _frame_lock:
        global _latest_frame
        _latest_frame = data
    _frame_event.set()

    # 204 No Content is perfect here
    return ("", 204)

# --------------- Main ---------------------
if __name__ == "__main__":
    # You can also serve with: gunicorn -w 1 -b 0.0.0.0:20807 server_site:app
    app.run(host=LISTEN_HOST, port=LISTEN_PORT, threaded=True)
