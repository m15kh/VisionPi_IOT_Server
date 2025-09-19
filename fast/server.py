from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import cv2
import numpy as np
import os
from datetime import datetime
import requests
import uvicorn


app = FastAPI()

class NumberRequest(BaseModel):
    value: float

@app.get("/health")
async def health_check():
    """API health check endpoint that returns service status."""
    return {"status": "healthy", "service": "VisionPi_IOT"}

@app.post("/audio")
async def process_audio(data: NumberRequest):
    result = data.value * 10
    led_state = "on" if data.value > 10 else "off"
    
    try:
        local_server_url = "http://localhost:8080/led"
        requests.post(local_server_url, json={"state": led_state})
    except Exception as e:
        print(f"Failed to send LED command: {e}")
    
    return {"result": result, "led": led_state}




FRAMES_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frames")

@app.websocket("/ws_frames")
async def websocket_frames(websocket: WebSocket):
    await websocket.accept()

    os.makedirs(FRAMES_ROOT, exist_ok=True)

    current_date = datetime.now().strftime("%Y-%m-%d")
    date_dir = os.path.join(FRAMES_ROOT, current_date)
    os.makedirs(date_dir, exist_ok=True)

    frame_count = 0

    try:
        while True:
            data = await websocket.receive_bytes()

            nparr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                await websocket.send_text("ERR: decode failed")
                continue

            timestamp = datetime.now().strftime("%H-%M-%S-%f")
            frame_filename = f"frame_{timestamp}_{frame_count:04d}.jpg"
            frame_path = os.path.join(date_dir, frame_filename)

            try:
                cv2.imwrite(frame_path, img)
                msg = f"OK {img.shape[1]}x{img.shape[0]} (saved {frame_filename})"
            except Exception as e:
                msg = f"ERR: could not save frame ({e})"

            frame_count += 1
            await websocket.send_text(msg)

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=20807, reload=True)

#uvicorn server:app --host 0.0.0.0 --port 20807 --reload
