from flask import Flask, render_template, request, send_file, jsonify
from yt_dlp import YoutubeDL
import os
import uuid
import subprocess
import re
import shutil
from datetime import datetime, timedelta
import time
import threading

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
CLEANUP_INTERVAL = 3600  # 1 hour
download_progress = {}

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def is_valid_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    return bool(re.match(youtube_regex, url))

def cleanup_old_files():
    """Clean up files older than 1 hour"""
    current_time = datetime.now()
    for filename in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if current_time - file_time > timedelta(seconds=CLEANUP_INTERVAL):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error cleaning up file {filename}: {e}")

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        if not is_valid_youtube_url(url):
            return render_template('index.html', error="Invalid YouTube URL")
            
        try:
            with YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                thumbnail = info.get('thumbnail')
                title = info.get('title')

                # Separate video and audio formats
                video_formats = []
                audio_formats = []
                
                for f in formats:
                    # Check if it has video and/or audio
                    has_video = f.get('vcodec') != 'none'
                    has_audio = f.get('acodec') != 'none'
                    
                    if has_video:
                        resolution = f.get('height', 0)
                        if resolution > 0:  # Only add formats with valid resolution
                            # Ensure all numeric values have defaults to avoid NoneType comparison
                            video_formats.append({
                                'format_id': f['format_id'],
                                'resolution': f"{resolution}p",
                                'ext': f['ext'],
                                'is_audio': False,
                                'filesize': f.get('filesize') or f.get('filesize_approx') or 0,
                                'height': resolution or 0,
                                'tbr': f.get('tbr') or 0  # Video bitrate with default value
                            })
                    elif has_audio:
                        audio_formats.append({
                            'format_id': f['format_id'],
                            'resolution': "Audio Only",
                            'ext': f['ext'],
                            'is_audio': True,
                            'filesize': f.get('filesize') or f.get('filesize_approx') or 0,
                            'abr': f.get('abr') or 0  # Audio bitrate with default value
                        })
                
                # Sort video formats by resolution and bitrate
                video_formats = sorted(video_formats, key=lambda x: (x['height'] or 0, x['tbr'] or 0), reverse=True)
                
                # Group video formats by resolution, keeping only the highest bitrate for each
                grouped_video_formats = {}
                for fmt in video_formats:
                    res = fmt['resolution']
                    if res not in grouped_video_formats:
                        grouped_video_formats[res] = fmt
                
                # Convert back to list
                video_formats = list(grouped_video_formats.values())
                
                # Sort audio formats by bitrate (highest quality first)
                audio_formats = sorted(audio_formats, key=lambda x: x['abr'] or 0, reverse=True)
                
                # Find the best m4a audio format
                best_m4a_audio = None
                for fmt in audio_formats:
                    if fmt['ext'] == 'm4a':
                        best_m4a_audio = fmt
                        break
                
                # If no m4a format is found, use the best available audio format
                if not best_m4a_audio and audio_formats:
                    best_m4a_audio = audio_formats[0]
                
                # Combine formats for template
                all_formats = {
                    'video': video_formats,
                    'best_audio': best_m4a_audio
                }

                return render_template('index.html', url=url, title=title, thumbnail=thumbnail, formats=all_formats)

        except Exception as e:
            print("Error:", e)
            return render_template('index.html', error=str(e))

    return render_template('index.html')

@app.route('/merge_status/<download_id>', methods=['GET'])
def merge_status(download_id):
    """Return the merge status for a specific download"""
    if download_id in download_progress:
        return jsonify(download_progress[download_id])
    return jsonify({"status": "unknown", "progress": 0})

@app.route('/download', methods=['POST'])
def download():
    if not check_ffmpeg():
        return "ffmpeg is not installed. Please install ffmpeg to use this service.", 500

    url = request.form['url']
    if not is_valid_youtube_url(url):
        return "Invalid YouTube URL", 400

    video_format_id = request.form['video_format_id']
    
    # Create a unique download ID
    download_id = str(uuid.uuid4())
    
    # Store download ID in response headers so frontend can track progress
    response_headers = {'X-Download-ID': download_id}
    
    # Create a directory for this download
    session_dir = os.path.join(DOWNLOAD_FOLDER, download_id)
    os.makedirs(session_dir, exist_ok=True)

    # Get video info to use for final filename
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            # Clean filename
            title = re.sub(r'[^\w\-. ]', '_', title)
    except Exception:
        title = 'video'

    # File paths
    video_output = os.path.join(session_dir, "video")
    audio_output = os.path.join(session_dir, "audio")
    final_output = os.path.join(DOWNLOAD_FOLDER, f"{title}_{download_id}.mp4")

    # Create a thread to handle downloading and merging
    def process_download():
        try:
            download_progress[download_id] = {"status": "downloading", "progress": 0}
            
            # Get best audio format
            with YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                # Find the best m4a audio format
                audio_formats = []
                for f in formats:
                    has_audio = f.get('acodec') != 'none'
                    has_video = f.get('vcodec') != 'none'
                    
                    if has_audio and not has_video:
                        audio_formats.append({
                            'format_id': f['format_id'],
                            'ext': f['ext'],
                            'abr': f.get('abr') or 0
                        })
                
                # Sort audio formats by bitrate
                audio_formats = sorted(audio_formats, key=lambda x: x['abr'], reverse=True)
                
                # Find best m4a audio
                audio_format_id = None
                for fmt in audio_formats:
                    if fmt['ext'] == 'm4a':
                        audio_format_id = fmt['format_id']
                        break
                
                # If no m4a found, use best audio format
                if not audio_format_id and audio_formats:
                    audio_format_id = audio_formats[0]['format_id']
                    
                if not audio_format_id:
                    raise ValueError("No suitable audio format found")

            # Start download threads for faster parallel processing
            download_progress[download_id] = {"status": "downloading", "progress": 25}
            
            video_download_thread = threading.Thread(
                target=download_media,
                args=(url, video_format_id, f"{video_output}.%(ext)s")
            )
            
            audio_download_thread = threading.Thread(
                target=download_media,
                args=(url, audio_format_id, f"{audio_output}.%(ext)s")
            )
            
            # Start downloads in parallel
            video_download_thread.start()
            audio_download_thread.start()
            
            # Wait for both downloads to complete
            video_download_thread.join()
            audio_download_thread.join()
            
            download_progress[download_id] = {"status": "downloaded", "progress": 50}

            # Find the downloaded files
            video_file = next((os.path.join(session_dir, f) for f in os.listdir(session_dir) if f.startswith("video.")), None)
            audio_file = next((os.path.join(session_dir, f) for f in os.listdir(session_dir) if f.startswith("audio.")), None)

            if not video_file or not audio_file:
                download_progress[download_id] = {"status": "failed", "progress": 0, "error": "Downloaded files not found"}
                raise FileNotFoundError("Downloaded video or audio file not found")

            # Check file sizes
            if os.path.getsize(video_file) + os.path.getsize(audio_file) > MAX_FILE_SIZE:
                download_progress[download_id] = {"status": "failed", "progress": 0, "error": "File size limit exceeded"}
                raise ValueError("Combined file size exceeds maximum limit")

            # Merge video and audio using helper function with progress tracking
            success = merge_with_progress(video_file, audio_file, final_output, download_id)
            
            if not success:
                raise Exception("Merging failed")
            
            # Schedule cleanup
            def cleanup_files():
                time.sleep(CLEANUP_INTERVAL)
                try:
                    # Remove the temporary directory and merged file
                    if download_id in download_progress:
                        del download_progress[download_id]
                    shutil.rmtree(session_dir, ignore_errors=True)
                    if os.path.exists(final_output):
                        os.remove(final_output)
                except Exception as e:
                    print(f"Error cleaning up download files: {e}")

            cleanup_thread = threading.Thread(target=cleanup_files, daemon=True)
            cleanup_thread.start()

        except Exception as e:
            # Clean up any partial downloads
            try:
                download_progress[download_id] = {"status": "failed", "progress": 0, "error": str(e)}
                shutil.rmtree(session_dir, ignore_errors=True)
                if os.path.exists(final_output):
                    os.remove(final_output)
            except Exception as cleanup_error:
                print(f"Error cleaning up failed download: {cleanup_error}")

    # Start the download process in a background thread
    download_thread = threading.Thread(target=process_download)
    download_thread.daemon = True
    download_thread.start()
    
    # Return a response with the download ID and file path
    # The actual file will be served via a separate endpoint once processing is complete
    return jsonify({
        "download_id": download_id,
        "filename": f"{title}.mp4",
        "status": "processing"
    }), 200, response_headers

@app.route('/get_file/<download_id>', methods=['GET'])
def get_file(download_id):
    try:
        # Check if download exists and is complete
        if download_id not in download_progress:
            return jsonify({"error": "Download not found"}), 404
        
        if download_progress[download_id]['status'] != 'completed':
            return jsonify({"error": "Download not complete"}), 400
        
        # Get video title for the filename
        title = "video"
        for filename in os.listdir(DOWNLOAD_FOLDER):
            if download_id in filename and filename.endswith(".mp4"):
                file_path = os.path.join(DOWNLOAD_FOLDER, filename)
                title = filename.replace(f"_{download_id}.mp4", "")
                break
        else:
            return jsonify({"error": "File not found"}), 404
        
        # Get original filename or use download ID
        safe_filename = f"{title}.mp4".replace('"', '_').replace("'", "_")
        
        # Read file and send with appropriate headers
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        response = app.response_class(
            file_data,
            mimetype="video/mp4"
        )
        
        # Add headers that strongly enforce download behavior
        file_size = os.path.getsize(file_path)
        response.headers["Content-Length"] = str(file_size)
        response.headers["Content-Type"] = "video/mp4"
        response.headers["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error serving file: {str(e)}")
        return jsonify({"error": "Server error"}), 500

# Helper function to download media
def download_media(url, format_id, output_template):
    ydl_opts = {
        'format': format_id,
        'outtmpl': output_template,
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Helper function to merge video and audio with progress tracking
def merge_with_progress(video_file, audio_file, output_file, download_id):
    download_progress[download_id] = {"status": "preparing", "progress": 0}
    
    try:
        # Get video duration for progress calculation
        probe_cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', video_file
        ]
        total_duration = float(subprocess.check_output(probe_cmd).decode('utf-8').strip())
        
        # Prepare FFmpeg command
        command = [
            'ffmpeg', '-i', video_file, '-i', audio_file,
            '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
            '-movflags', 'faststart',  # Optimize for web streaming
            '-threads', '4',  # Use multiple threads for faster processing
            '-y',  # Overwrite output file if it exists
            '-progress', 'pipe:1',  # Output progress information
            output_file
        ]
        
        download_progress[download_id] = {"status": "merging", "progress": 0}
        
        # Run FFmpeg with progress tracking
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Process output to track progress
        for line in process.stdout:
            if 'out_time_ms=' in line:
                # Extract time in microseconds
                time_str = line.strip().split('=')[1]
                if time_str.isdigit():
                    current_time = int(time_str) / 1000000  # Convert to seconds
                    percent = min(int((current_time / total_duration) * 100), 100)
                    download_progress[download_id] = {"status": "merging", "progress": percent}
        
        # Wait for process to finish
        process.wait()
        
        if process.returncode == 0:
            download_progress[download_id] = {"status": "completed", "progress": 100}
            return True
        else:
            download_progress[download_id] = {"status": "failed", "progress": 0}
            return False
    
    except Exception as e:
        print(f"Error during merging: {e}")
        download_progress[download_id] = {"status": "failed", "progress": 0, "error": str(e)}
        return False

if __name__ == '__main__':
    # Start cleanup thread
    def cleanup_thread():
        while True:
            cleanup_old_files()
            time.sleep(CLEANUP_INTERVAL)

    threading.Thread(target=cleanup_thread, daemon=True).start()
    app.run(debug=True)
