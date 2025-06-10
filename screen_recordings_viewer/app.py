import os
import re
import subprocess
import json
from flask import Flask, render_template, send_from_directory, url_for, abort
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

# Path to the directory where recordings are stored.
# Assumes this 'app.py' is in 'screen_recordings_viewer', and 'recordings' is a sibling to 'screen_recordings_viewer'.
# So, ../recordings/ from the perspective of app.py
RECORDINGS_DIR_RELATIVE_TO_APP = os.path.join('..', 'recordings')
RECORDINGS_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), RECORDINGS_DIR_RELATIVE_TO_APP))
RECORDINGS_DIR_NAME = os.path.basename(RECORDINGS_BASE_DIR)

def get_video_duration_and_size(filepath):
    """Gets video duration using ffprobe and file size."""
    size = 0
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
    else:
        print(f"File not found for size check: {filepath}")
        return 0, 0 # File doesn't exist, so duration and size are 0

    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            filepath
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        
        duration_s = 0
        if 'format' in data and 'duration' in data['format']:
            duration_s = float(data['format']['duration'])
        elif 'streams' in data and data['streams']:
            for stream in data['streams']:
                if stream.get('codec_type') == 'video' and 'duration' in stream:
                    duration_s = float(stream['duration'])
                    break
        return duration_s, size
    except subprocess.TimeoutExpired:
        print(f"ffprobe timed out for {filepath}")
        return 0, size # Return 0 duration on timeout, but still provide size
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error processing {filepath} with ffprobe: {e}. Ensure ffprobe is installed and in PATH.")
        return 0, size # Fallback if ffprobe fails, but still provide size

def format_duration(seconds):
    """Formats duration in seconds to HH:MM:SS or MM:SS string."""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "N/A"
    if seconds == 0:
        return "00:00"
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds_val = divmod(remainder, 60)
    if td.days > 0:
        return f"{td.days}d {hours:02}:{minutes:02}:{seconds_val:02}"
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{seconds_val:02}"
    else:
        return f"{minutes:02}:{seconds_val:02}"

def format_size(size_bytes):
    """Formats size in bytes to a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.1f} GB"

def get_recordings_info():
    """
    Scans session subfolders (YYYYMMDD_HHMMSS) in RECORDINGS_BASE_DIR for 'recording.mp4' files,
    groups them by day, and calculates total duration for each day.
    """
    daily_recordings = defaultdict(lambda: {'files': [], 'total_duration': 0, 'count': 0})
    
    if not os.path.exists(RECORDINGS_BASE_DIR):
        print(f"Recordings directory not found: {RECORDINGS_BASE_DIR}")
        return [], RECORDINGS_BASE_DIR, RECORDINGS_DIR_NAME

    # Regex to match session folder names like YYYYMMDD_HHMMSS
    session_folder_pattern = re.compile(r"^(\d{8})_(\d{6})$")
    video_filename = "recording.mp4"

    for item_name in os.listdir(RECORDINGS_BASE_DIR):
        session_dir_path = os.path.join(RECORDINGS_BASE_DIR, item_name)
        if os.path.isdir(session_dir_path):
            match = session_folder_pattern.match(item_name)
            if match:
                date_str_yyyymmdd = match.group(1) # YYYYMMDD
                # Convert YYYYMMDD to YYYY-MM-DD for consistency and easier parsing
                try:
                    date_obj_from_folder = datetime.strptime(date_str_yyyymmdd, "%Y%m%d")
                    date_key = date_obj_from_folder.strftime("%Y-%m-%d") # Key for grouping
                    time_str_hhmmss = match.group(2) # HHMMSS
                    try:
                        time_obj_from_folder = datetime.strptime(time_str_hhmmss, "%H%M%S")
                        time_formatted = time_obj_from_folder.strftime("%I:%M:%S %p") # e.g., 10:30:15 PM
                    except ValueError:
                        time_formatted = time_str_hhmmss # Fallback to raw HHMMSS

                except ValueError:
                    print(f"Skipping folder with invalid date format: {item_name}")
                    continue

                video_filepath = os.path.join(session_dir_path, video_filename)
                
                if os.path.exists(video_filepath) and os.path.isfile(video_filepath):
                    duration, size = get_video_duration_and_size(video_filepath)
                    
                    # Use session folder name as a unique identifier for the recording in the day view
                    # and to construct the path for serving the file.
                    daily_recordings[date_key]['files'].append({
                        'filename': video_filename, # Actual filename (recording.mp4)
                        'session_folder': item_name, # e.g., 20250609_224319
                        'path': video_filepath,
                        'duration': duration,
                        'duration_formatted': format_duration(duration),
                        'size': size,
                        'size_formatted': format_size(size),
                        'display_name': f"Recording from {time_formatted}", # For display in UI
                        'time_formatted': time_formatted # Store for potential direct use
                    })
                    daily_recordings[date_key]['total_duration'] += duration
                    daily_recordings[date_key]['count'] += 1
                else:
                    print(f"No '{video_filename}' found in session folder: {session_dir_path}")
            
    sorted_days = sorted(daily_recordings.items(), key=lambda item: item[0], reverse=True)
    
    processed_info = []
    for date_key, data in sorted_days:
        try:
            date_obj = datetime.strptime(date_key, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%A, %B %d, %Y")
        except ValueError:
            date_formatted = date_key # Should not happen if date_key is always YYYY-MM-DD

        processed_info.append({
            'date': date_key,
            'date_formatted': date_formatted,
            'count': data['count'],
            'total_duration': data['total_duration'],
            'total_duration_formatted': format_duration(data['total_duration']),
            # Sort recordings within a day by session folder name (chronologically)
            'recordings': sorted(data['files'], key=lambda x: x['session_folder'])
        })
    return processed_info, RECORDINGS_BASE_DIR, RECORDINGS_DIR_NAME

@app.route('/')
def index():
    days_data, base_path, dir_name = get_recordings_info()
    days_summary = [{
        'date': day['date'],
        'date_formatted': day['date_formatted'],
        'count': day['count'],
        'total_duration_formatted': day['total_duration_formatted']
    } for day in days_data]
    return render_template('index.html', 
                           days_with_recordings=days_summary, 
                           recordings_base_path=base_path, 
                           recordings_dir_name=dir_name)

@app.route('/day/<date_str>')
def view_day(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        abort(404, description="Invalid date format. Please use YYYY-MM-DD.")

    all_days_data, _, _ = get_recordings_info()
    day_data = next((day for day in all_days_data if day['date'] == date_str), None)

    date_obj_for_title = datetime.strptime(date_str, "%Y-%m-%d")
    date_formatted_for_title = date_obj_for_title.strftime("%A, %B %d, %Y")

    if not day_data:
        return render_template('day_view.html', 
                               date_str=date_str, 
                               date_formatted=date_formatted_for_title, 
                               recordings=[])
    
    return render_template('day_view.html', 
                           date_str=day_data['date'], 
                           date_formatted=day_data['date_formatted'], 
                           recordings=day_data['recordings'])

@app.route('/recordings/<session_folder_name>/<filename>')
def serve_recording(session_folder_name, filename):
    # Validate session_folder_name format (e.g., YYYYMMDD_HHMMSS)
    session_folder_pattern = re.compile(r"^(\d{8})_(\d{6})$")
    if not session_folder_pattern.match(session_folder_name):
        abort(400, description="Invalid session folder format in URL.")

    if '..' in filename or filename.startswith('/') or filename != "recording.mp4":
        abort(400, description="Invalid or disallowed filename.")

    # Construct the full path to the video file
    # RECORDINGS_BASE_DIR -> session_folder_name -> filename (recording.mp4)
    session_dir_path = os.path.join(RECORDINGS_BASE_DIR, session_folder_name)
    video_filepath = os.path.join(session_dir_path, filename)

    if not os.path.exists(video_filepath) or not os.path.isfile(video_filepath):
        print(f"Attempted to serve non-existent file: {video_filepath}")
        abort(404, description="Recording not found at expected path.")
        
    # Serve the file from the specific session directory
    return send_from_directory(session_dir_path, filename, as_attachment=False)

if __name__ == '__main__':
    if not os.path.exists(RECORDINGS_BASE_DIR):
        print(f"INFO: Recordings directory '{RECORDINGS_BASE_DIR}' does not exist. It will be scanned if created.")
        # For local testing, you might want to create it and add dummy files:
        # os.makedirs(RECORDINGS_BASE_DIR, exist_ok=True)
        # with open(os.path.join(RECORDINGS_BASE_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_00-00-00_dummy.mp4"), "w") as f: f.write("dummy mp4 content")

    print(f"Attempting to serve recordings from: {RECORDINGS_BASE_DIR}")
    # The rest of your app initialization and routes go here...

if __name__ == '__main__':
    # Note: debug=True is for development, not for production
    app.run(debug=True, port=5002)
