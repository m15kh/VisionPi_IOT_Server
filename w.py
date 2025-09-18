# turbo_en_only.py
import os
import gradio as gr
import whisper
import numpy as np

# Load turbo once
model = whisper.load_model("turbo")

# 🔥 Warm-up right after load (small dummy input)
def warm_up():
    # 1 second of silence at 16kHz
    dummy_audio = np.zeros(16000, dtype=np.float32)
    _ = model.transcribe(dummy_audio, language="en", task="transcribe")

warm_up()  # Do this once at startup

def transcribe(audio_path):
    if not audio_path or not os.path.exists(audio_path):
        return "No audio received."
    try:
        result = model.transcribe(audio_path, language="en", task="transcribe")
        return result.get("text", "").strip()
    
    except Exception as e:
        return f"Error: {e}"

with gr.Blocks(title="Turbo Whisper - English Only") as demo:
    gr.Markdown("## 🎤 Turbo Whisper (English Only)\nRecord or upload audio → get English transcript.")

    audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Audio")
    output = gr.Textbox(label="Transcript", lines=10)

    transcribe_btn = gr.Button("Transcribe 🚀")
    transcribe_btn.click(fn=transcribe, inputs=audio, outputs=output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
