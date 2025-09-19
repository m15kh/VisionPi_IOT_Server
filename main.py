from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from contextlib import asynccontextmanager
from pydantic import BaseModel
import cv2
import numpy as np
import os
from datetime import datetime
import requests
import uvicorn
from faster_whisper import WhisperModel
import tempfile

# Global variable to store the model
whisper_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model on startup
    global whisper_model
    print("Loading Whisper model...")
    model_size = "large-v3"
    # Uncomment the line below to check CUDA availability
    # import torch
    # print(f"CUDA available: {torch.cuda.is_available()}")
    # print(f"CUDA device count: {torch.cuda.device_count()}")
    
    # Run on GPU with FP16 if available, otherwise fall back to CPU
    try:
        whisper_model = WhisperModel(model_size, device="cuda", compute_type="float16")
        print("Whisper model loaded on GPU")
    except Exception as e:
        print(f"Failed to load model on GPU: {e}")
        print("Falling back to CPU")
        whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("Whisper model loaded on CPU")
    
    yield
    # Cleanup on shutdown
    print("Shutting down Whisper model...")
    whisper_model = None


app = FastAPI(lifespan=lifespan)

class NumberRequest(BaseModel):
    value: float

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    language_probability: float



@app.get("/health")
async def health_check():
    """API health check endpoint that returns service status."""
    return {"status": "healthy", "service": "VisionPi_IOT"}

@app.post("/audio", response_model=dict)
async def process_audio(data: NumberRequest):
    """
    Process audio data and control LED based on input value.
    
    Args:
        data: Request object containing a numeric value (1 for LED on, 0 for LED off)
        
    Returns:
        Dictionary with processed result and LED state
    """
    
    # Change logic to check for exact values 1 and 0
    if data.value == 1:
        led_state = "on"
    elif data.value == 0:
        led_state = "off"
    else:
        # Handle unexpected values
        led_state = "not valid just 1 or 0"
    
    
    return {
        "led": led_state,
    }




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


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe an audio file using Whisper model
    
    Args:
        file: The audio file to transcribe
        
    Returns:
        Dictionary with transcription results
    """
    if whisper_model is None:
        return {"error": "Model not loaded"}
    
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name
    
    try:
        # Transcribe the audio
        segments, info = whisper_model.transcribe(temp_audio_path, beam_size=5)
        
        # Combine all segments into one text
        full_text = " ".join([segment.text for segment in segments])
        
        return {
            "text": full_text,
            "language": info.language,
            "language_probability": float(info.language_probability)
        }
    except Exception as e:
        return {"error": f"Transcription failed: {str(e)}"}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)

#uvicorn main:app  --port 20807 --reload
