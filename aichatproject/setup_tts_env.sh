# Create scripts directory
mkdir -p ~/Documents/Myskills/my_ml_service/backend/aichatproject/scripts

# Create setup script
cat > ~/Documents/Myskills/my_ml_service/backend/aichatproject/scripts/setup_tts_env.sh << 'SCRIPT_END'
#!/bin/bash

# setup_tts_env.sh - Auto TTS Environment Setup

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="tts_env"
ENV_PATH="$PROJECT_ROOT/$ENV_NAME"

echo "🔧 TTS Environment Setup"
echo "Project Root: $PROJECT_ROOT"
echo "Environment Path: $ENV_PATH"
echo ""

# Check if environment exists
if [ -d "$ENV_PATH" ]; then
    echo "✅ TTS environment already exists at: $ENV_PATH"
    exit 0
fi

echo "📦 Creating TTS environment..."

# Detect Python version (prefer 3.11, fallback to 3.10)
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "Using Python 3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo "Using Python 3.10"
else
    PYTHON_CMD="python3"
    echo "Using default Python 3"
fi

# Create virtual environment
$PYTHON_CMD -m venv "$ENV_PATH"

# Activate environment
source "$ENV_PATH/bin/activate"

echo "🔄 Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "🔥 Installing PyTorch (CPU)..."
pip install torch transformers librosa pyannote.audio

echo "🔍 Installing Django (for subprocess compatibility)..."
pip install Django



echo ""
echo "🎉 TTS environment setup complete!"
echo "Location: $ENV_PATH"
echo "Activate with: source $ENV_PATH/bin/activate"

deactivate
SCRIPT_END

# Make executable
chmod +x ~/Documents/Myskills/my_ml_service/backend/aichatproject/scripts/setup_tts_env.sh