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

class MyCustomPP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        self.to_screen('Custom PostProcessor: Doing stuff')
        return [], info

def format_selector(ctx, preferred_ext="mp4"):
    formats = ctx.get('formats')[::-1]
    best_video = next(f for f in formats if f['vcodec'] != 'none' and f['acodec'] == 'none')
    audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[preferred_ext]
    best_audio = next(f for f in formats if (
        f['acodec'] != 'none' and f['vcodec'] == 'none' and f['ext'] == audio_ext))
    yield {
        'format_id': f'{best_video["format_id"]}+{best_audio["format_id"]}',
        'ext': best_video['ext'],
        'requested_formats': [best_video, best_audio],
        'protocol': f'{best_video["protocol"]}+{best_audio["protocol"]}'
    }

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
                # Ensure extension matches codec
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

        elif mode == "postprocessor":
            when = request.form.get("pp_when", "pre_process")
            ydl_opts = {'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.add_post_processor(MyCustomPP(), when=when)
                info = ydl.extract_info(url, download=True)
                download_path = info.get("_filename") or ydl.prepare_filename(info)
            return send_file(download_path, as_attachment=True)

        elif mode == "format_selector":
            preferred_ext = request.form.get("preferred_ext", "mp4")
            ydl_opts = {
                'format': lambda ctx: format_selector(ctx, preferred_ext),
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

            <label><input type="radio" name="mode" value="postprocessor" onclick="showSettings('postprocessor')"> Custom PostProcessor</label><br>
            <div id="postprocessor-settings" style="display:none; margin-left:20px;">
                <label>When to run:</label>
                <select name="pp_when">
                    <option value="pre_process">Pre-process</option>
                    <option value="post_process">Post-process</option>
                </select>
            </div>

            <label><input type="radio" name="mode" value="format_selector" onclick="showSettings('format_selector')"> Custom Format Selector</label><br>
            <div id="format_selector-settings" style="display:none; margin-left:20px;">
                <label>Preferred Extension:</label>
                <select name="preferred_ext">
                    <option value="mp4">MP4</option>
                    <option value="webm">WebM</option>
                </select>
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
