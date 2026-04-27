import subprocess
import json
import os
from django.conf import settings

def run_diarization(audio_path):
    subprocess.run([
        "./diar_env/bin/python",
        "diarize.py",
        audio_path
    ])

def run_qwen(audio_path):
    subprocess.run([
        "./qwen_env/bin/python",
        "qwen_audio.py",
        audio_path
    ])


def run_audio_script(audio_path):
    command = [
        str(os.path.join(settings.BASE_DIR, "diar_env/bin/python")),   # 👈 IMPORTANT
        str(os.path.join(settings.BASE_DIR,  'qwen_audio_pyannote.py')),
        audio_path
    ]
    print(f"Running command: {' '.join(command)}")


    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )
    result=subprocess.run([
        "./qwen_env/bin/python",
        "qwen_audio.py",
        audio_path
    ])
    print("Script STDOUT:", result.stdout)
    print("Script STDERR:", result.stderr)

    if result.returncode != 0:
        return {
            "status": "error",
            "error": result.stderr
        }

    try:
        output = result.stdout.split("--- Final JSON Output ---")[-1].strip()
        parsed = json.loads(output)

        return {
            "status": "success",
            "data": parsed
        }
    except Exception as e:
        return {
            "status": "parse_error",
            "raw": result.stdout,
            "error": str(e)
        }
    

# command = [
#         str(os.path.join(settings.BASE_DIR, "tts_env/bin/python")),   # 👈 IMPORTANT
#         str(os.path.join(settings.BASE_DIR,  'qwen_audio_pyannote.py')),
#         audio_path
#     ]