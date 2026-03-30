import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel
import os
os.environ["CUDA_VISIBLE_DEVICES"]="0"
import uuid
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="auto",
    dtype=torch.bfloat16,
    # attn_implementation="flash_attention_2",
)

ref_audio = "20sec.mp3"
ref_text  = "Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it! And thanks to you."

wavs, sr = model.generate_voice_clone(
    text="Osiz technologies. Yeah. I resent you. I love you. I respect you. But you know what? You blew it! And thanks to you.When an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. When an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. ",
    language="English",
    ref_audio=ref_audio,
    ref_text=ref_text,
)
sf.write(f"output_voice_clone+{uuid.uuid4()}+.wav", wavs[0], sr)
