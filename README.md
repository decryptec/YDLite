# Simple yt-dlp Frontend UI

A web interface for [yt-dlp](https://github.com/yt-dlp/yt-dlp), built with Flask.  
Easily download videos or audio from supported platforms using a clean and minimal UI.

## Features

- Paste video URLs and download with one click
- Choose between **MP3 audio** or **MP4 video**
- Optional flags:
  - Add metadata
  - Download subtitles
  - Embed thumbnail
  - Extract audio
  - Delete file after serving
- Files are downloaded to the host machine and can be kept or auto‑deleted
- Powered by `yt-dlp` and `Flask`

## Requirements

- Python 3.7+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Flask

## Installation

Install dependencies:

```bash
pip install flask yt-dlp
