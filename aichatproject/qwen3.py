# app/services/tts_service.py

import torch
import whisper
from qwen_tts import Qwen3TTSModel
import numpy as np

class TTSService:
    def __init__(self):
        print("🚀 Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")

        print("🚀 Loading Qwen TTS model...")
        self.tts_model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map={"": "cpu"},
            dtype=torch.float32
        )

    def transcribe(self, audio_path):
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)

        result = self.whisper_model.transcribe(audio)
        return result["text"].strip()

    def split_text(self, text, max_len=200):
        return [text[i:i+max_len] for i in range(0, len(text), max_len)]

    def generate(self, ref_audio, new_text):
        ref_text = self.transcribe(ref_audio)

        chunks = self.split_text(new_text)

        all_wavs = []
        sr = None

        for chunk in chunks:
            wavs, sr = self.tts_model.generate_voice_clone(
                text=chunk,
                language="English",
                ref_audio=ref_audio,
                ref_text=ref_text,
            )
            all_wavs.append(wavs[0])

        final_audio = np.concatenate(all_wavs)
        return final_audio, sr


# 🔥 Singleton (loads once)
tts_service = TTSService()