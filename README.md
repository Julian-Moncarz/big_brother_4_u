# Big Brother 4 U - Automated Screen Recorder & Viewer

This project provides a complete system for continuously recording a Mac's screen with minimal resource usage and a web interface to easily browse and view the recordings.

It consists of two main components:
1.  **Screen Recorder (`screen_recorder.py`)**: A lightweight Python script that runs in the background, capturing the screen at a low frame rate and resolution.
2.  **Recordings Viewer (`screen_recordings_viewer/`)**: A Flask-based web application that provides a timeline and gallery view for all recorded sessions.

## Features

- **Continuous & Automated Recording**: Uses a macOS `launchd` agent to run automatically on login and restart if it ever stops.
- **4-Hour Recording Cycle**: Automatically stops and saves videos in 4-hour chunks to keep files manageable.
- **Low Resource Usage**: Defaults to 1 FPS and 720p resolution, using minimal CPU and memory.
- **Web-Based Viewer**: Browse recordings through a clean web interface, organized by day.
- **Efficient Storage**: Converts image frames into a highly compressed MP4 video using a two-pass FFmpeg process and cleans up the original frames.
- **Resilient**: Automatically finds and converts incomplete sessions from previous runs upon startup.

## Getting Started

### 1. Prerequisites

- **Homebrew**: For installing packages on macOS. If you don't have it, install it from [brew.sh](https://brew.sh/).
- **Python 3**: Should be pre-installed on modern macOS.

### 2. Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Julian-Moncarz/big_brother_4_u.git
    cd big_brother_4_u
    ```

2.  **Install FFmpeg:**
    This is required for video conversion.
    ```bash
    brew install ffmpeg
    ```

3.  **Set Up Virtual Environments & Dependencies:**
    We use separate virtual environments for the recorder and the viewer for better dependency management.

    *   **Screen Recorder:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        deactivate
        ```

    *   **Recordings Viewer:**
        ```bash
        cd screen_recordings_viewer
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        deactivate
        cd ..
        ```

### 3. Grant macOS Screen Recording Permissions

Before the script can record the screen, you must grant permissions.

1.  Run the script manually once to trigger the permission prompt:
    ```bash
    source venv/bin/activate
    python screen_recorder.py
    ```
2.  You will see a macOS prompt. Click **Open System Settings**.
3.  Go to **Privacy & Security** → **Screen Recording**.
4.  Enable the toggle for **Terminal** (or your preferred terminal application, like iTerm).
5.  You can now stop the manual script with `Ctrl+C`.

## Continuous Operation (Automated Recording)

To make the recorder run automatically in the background, we use a macOS `launchd` agent.

### 1. Create the Launch Agent `.plist` File

Create a file named `com.user.screenrecorder.plist` in `~/Library/LaunchAgents/` with the following content. **Make sure to replace `YOUR_USERNAME` with your actual macOS username.**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.screenrecorder</string>

    <key>ProgramArguments</key>
    <array>
        <!-- IMPORTANT: Replace YOUR_USERNAME with your actual username -->
        <string>/Users/YOUR_USERNAME/path/to/big_brother_4_u/venv/bin/python</string>
        <string>/Users/YOUR_USERNAME/path/to/big_brother_4_u/screen_recorder.py</string>
    </array>

    <key>WorkingDirectory</key>
    <!-- IMPORTANT: Replace YOUR_USERNAME with your actual username -->
    <string>/Users/YOUR_USERNAME/path/to/big_brother_4_u</string>

    <key>RunAtLoad</key>
    <true/> <!-- Start the script when you log in -->

    <key>KeepAlive</key>
    <true/> <!-- Restart the script if it stops for any reason (including the 4-hour cycle) -->

    <key>StandardOutPath</key>
    <string>screen_recorder.log</string>

    <key>StandardErrorPath</key>
    <string>screen_recorder.err</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
    </dict>

    <key>SessionCreate</key>
    <true/>

</dict>
</plist>
```

### 2. Load the Launch Agent

Open Terminal and run the following command to load and start the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.user.screenrecorder.plist
```

The screen recorder will now be running in the background and will automatically start every time you log in.

### Managing the Agent

-   **To stop and unload the agent:**
    ```bash
    launchctl unload ~/Library/LaunchAgents/com.user.screenrecorder.plist
    ```
-   **To check logs:**
    ```bash
    tail -f screen_recorder.log
    tail -f screen_recorder.err
    ```

## Viewing Your Recordings

Run the Flask web app to browse your recordings.

1.  **Navigate to the viewer directory:**
    ```bash
    cd screen_recordings_viewer
    ```

2.  **Activate its virtual environment:**
    ```bash
    source venv/bin/activate
    ```

3.  **Run the Flask app:**
    ```bash
    flask run
    ```

4.  Open your web browser and go to **http://127.0.0.1:5000** to see the viewer.
