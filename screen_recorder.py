#!/usr/bin/env python3
"""
Lightweight Auto Screen Recorder for macOS
Captures screenshots at 1fps and saves them locally with optional video conversion.
"""

import os
import time
import threading
from datetime import datetime
from PIL import ImageGrab, Image
import argparse
import signal
import sys

class ScreenRecorder:
    def __init__(self, fps=0.5, resolution=(1280, 720), output_dir="recordings", auto_convert=True):
        self.fps = fps
        self.resolution = resolution
        self.output_dir = output_dir
        self.auto_convert = auto_convert
        self.recording = False
        self.frames = []
        self.current_session = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Attempt to recover any incomplete sessions from previous runs
        self.recover_incomplete_sessions()
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Stopping recorder...")
        self.stop_recording()
        sys.exit(0)
    
    def capture_screenshot(self):
        """Capture and resize screenshot"""
        try:
            # Capture full screen
            screenshot = ImageGrab.grab()
            
            # Resize to target resolution for efficiency
            screenshot = screenshot.resize(self.resolution, Image.Resampling.LANCZOS)
            
            return screenshot
        except Exception as e:
            print(f"❌ Error capturing screenshot: {e}")
            return None
    
    def save_frame(self, frame, session_dir, frame_number):
        """Save individual frame"""
        filename = f"frame_{frame_number:06d}.jpg"
        filepath = os.path.join(session_dir, filename)
        
        # Convert to RGB to remove alpha channel, which JPEG doesn't support
        rgb_frame = frame.convert("RGB")
        # Save with high compression for smaller file size
        rgb_frame.save(filepath, "JPEG", quality=60, optimize=True)
        return filepath
    
    def recording_loop(self):
        """Main recording loop"""
        frame_number = 0
        session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.output_dir, session_name)
        os.makedirs(session_dir, exist_ok=True)
        
        self.current_session = session_dir
        print(f"📁 Recording to: {session_dir}")
        
        while self.recording:
            start_time = time.time()
            
            # Capture screenshot
            frame = self.capture_screenshot()
            if frame:
                # Save frame
                self.save_frame(frame, session_dir, frame_number)
                self.frames.append(frame_number)
                frame_number += 1
                
                if frame_number % 30 == 0 and frame_number > 0:  # Progress update every 30 frames
                    print(f"📸 Captured {frame_number} frames")
            
            # Maintain target FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, (1.0 / self.fps) - elapsed)
            time.sleep(sleep_time)
    
    def start_recording(self):
        """Start the recording process"""
        if self.recording:
            print("⚠️  Already recording!")
            return
        
        print(f"🎬 Starting screen recorder...")
        print(f"   📐 Resolution: {self.resolution[0]}x{self.resolution[1]}")
        print(f"   🎯 FPS: {self.fps}")
        print(f"   📂 Output: {self.output_dir}")
        print(f"   🔄 Auto-convert: {self.auto_convert}")
        print("   Press Ctrl+C to stop")
        
        self.recording = True
        self.frames = []
        
        # Start recording in separate thread
        self.recording_thread = threading.Thread(target=self.recording_loop)
        self.recording_thread.daemon = True
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop recording and optionally convert to video"""
        if not self.recording:
            return
        
        self.recording = False
        
        # Wait for recording thread to finish
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join()
        
        print(f"✅ Recording stopped. Captured {len(self.frames)} frames.")
        
        if self.auto_convert and len(self.frames) > 0 and self.current_session:
            self.convert_to_video(self.current_session)
    
    def convert_to_video(self, session_dir):
        """
        Convert frames to a highly compressed MP4 video using a two-pass FFmpeg process.
        1. Generate a 256-color palette from the frames.
        2. Use the palette to create a smaller video file.
        """
        if not os.path.isdir(session_dir):
            print(f"❌ Session directory not found: {session_dir}")
            return

        frame_files_exist = any(f.startswith('frame_') and f.endswith('.jpg') for f in os.listdir(session_dir))
        if not frame_files_exist:
            print(f"ℹ️ No frames found in {session_dir} to convert.")
            return
        
        print(f"🎞️  Converting frames to video for session: {session_dir}...")
        
        input_pattern = os.path.join(session_dir, "frame_%06d.jpg")
        palette_file = os.path.join(session_dir, "palette.png")
        output_file = os.path.join(session_dir, "recording.mp4")
        
        try:
            # --- Pass 1: Generate color palette ---
            print("   -> Step 1/2: Generating color palette...")
            cmd_palette = [
                "ffmpeg", "-y",
                "-framerate", str(self.fps),
                "-i", input_pattern,
                "-vf", "palettegen=stats_mode=single",
                palette_file
            ]
            import subprocess
            subprocess.run(cmd_palette, capture_output=True, text=True, check=True)

            # --- Pass 2: Create video using the palette ---
            print("   -> Step 2/2: Encoding video...")
            cmd_video = [
                "ffmpeg", "-y",
                "-framerate", str(self.fps),
                "-i", input_pattern,
                "-i", palette_file,
                "-lavfi", "paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
                "-c:v", "libx264",
                "-preset", "medium",       # Slower preset for better compression
                "-tune", "stillimage",    # Optimized for static content like screen text
                "-crf", "30",             # Higher CRF for more compression (lower quality)
                "-pix_fmt", "yuv420p",      # Compatibility
                output_file
            ]
            result_video = subprocess.run(cmd_video, capture_output=True, text=True)

            if result_video.returncode == 0:
                print(f"✅ Video saved: {output_file}")
                video_size = os.path.getsize(output_file) / (1024 * 1024)
                print(f"📊 Video size: {video_size:.1f} MB")
                
                # Clean up frames automatically
                self.cleanup_frames(session_dir)
            else:
                print(f"❌ FFmpeg error during video encoding: {result_video.stderr}")

        except FileNotFoundError:
            print("❌ FFmpeg not found. Please install FFmpeg to convert to video.")
            print("   Install with: brew install ffmpeg")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error during palette generation: {e.stderr}")
        except Exception as e:
            print(f"❌ Error during conversion: {e}")
        finally:
            # --- Cleanup ---
            if os.path.exists(palette_file):
                os.remove(palette_file)
                print(f"🗑️  Cleaned up temporary palette file.")
    
    def recover_incomplete_sessions(self):
        """Scan output directory for incomplete sessions and try to convert them."""
        print(f"🔎 Checking for incomplete sessions in {self.output_dir}...")
        for session_name in os.listdir(self.output_dir):
            session_path = os.path.join(self.output_dir, session_name)
            if os.path.isdir(session_path):
                has_frames = any(f.startswith('frame_') and f.endswith('.jpg') for f in os.listdir(session_path))
                has_video = os.path.exists(os.path.join(session_path, 'recording.mp4'))
                
                if has_frames and not has_video:
                    print(f"🛠️ Found incomplete session: {session_name}. Attempting conversion.")
                    self.convert_to_video(session_path)
                elif has_frames and has_video:
                    print(f"ℹ️ Session {session_name} already has a video. Checking if frames need cleanup.")
                    # If video exists but frames are still there, it implies cleanup might have failed or was skipped.
                    # We can offer to clean them up here, or just proceed with the new logic which cleans up after conversion.
                    # For now, let's assume convert_to_video will handle cleanup if it runs again.
                    # Or, more directly, we can call cleanup if video exists and frames exist.
                    self.cleanup_frames(session_path) # Ensure cleanup if video exists and frames are present

        print("✅ Finished checking for incomplete sessions.")

    def cleanup_frames(self, session_dir):
        """Remove individual frame files after video creation from a given session directory."""
        print(f"🗑️  Cleaning up frame files in {session_dir}...")
        try:
            frame_files = [f for f in os.listdir(session_dir) if f.startswith('frame_') and f.endswith('.jpg')]
            if not frame_files:
                print(f"ℹ️ No frame files to clean up in {session_dir}.")
                return

            for frame_file in frame_files:
                os.remove(os.path.join(session_dir, frame_file))
            print(f"✅ Cleaned up {len(frame_files)} frame files from {session_dir}")
        except Exception as e:
            print(f"❌ Error cleaning up frames in {session_dir}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Lightweight Auto Screen Recorder")
    parser.add_argument("--fps", type=float, default=1, help="Frames per second (default: 1)")
    parser.add_argument("--width", type=int, default=1280, help="Video width (default: 1280)")
    parser.add_argument("--height", type=int, default=720, help="Video height (default: 720)")
    parser.add_argument("--output", type=str, default="recordings", help="Output directory")
    parser.add_argument("--no-convert", action="store_true", help="Skip video conversion")
    
    args = parser.parse_args()
    
    # Create recorder instance
    recorder = ScreenRecorder(
        fps=args.fps,
        resolution=(args.width, args.height),
        output_dir=args.output,
        auto_convert=not args.no_convert
    )
    
    try:
        # Start recording
        recorder.start_recording()

        # Keep main thread alive, but exit after 4 hours
        start_time = time.time()
        four_hours = 4 * 60 * 60  # 14400 seconds

        while recorder.recording:
            if time.time() - start_time > four_hours:
                print("⏳ 4-hour limit reached. Shutting down to restart.")
                recorder.stop_recording()
                break  # Exit the loop, allowing the script to terminate
            time.sleep(1)

    except KeyboardInterrupt:
        pass  # Handled by signal handler

if __name__ == "__main__":
    main()
