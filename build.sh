#!/usr/bin/env bash
set -o errexit

echo "🔨 Starting build process..."

# Install main requirements
echo "📦 Installing main requirements..."
pip install -r requirements.txt

# Setup TTS environment (auto-creates if needed)
echo "🎤 Setting up TTS environment..."
bash scripts/setup_tts_env.sh

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "🗄️ Running migrations..."
python manage.py migrate

echo "✅ Build complete!"