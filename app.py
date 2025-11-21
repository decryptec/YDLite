from flask import Flask, request, render_template_string, send_file
import yt_dlp
import os
import json

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Helpers ---
def longer_than(info, min_duration, *, incomplete):
    duration = info.get('duration')
    if duration and duration < min_duration:
        return f"Video shorter than {min_duration}s"

class MyLogger:
    def __init__(self, debug=False):
        self.debug_enabled = debug
    def debug(self, msg):
        if msg.startswith('[debug] '):
            if self.debug_enabled:
                print(msg)
        else:
            self.info(msg)
    def info(self, msg): print(msg)
    def warning(self, msg): print("WARNING:", msg)
    def error(self, msg): print("ERROR:", msg)

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now post-processing ...')

# --- Route ---
@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        url = request.form.get("URL")
        mode = request.form.get("mode")
        download_path = None

        if mode == "info":
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                result = json.dumps(ydl.sanitize_info(info), indent=2)

        elif mode == "audio":
            codec = request.form.get("codec", "m4a")
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': codec}],
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)
                base, _ = os.path.splitext(download_path)
                download_path = f"{base}.{codec}"
            return send_file(download_path, as_attachment=True)

        elif mode == "filter":
            min_duration = int(request.form.get("min_duration", 60))
            def custom_filter(info, *, incomplete):
                return longer_than(info, min_duration, incomplete=incomplete)
            ydl_opts = {
                'match_filter': custom_filter,
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)
            return send_file(download_path, as_attachment=True)

        elif mode == "logger":
            debug = request.form.get("debug") == "true"
            ydl_opts = {
                'logger': MyLogger(debug=debug),
                'progress_hooks': [my_hook],
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)
            return send_file(download_path, as_attachment=True)

        elif mode == "best_video":
            # Default to MP4 output
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)
            return send_file(download_path, as_attachment=True)

    # frontend form
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube Downloader Advanced</title>
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
        <h1>YouTube Downloader Advanced</h1>
        <form method="POST">
            <label><input type="radio" name="mode" value="info" onclick="showSettings('info')" required> Extract Info</label><br>
            <div id="info-settings" style="display:none; margin-left:20px;">
                <p>No extra settings for info mode.</p>
            </div>

            <label><input type="radio" name="mode" value="audio" onclick="showSettings('audio')"> Extract Audio</label><br>
            <div id="audio-settings" style="display:none; margin-left:20px;">
                <label>Codec:</label>
                <select name="codec">
                    <option value="m4a">m4a</option>
                    <option value="mp3">mp3</option>
                    <option value="wav">wav</option>
                </select>
            </div>

            <label><input type="radio" name="mode" value="filter" onclick="showSettings('filter')"> Filter Videos</label><br>
            <div id="filter-settings" style="display:none; margin-left:20px;">
                <label>Minimum Duration (seconds):</label>
                <input type="number" name="min_duration" value="60">
            </div>

            <label><input type="radio" name="mode" value="logger" onclick="showSettings('logger')"> Logger + Progress Hook</label><br>
            <div id="logger-settings" style="display:none; margin-left:20px;">
                <label>Enable Debug:</label>
                <input type="checkbox" name="debug" value="true">
            </div>

            <label><input type="radio" name="mode" value="best_video" onclick="showSettings('best_video')"> Download Best Video (MP4)</label><br>
            <div id="best_video-settings" style="display:none; margin-left:20px;">
                <p>Downloads best available MP4 video + M4A audio.</p>
            </div>

            <br>
            <label>YouTube URL:</label><br>
            <input type="text" name="URL" placeholder="https://youtube.com/..." required><br><br>

            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, result=result)

if __name__ == "__main__":
    app.run(debug=True)
