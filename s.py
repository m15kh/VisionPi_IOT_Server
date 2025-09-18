# turbo_en_streamlit.py
import os
import whisper
import streamlit as st

# Load model once
@st.cache_resource
def load_model():
    return whisper.load_model("turbo")

model = load_model()

st.title("🎤 Turbo Whisper (English Only)")
st.write("Upload an English audio file and get a transcript.")

audio_file = st.file_uploader("Upload audio", type=["wav", "mp3", "m4a"])

if audio_file is not None:
    st.audio(audio_file)
    with st.spinner("Transcribing..."):
        # Save to temp file
        temp_path = f"/tmp/{audio_file.name}"
        with open(temp_path, "wb") as f:
            f.write(audio_file.getbuffer())

        # Force English, disable auto-detect
        result = model.transcribe(temp_path, language="en", task="transcribe")
        st.success("✅ Transcription complete!")
        st.text_area("Transcript", value=result["text"], height=200)
