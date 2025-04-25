# YouTube Video Downloader

## 💡 Overview

**YouTube Video Downloader** is a feature-rich, web-based application built as my final project for **CS50x 2025**. It enables users to easily download **videos or audio** from YouTube in various formats and quality levels — all through a sleek, user-friendly interface.

The project was born out of the idea to create a tool that simplifies downloading media content from YouTube without needing browser extensions, ads, or third-party apps. With this app, users have full control over the format, resolution, and type (audio/video) they want — with just a few clicks.

The application uses:
- **Flask (Python)** as the web server backend
- **yt-dlp** to handle extraction and downloading of YouTube video/audio streams
- **ffmpeg** to merge separate video/audio files into a unified `.mp4`
- **HTML, CSS (Bootstrap), and JavaScript** to create a responsive and modern frontend experience

## 🎥 Video Demo

▶️ Watch the full video demo here: [https://youtu.be/e2Ahp6QTwBU](https://youtu.be/e2Ahp6QTwBU)

## 🚀 Features

- 🎯 **Download videos** in high quality (360p, 720p, 1080p, etc.)
- 🎧 **Extract and download audio only** (MP3/M4A)
- 🔗 **Single-click download experience** — just paste the URL and go!
- 📦 **Auto-merging** of video and audio using `ffmpeg`
- 🧼 Clean, minimal UI built with **Bootstrap**
- ⚙️ Flexible format selection from a list of all available streams
- 🗑️ Automatic cleanup of temporary files after merging
- 🧪 Lightweight, fast, and works locally — no need for hosting

## 📋 How It Works

1. User visits the home page.
2. They paste a valid YouTube URL.
3. The app uses `yt-dlp` to fetch metadata and available formats.
4. User selects a format or resolution for video/audio.
5. Flask backend downloads the selected streams.
6. If video/audio are separate, `ffmpeg` merges them into one file.
7. The merged file is sent to the user as a direct download.
8. Temporary files are deleted to save space.

## 🛠️ Technologies Used

| Category         | Tools & Libraries                     |
|------------------|----------------------------------------|
| **Frontend**     | HTML5, CSS3, JavaScript, Bootstrap     |
| **Backend**      | Python 3.x, Flask                      |
| **Download Tool**| [yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| **Media Processing** | [ffmpeg](https://ffmpeg.org/)         |
| **System**       | Linux (Ubuntu), Git, Shell Scripting   |

## 🧑‍💻 Installation & Setup

Follow these steps to run the app locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/PrinceSuthar0001/cs50-final-project
cd cs50-final-project
```

### 2. Create & Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install `ffmpeg`
- **Linux**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: [Download](https://ffmpeg.org/download.html) and add to PATH

### 5. Run the App
```bash
flask run
```

Then open your browser and go to:
```
http://127.0.0.1:5000
```

## 🎨 UI & Design Decisions

- The app uses **Bootstrap 5** to keep the design responsive and mobile-friendly.
- Format selections are dynamically populated based on `yt-dlp` output.
- The backend merges streams only when necessary, ensuring speed and performance.
- Errors (like unsupported formats or broken URLs) are handled gracefully with user-friendly messages.

## 💡 Why This Project?

I chose this project because it combines multiple real-world skills:

- Web development (Flask, HTML/CSS/JS)
- Media processing (ffmpeg)
- Open-source tools (yt-dlp)
- Working with APIs, streams, and file handling
- Delivering real utility to users

I also wanted to go beyond a static website or pure backend project and create something that interacts with third-party services, processes real data, and delivers something useful and functional.

## 🔄 Future Improvements

Here are a few features I’d like to add in the future:

- ⏳ Real-time progress bar or download status indicator
- 🧩 Playlist download support
- 🌓 Dark Mode toggle for better UX
- 🔁 Download history on the local device
- ☁️ Optional cloud-based version with user login

## 🙋 Author

- **Name**: Prince Suthar  
- **GitHub**: [@PrinceSuthar0001](https://github.com/PrinceSuthar0001)  
- **edX Username**: PrinceSuthar0001  
- **Location**: Hanumangarh, Rajasthan, India  

## 📄 License

This project was built as part of the **CS50x 2025 Final Project**. It is open-source and available for educational use only.
