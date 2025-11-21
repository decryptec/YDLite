# Simple yt-dlp Frontend UI

A lightweight web interface for [yt-dlp](https://github.com/yt-dlp/yt-dlp), built with Flask.  
Quickly download videos or audio from supported platforms using a clean and minimal browser UI.

## Features

- Paste video URLs and download with one click
- Choose between **MP3 audio** or **MP4 video**
- Extra modes:
  - **Extract Info** – show metadata only
  - **Extract Audio** – convert to chosen codec (m4a, mp3, wav)
  - **Best Video (MP4)** – download best available MP4 + M4A
  - **Logger + Progress Hook** – see yt-dlp logs and progress
  - **Filter Videos** – skip videos shorter than a chosen duration
- **auto‑delete files after serving** so the server stays clean
- Runs on your LAN so you can access from other devices
- Powered by `yt-dlp` and `Flask`

## Usage

1. Clone this repository or copy `app.py` into a folder.
2. Install dependencies:

   ```bash
   pip install flask yt-dlp
