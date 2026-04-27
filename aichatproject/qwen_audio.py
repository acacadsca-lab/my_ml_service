import sys

import librosa
import torch
from transformers import Qwen2AudioForConditionalGeneration, AutoProcessor

print("Loading Processor and Model...")

processor = AutoProcessor.from_pretrained(
    "Qwen/Qwen2-Audio-7B-Instruct", 
    trust_remote_code=True
)

model = Qwen2AudioForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-Audio-7B-Instruct", 
    device_map="cpu", 
    torch_dtype=torch.float16, # <-- Added this so you don't run out of memory!
    trust_remote_code=True
)

test_prompt = (
    "This audio contains a back-and-forth conversation between two different people. "
    "You must transcribe the audio TURN-BY-TURN. Every single time a different person starts speaking, "
    "you MUST create a new JSON object for them. "
    "Identify them alternatingly as 'Speaker 1' and 'Speaker 2'. "
    "Output STRICTLY as a JSON array with absolutely no other text. Use this exact structure:\n"
    "[\n"
    "  {\"speaker\": \"Speaker 1\", \"text\": \"...\"},\n"
    "  {\"speaker\": \"Speaker 2\", \"text\": \"...\"},\n"
    "  {\"speaker\": \"Speaker 1\", \"text\": \"...\"},\n"
    "  {\"speaker\": \"Speaker 2\", \"text\": \"...\"}\n"
    "]"
)
conversation = [
    {"role": "user", "content": [
        {"type": "audio", "audio_url":  sys.argv[1]},
        {"type": "text", "text": test_prompt},
    ]},
]

text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)

audios = []
for message in conversation:
    if isinstance(message["content"], list):
        for ele in message["content"]:
            if ele["type"] == "audio":
                audio_data, _ = librosa.load(
                    ele['audio_url'], 
                    sr=processor.feature_extractor.sampling_rate,
                    mono=True
                )
                audios.append(audio_data)

inputs = processor(text=text, audios=audios, return_tensors="pt", padding=True)

# THE FIX: This correctly moves text, masks, AND audio to the GPU
inputs = inputs.to("cpu")  # Change to "cuda" if you have a GPU and the model is on GPU

print("Processing audio...")
generate_ids = model.generate(**inputs, max_new_tokens=4096)
generate_ids = generate_ids[:, inputs.input_ids.size(1):]

response = processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

print("\n--- Final Output ---")
print(response)