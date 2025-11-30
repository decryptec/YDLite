from flask import Flask, request, render_template_string, send_file, after_this_request
import yt_dlp
import os
import json

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Options
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

# Common options builder
def build_common_opts(download_path, write_subs=False):
    opts = {
        'outtmpl': download_path,
        'postprocessors': [
            {'key': 'FFmpegMetadata'},   # --add-metadata
            {'key': 'EmbedThumbnail'},   # --embed-thumbnail
        ],
        'writethumbnail': True,
    }
    if write_subs:
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['en']  # adjust language if needed
    return opts

# Route
@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        url = request.form.get("URL")
        mode = request.form.get("mode")
        write_subs = request.form.get("write_subs") == "true"
        download_path = None

        if mode == "audio":
            codec = request.form.get("codec", "m4a")
            ydl_opts = build_common_opts(
                os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                write_subs=write_subs
            )
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'].insert(0, {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec
            })
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)
                base, _ = os.path.splitext(download_path)
                download_path = f"{base}.{codec}"

        elif mode == "filter":
            min_duration = int(request.form.get("min_duration", 60))
            def custom_filter(info, *, incomplete):
                return longer_than(info, min_duration, incomplete=incomplete)
            ydl_opts = build_common_opts(
                os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                write_subs=write_subs
            )
            ydl_opts['match_filter'] = custom_filter
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)

        elif mode == "logger":
            debug = request.form.get("debug") == "true"
            ydl_opts = build_common_opts(
                os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                write_subs=write_subs
            )
            ydl_opts['logger'] = MyLogger(debug=debug)
            ydl_opts['progress_hooks'] = [my_hook]
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)

        elif mode == "best_video":
            ydl_opts = build_common_opts(
                os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                write_subs=write_subs
            )
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)

        # Delete file after sending
        if download_path:
            @after_this_request
            def remove_file(response):
                try:
                    os.remove(download_path)
                    print(f"Deleted {download_path}")
                except Exception as e:
                    print(f"Error deleting file: {e}")
                return response
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
            <label><input type="radio" name="mode" value="audio" onclick="showSettings('audio')" required> Extract Audio</label><br>
            <div id="audio-settings" style="display:none; margin-left:20px;">
                <label>Codec:</label>
                <select name="codec">
                    <option value="m4a">m4a</option>
                    <option value="mp3">mp3</option>
                    <option value="wav">wav</option>
                </select><br>
                <label>Download Subtitles:</label>
                <input type="checkbox" name="write_subs" value="true">
            </div>

            <label><input type="radio" name="mode" value="filter" onclick="showSettings('filter')"> Filter Videos</label><br>
            <div id="filter-settings" style="display:none; margin-left:20px;">
                <label>Minimum Duration (seconds):</label>
                <input type="number" name="min_duration" value="60"><br>
                <label>Download Subtitles:</label>
                <input type="checkbox" name="write_subs" value="true">
            </div>

            <label><input type="radio" name="mode" value="logger" onclick="showSettings('logger')"> Logger + Progress Hook</label><br>
            <div id="logger-settings" style="display:none; margin-left:20px;">
                <label>Enable Debug:</label>
                <input type="checkbox" name="debug" value="true"><br>
                <label>Download Subtitles:</label>
                <input type="checkbox" name="write_subs" value="true">
            </div>

            <label><input type="radio" name="mode" value="best_video" onclick="showSettings('best_video')"> Download Best Video (MP4)</label><br>
            <div id="best_video-settings" style="display:none; margin-left:20px;">
                <p>Downloads best available MP4 video + M4A audio.</p>
                <label>Download Subtitles:</label>
                <input type="checkbox" name="write_subs" value="true">
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
    app.run(debug=True, host="0.0.0.0", port=5000)
