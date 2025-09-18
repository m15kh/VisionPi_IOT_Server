from faster_whisper import WhisperModel
m = WhisperModel("tiny", device="cuda", compute_type="float16", device_index=0)
print("OK: model loaded on CUDA")
