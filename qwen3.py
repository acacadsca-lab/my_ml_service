# app/utils/qwen3.py

import sys
import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel
import uuid
import whisper
import librosa
import os

def main():
    # ==============================
    # INPUT FROM DJANGO
    # ==============================
    ref_audio = sys.argv[1]   # audio file path
    new_text = sys.argv[2]    # text from API

    # ==============================
    # CPU MODE FIX
    # ==============================
    device = "cpu"

    # ==============================
    # STEP 1: SPEECH → TEXT (Whisper)
    # ==============================
    print("🎧 Extracting text from audio...", flush=True)

    whisper_model = whisper.load_model("base")  # CPU model

    audio_data, sample_rate = librosa.load(ref_audio, sr=16000)

    result = whisper_model.transcribe(audio_data)
    ref_text = result["text"].strip()

    print(f"Extracted: {ref_text}", flush=True)

    # ==============================
    # STEP 2: LOAD TTS MODEL (CPU)
    # ==============================
    print("🔄 Loading TTS model...", flush=True)

    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base",  
        device_map={"": device},   # force CPU
        dtype=torch.float32        # CPU compatible
    )

    # ==============================
    # STEP 3: VOICE CLONE
    # ==============================
    print("🎙️ Generating voice...", flush=True)

    wavs, sr = model.generate_voice_clone(
        text=new_text,
        language="English",
        ref_audio=ref_audio,
        ref_text=ref_text,
    )

    # ==============================
    # STEP 4: SAVE OUTPUT
    # ==============================
    os.makedirs("/tmp/tts_output", exist_ok=True)

    output_path = f"/tmp/tts_output/output_{uuid.uuid4()}.wav"

    sf.write(output_path, wavs[0], sr)

    print(output_path, flush=True)  # VERY IMPORTANT


if __name__ == "__main__":
    main()