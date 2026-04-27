import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel
import os
import uuid
import whisper
import librosa  # ✅ FFmpeg replacement

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

print("🎧 Audio-la irundhu text extract pannurom...")

# ======================================
# FFmpeg-ku Alternative: librosa use pannurom
# ======================================
whisper_model = whisper.load_model("base")

ref_audio = "20sec.mp3"

# Method 1: librosa use panni audio load pannalam
audio_data, sample_rate = librosa.load(ref_audio, sr=16000)

# Whisper-ku direct audio array kudukkalam
result = whisper_model.transcribe(audio_data)
ref_text = result["text"].strip()

print(f"✅ Extracted Text: {ref_text}")
print("=" * 60)

# ======================================
# Rest of the code same...
# ======================================
print("🔄 TTS Model load pannurom...")
model = Qwen3TTSModel.from_pretrained( 
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="auto",
    dtype=torch.bfloat16,
)

new_text = """
At Osiz, we have been the driving force for countless career success stories. With our wide range of career options, we have transformed the lives of individuals, while also igniting growth and success for employers. Our commitment to excellence has established us as a trusted partner in the job market by connecting talented professionals with rewarding opportunities. Through our innovative approach, we have connected talented professionals with opportunities that align with their passions and aspirations.
"""

print(f"🎙️ Voice cloning start...")

wavs, sr = model.generate_voice_clone(
    text=new_text,
    language="English",
    ref_audio=ref_audio,
    ref_text=ref_text,
)

output_file = f"output_voice_clone_{uuid.uuid4()}.wav"
output_path = os.path.join("output", output_file)  # ✅ Folder path join pannurom

sf.write(output_path, wavs[0], sr)

print(f"✅ Successfully saved: {output_file}")