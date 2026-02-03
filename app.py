import threading
from flask import Flask, request, render_template_string, send_file, abort
import yt_dlp
import os
import shutil
import validators

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

cleanup_lock = threading.Lock()

def safe_cleanup():
    with cleanup_lock:
        for fname in os.listdir(DOWNLOAD_DIR):
            if fname.lower() == "readme.md":
                continue
            fpath = os.path.join(DOWNLOAD_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                elif os.path.isdir(fpath):
                    shutil.rmtree(fpath)
            except Exception as e:
                print(f"Cleanup error: {e}")

def build_common_opts(download_path, include_subs=False):
    opts = {
        'outtmpl': download_path,
        'postprocessors': [
            {'key': 'FFmpegMetadata'},
            {'key': 'EmbedThumbnail'},
        ],
        'writethumbnail': True,
        'noplaylist': True,
        'retries': 5,
        'fragment_retries': 5,
        'socket_timeout': 15,
        'http_chunk_size': 1048576,
        'concurrent_fragment_downloads': 3,
    }
    if include_subs:
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['en']
    return opts

def get_final_filepath(info, ydl):
    if "requested_downloads" in info and info["requested_downloads"]:
        return info["requested_downloads"][0]["filepath"]
    return ydl.prepare_filename(info)
    
html = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Downloader</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 0;
               display: flex; justify-content: center; align-items: flex-start;
               min-height: 100vh; }
        .container { background: white; margin-top: 40px; padding: 25px;
                     border-radius: 12px; width: 90%; max-width: 480px;
                     box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h1 { text-align: center; font-size: 1.8rem; margin-bottom: 20px; }
        label { font-size: 1.1rem; display: block; margin-top: 12px; }
        input[type="text"], select { width: 100%; padding: 12px; font-size: 1.1rem;
                                    margin-top: 6px; border-radius: 8px; border: 1px solid #ccc; }
        button { width: 100%; padding: 14px; margin-top: 20px; font-size: 1.2rem;
                 background: #007bff; color: white; border: none; border-radius: 8px; cursor: pointer; }
        button:hover { background: #0056cc; }
        .settings { margin-left: 15px; padding: 10px 0; }
    </style>
    <script>
    function showSettings(mode) {
        document.querySelectorAll('[id$="-settings"]').forEach(div => div.style.display = "none");
        if (mode) {
            document.getElementById(mode + "-settings").style.display = "block";
        }
    }
    </script>
</head>
<body>
    <div class="container">
        <h1>YouTube Downloader</h1>
        <form method="POST">
            <label>
                <input type="radio" name="mode" value="audio" onclick="showSettings('audio')" required>
                Extract Audio
            </label>
            <div id="audio-settings" class="settings" style="display:none;">
                <label>Codec:</label>
                <select name="codec">
                    <option value="m4a">m4a</option>
                    <option value="mp3">mp3</option>
                    <option value="wav">wav</option>
                </select>
                <label>Include Subs if Any:</label>
                <input type="checkbox" name="include_subs" value="true">
            </div>

            <label>
                <input type="radio" name="mode" value="best_video" onclick="showSettings('best_video')">
                Download Best Video (MP4)
            </label>
            <div id="best_video-settings" class="settings" style="display:none;">
                <p>Downloads best available MP4 video + M4A audio.</p>
                <label>Include Subs if Any:</label>
                <input type="checkbox" name="include_subs" value="true">
            </div>

            <label>YouTube URL:</label>
            <input type="text" name="URL" placeholder="https://youtube.com/..." required>

            <button type="submit">Submit</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("URL")
        mode = request.form.get("mode")
        include_subs = request.form.get("include_subs") == "true"

        if not validators.url(url):
            return "Invalid URL", 400

        safe_cleanup()

        try:
            if mode == "audio":
                codec = request.form.get("codec", "m4a")
                ydl_opts = build_common_opts(
                    os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                    include_subs=include_subs
                )
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'].insert(0, {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': codec
                })

            elif mode == "best_video":
                ydl_opts = build_common_opts(
                    os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                    include_subs=include_subs
                )
                ydl_opts['format'] = (
                    'bestvideo[ext=mp4]+bestaudio[ext=m4a]/'
                    'best[ext=mp4]/best'
                )
            else:
                return "Invalid mode", 400

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = get_final_filepath(info, ydl)

            return send_file(download_path, as_attachment=True)

        except yt_dlp.utils.DownloadError as e:
            return f"Download failed: {str(e)}", 500

        except Exception as e:
            return f"Unexpected error: {str(e)}", 500

    return render_template_string(html)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
