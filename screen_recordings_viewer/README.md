# Screen Recordings Viewer

A simple web application to view screen recordings grouped by day.

## Setup

1.  Ensure you have Python 3 installed.
2.  Navigate to the `screen_recordings_viewer` directory:
    ```bash
    cd /Users/julianmoncarz/screen_recorder/screen_recordings_viewer
    ```
3.  Create and activate a Python virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate 
    ```
    (On Windows, use `venv\Scripts\activate`)
4.  Install dependencies into the virtual environment:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Install FFmpeg**: This application uses `ffprobe` (part of FFmpeg) to determine video durations. If FFmpeg is not installed or `ffprobe` is not in your system's PATH, video durations will not be displayed. You can download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
4.  Place your screen recordings in a folder named `recordings` in the parent directory of this web app (i.e., at `/Users/julianmoncarz/screen_recorder/recordings/`). Recordings should be in `.mp4` format and ideally named with a timestamp, e.g., `YYYY-MM-DD_HH-MM-SS.mp4`.

## Running the Application

1.  Navigate to the `screen_recordings_viewer` directory (if not already there):
    ```bash
    cd /Users/julianmoncarz/screen_recorder/screen_recordings_viewer
    ```
2.  Activate the virtual environment (if not already active):
    ```bash
    source venv/bin/activate
    ```
3.  Run the Flask application:
    ```bash
    flask run
    ```
    Or, to run it directly using the Python interpreter from the venv (which is what `if __name__ == '__main__':` in `app.py` uses):
    ```bash
    python app.py
    ```
    The application will start, and you should see output indicating it's running (e.g., `* Running on http://0.0.0.0:5001/`).
4.  Open your web browser and go to `http://127.0.0.1:5001`.

## Structure

-   `app.py`: The main Flask application logic.
-   `templates/`: Contains HTML templates.
    -   `index.html`: Homepage displaying a timeline of days with recordings.
    -   `day_view.html`: Page displaying recordings for a specific day.
-   `static/`: Contains static files (CSS, JavaScript).
    -   `style.css`: Basic styling for the web pages.
-   `requirements.txt`: Python dependencies.
