# chatapp/tts_voice.py

"""
TTS Voice Module - Compatibility Layer
Checks TTS availability in main environment
For actual processing, use tts_processor.py in tts_env
"""

import os
import sys

# Global variables
TTS_AVAILABLE = False
_tts_instance = None

def check_tts_in_main_env():
    """
    Check if TTS is available in MAIN environment
    (Not recommended - use separate tts_env instead)
    """
    try:
        import TTS
        print("✅ TTS found in main environment")
        return True
    except ImportError:
        print("⚠️ TTS not in main environment (expected - use tts_env)")
        return False

def check_tts_env_exists():
    """
    Check if separate TTS environment exists
    This is the RECOMMENDED approach
    """
    from pathlib import Path
    
    # Get project root (assuming this file is in chatapp/)
    project_root = Path(__file__).resolve().parent.parent
    tts_env_path = project_root / 'tts_env'
    tts_python = tts_env_path / 'bin' / 'python'
    
    if tts_env_path.exists() and tts_python.exists():
        print(f"✅ TTS environment found at: {tts_env_path}")
        return True
    else:
        print(f"⚠️ TTS environment not found at: {tts_env_path}")
        print("   It will be auto-created on first use")
        return False

def get_tts_instance():
    """
    Get TTS instance from main environment
    
    WARNING: This is NOT the recommended approach!
    Use subprocess with tts_env instead (see views.py)
    
    This function kept for backward compatibility only.
    """
    global _tts_instance, TTS_AVAILABLE
    
    if not TTS_AVAILABLE:
        print("❌ TTS not available in main environment")
        print("💡 Use tts_env subprocess instead (automatic in views.py)")
        return None
    
    if _tts_instance is not None:
        print("♻️ Reusing existing TTS instance")
        return _tts_instance
    
    try:
        print("🔄 Loading TTS model in main environment...")
        print("⚠️ WARNING: This may cause dependency conflicts!")
        print("💡 Recommended: Use separate tts_env (automatic)")
        
        from TTS.api import TTS
        
        _tts_instance = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            progress_bar=True,
            gpu=False
        )
        
        print("✅ TTS model loaded (not recommended approach)")
        return _tts_instance
        
    except Exception as e:
        print(f"❌ Failed to load TTS in main env: {e}")
        print("💡 Solution: Use subprocess method (automatic in views.py)")
        return None

# Initialize on module load
print("\n" + "="*60)
print("🎤 TTS Voice Module Initializing...")
print("="*60)

# Check main environment (not recommended)
TTS_AVAILABLE = check_tts_in_main_env()

# Check separate TTS environment (recommended)
tts_env_exists = check_tts_env_exists()

if TTS_AVAILABLE:
    print("⚠️ WARNING: TTS in main environment detected")
    print("   This may cause dependency conflicts")
    print("   Recommended: Use separate tts_env")
elif tts_env_exists:
    print("✅ Using separate TTS environment (RECOMMENDED)")
    print("   Processing via subprocess (automatic)")
else:
    print("ℹ️ TTS environment will be auto-created on first use")

print("="*60 + "\n")

# Export
__all__ = [
    'TTS_AVAILABLE',
    'get_tts_instance',
    'check_tts_env_exists',
    'check_tts_in_main_env'
]