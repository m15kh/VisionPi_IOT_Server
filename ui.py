from faster_whisper import WhisperModel
import gradio as gr

model_size = "large-v3"
model = WhisperModel(model_size, device="cuda", compute_type="float16")




def transcribe_audio(audio_path):
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    transcript = f"Detected language '{info.language}' with probability {info.language_probability}\n\n"
    for segment in segments:
        transcript += f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
    
    return transcript

# Create Gradio interface
iface = gr.Interface(
    fn=transcribe_audio,
    inputs=gr.Audio(type="filepath"),
    outputs="text",
    title="Audio Transcription",
    description="Upload an audio file to transcribe it using Whisper"
)

# Launch the interface
iface.launch(server_name="0.0.0.0", server_port=8000)