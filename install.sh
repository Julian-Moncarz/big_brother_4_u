#!/bin/bash

echo "🚀 Installing Auto Screen Recorder..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "📹 FFmpeg not found. Installing via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "🍺 Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    brew install ffmpeg
else
    echo "✅ FFmpeg already installed"
fi

# Make the main script executable
chmod +x screen_recorder.py

echo "✅ Installation complete!"
echo ""
echo "🎬 To start recording:"
echo "   python screen_recorder.py"
echo ""
echo "📖 For more options:"
echo "   python screen_recorder.py --help"
echo ""
echo "⚠️  Note: You may need to grant screen recording permissions in System Preferences."
