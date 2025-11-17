import os
import yt_dlp
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

form_html = """
<!doctype html>
<html>
  <head>
    <title>LAN Video Downloader</title>
  </head>
  <body>
    <h2>Download a Video</h2>
    <form method="POST" action="/download">
      <label>Video URL:</label><br>
      <input type="text" name="url" required><br><br>
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

    ydl_opts = {
        "outtmpl": "%(title)s.%(ext)s",
        "http_headers": {"User-Agent": "Mozilla/5.0"},
        "nocheckcertificate": True
    }

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
