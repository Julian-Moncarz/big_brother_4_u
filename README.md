# Auto Screen Recorder

A lightweight Python screen recorder that continuously captures your screen at 1 FPS with low resolution for minimal resource usage.

## Features

- 🎬 Continuous screen recording at customizable FPS (default: 1 FPS)
- 📐 Low resolution recording (default: 640x480) for efficiency
- 💾 Automatic local storage with timestamped sessions
- 🎞️ Optional FFmpeg conversion to MP4 video
- ⚡ Lightweight and fast with minimal CPU/memory usage
- 🛑 Graceful shutdown with Ctrl+C
- 🗂️ Organized output with session folders

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg (for video conversion):**
   ```bash
   brew install ffmpeg
   ```

## Usage

### Basic Usage
```bash
python screen_recorder.py
```

### Custom Settings
```bash
# Record at 2 FPS with higher resolution
python screen_recorder.py --fps 2 --width 1280 --height 720

# Save to custom directory
python screen_recorder.py --output /path/to/recordings

# Skip video conversion (frames only)
python screen_recorder.py --no-convert
```

### Command Line Options

- `--fps`: Frames per second (default: 1)
- `--width`: Video width in pixels (default: 640)
- `--height`: Video height in pixels (default: 480)
- `--output`: Output directory (default: "recordings")
- `--no-convert`: Skip FFmpeg video conversion

## How It Works

1. **Capture**: Takes screenshots using PIL/Pillow at specified intervals
2. **Compress**: Resizes and compresses images for minimal storage
3. **Store**: Saves frames in timestamped session folders
4. **Convert**: Uses FFmpeg to create MP4 videos from frames
5. **Cleanup**: Optionally removes individual frames after video creation

## Output Structure

```
recordings/
├── 20240609_195430/          # Session timestamp
│   ├── frame_000001.jpg      # Individual frames
│   ├── frame_000002.jpg
│   ├── ...
│   └── recording.mp4         # Final video
└── 20240609_203015/          # Another session
    └── ...
```

## Performance

- **CPU Usage**: ~1-2% on modern Macs
- **Memory**: ~50-100MB
- **Storage**: ~1-5MB per hour (depending on resolution/content)
- **1 FPS Recording**: Captures 3,600 frames per hour

## macOS Permissions

On first run, macOS will request screen recording permissions:
1. Go to **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Screen Recording** from the left sidebar
3. Check the box next to **Terminal** (or your Python environment)

## Tips

- **Continuous Recording**: Run in background with `nohup python screen_recorder.py &`
- **Auto-Start**: Add to your shell profile or create a LaunchAgent
- **Storage Management**: Regularly clean old recordings to save disk space
- **Quality vs Size**: Increase resolution/FPS for better quality, decrease for smaller files

## Troubleshooting

- **Permission Denied**: Grant screen recording permissions in System Preferences
- **FFmpeg Not Found**: Install with `brew install ffmpeg`
- **High CPU Usage**: Reduce FPS or resolution
- **Large Files**: Enable auto-cleanup of frames after video conversion
