# chatapp/tts_processor.py

"""
Separate TTS Processor - Runs in isolated tts_env environment
"""

import os
import sys
import json

def process_tts(text, speaker_wav_path, output_path, language='en'):
    """
    Process TTS in isolated environment
    This runs in tts_env, not main env
    """
    try:
        print(f"🎤 TTS Processor Starting...")
        print(f"   Text: {text[:50]}...")
        print(f"   Speaker WAV: {speaker_wav_path}")
        print(f"   Output: {output_path}")
        print(f"   Language: {language}")
        
        # Import TTS (must be in tts_env)
        from TTS.api import TTS
        print("🤖 Loading TTS model...")
        tts = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            progress_bar=True,
            gpu=False
        )
        
        print("🎵 Generating speech...")
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav_path,
            language=language,
            file_path=output_path
        )
        
        # Verify output
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"✅ Success! Output size: {size} bytes")
            return True
        else:
            print("❌ Output file not created")
            return False
            
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Command line interface
    if len(sys.argv) != 5:
        print("Usage: python tts_processor.py <text> <speaker_wav> <output> <language>")
        sys.exit(1)
    
    text = sys.argv[1]
    speaker_wav = sys.argv[2]
    output = sys.argv[3]
    language = sys.argv[4]
    
    success = process_tts(text, speaker_wav, output, language)
    sys.exit(0 if success else 1)