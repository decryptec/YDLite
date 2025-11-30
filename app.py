from flask import Flask, request, render_template_string, send_file
import yt_dlp
import os
import shutil

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Common options builder
def build_common_opts(download_path, include_subs=False):
    opts = {
        'outtmpl': download_path,
        'postprocessors': [
            {'key': 'FFmpegMetadata'},   # --add-metadata
            {'key': 'EmbedThumbnail'},   # --embed-thumbnail
        ],
        'writethumbnail': True,
        'noplaylist': True,             # force single video only
    }
    if include_subs:
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['en']  # adjust language if needed
    return opts

# Helper to get final file path
def get_final_filepath(info, ydl):
    if "requested_downloads" in info and info["requested_downloads"]:
        return info["requested_downloads"][0]["filepath"]
    return ydl.prepare_filename(info)

# Route
@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        # cleanup downloads directory except readme.md ---
        for fname in os.listdir(DOWNLOAD_DIR):
            fpath = os.path.join(DOWNLOAD_DIR, fname)
            if fname.lower() != "readme.md":
                try:
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                    elif os.path.isdir(fpath):
                        shutil.rmtree(fpath)
                    print(f"Deleted {fpath}")
                except Exception as e:
                    print(f"Error deleting {fpath}: {e}")

        url = request.form.get("URL")
        mode = request.form.get("mode")
        include_subs = request.form.get("include_subs") == "true"
        download_path = None

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

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = get_final_filepath(info, ydl)

        elif mode == "best_video":
            ydl_opts = build_common_opts(
                os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                include_subs=include_subs
            )
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = get_final_filepath(info, ydl)

        # Send file
        if download_path:
            return send_file(download_path, as_attachment=True)

    # frontend form
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube Downloader</title>
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
        <h1>YouTube Downloader</h1>
        <form method="POST">
            <label><input type="radio" name="mode" value="audio" onclick="showSettings('audio')" required> Extract Audio</label><br>
            <div id="audio-settings" style="display:none; margin-left:20px;">
                <label>Codec:</label>
                <select name="codec">
                    <option value="m4a">m4a</option>
                    <option value="mp3">mp3</option>
                    <option value="wav">wav</option>
                </select><br>
                <label>Include Subs if Any:</label>
                <input type="checkbox" name="include_subs" value="true">
            </div>

            <label><input type="radio" name="mode" value="best_video" onclick="showSettings('best_video')"> Download Best Video (MP4)</label><br>
            <div id="best_video-settings" style="display:none; margin-left:20px;">
                <p>Downloads best available MP4 video + M4A audio.</p>
                <label>Include Subs if Any:</label>
                <input type="checkbox" name="include_subs" value="true">
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
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
