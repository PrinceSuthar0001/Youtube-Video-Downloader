@echo off
echo Setting up your Flask YouTube Downloader...

python -m venv venv
call venv\Scripts\activate

echo Virtual environment activated.
pip install --upgrade pip
pip install Flask yt-dlp

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo "⚠️  ffmpeg is not installed or not in your PATH."
    echo "Please install ffmpeg manually from https://ffmpeg.org/download.html"
) else (
    echo "✅ ffmpeg is installed."
)

echo Setup complete. To run the app: venv\Scripts\activate && python app.py
pause