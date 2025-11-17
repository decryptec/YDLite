import os
import yt_dlp
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

form_html = """
<!doctype html>
<html>
  <head>
    <title>yt-dlp Downloader</title>
  </head>
  <body>
    <h2>Download a Video</h2>
    <form method="POST" action="/download">
      <label>Video URL:</label><br>
      <input type="text" name="url" required><br><br>

      <h3>Options:</h3>
      <input type="checkbox" name="options" value="format_best"> Best Quality<br>
      <input type="checkbox" name="options" value="format_audio"> Audio Only<br>
      <input type="checkbox" name="options" value="write_subs"> Download Subtitles<br>
      <input type="checkbox" name="options" value="write_thumbnail"> Download Thumbnail<br>
      <input type="checkbox" name="options" value="no_playlist"> Single Video Only (no playlist)<br><br>

      <button type="submit">Download</button>
    </form>
  </body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(form_html)

@app.route("/download", methods=["POST"])
def url_download():
    url = request.form.get("url")
    if not url:
        return "Missing URL", 400

    selected_options = request.form.getlist("options")

    ydl_opts = {
        "outtmpl": "%(title)s.%(ext)s",
        "http_headers": {"User-Agent": "Mozilla/5.0"},
        "nocheckcertificate": True
    }

    if "format_best" in selected_options:
        ydl_opts["format"] = "best"
    if "format_audio" in selected_options:
        ydl_opts["format"] = "bestaudio/best"
    if "write_subs" in selected_options:
        ydl_opts["writesubtitles"] = True
        ydl_opts["subtitleslangs"] = ["en"]
    if "write_thumbnail" in selected_options:
        ydl_opts["writethumbnail"] = True
    if "no_playlist" in selected_options:
        ydl_opts["noplaylist"] = True

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        else:
            return "Download failed", 500

    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
