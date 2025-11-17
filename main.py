import os
import subprocess
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

    cmd = ["yt-dlp", "-o", "%(title)s.%(ext)s"]

    if "format_best" in selected_options:
        cmd += ["-f", "best"]
    if "format_audio" in selected_options:
        cmd += ["-f", "bestaudio/best"]
    if "write_subs" in selected_options:
        cmd += ["--write-subs", "--sub-lang", "en"]
    if "write_thumbnail" in selected_options:
        cmd += ["--write-thumbnail"]
    if "no_playlist" in selected_options:
        cmd += ["--no-playlist"]

    cmd.append(url)

    try:
        subprocess.run(cmd, check=True)
        files = sorted(
            [f for f in os.listdir(".") if os.path.isfile(f)],
            key=lambda x: os.path.getmtime(x),
            reverse=True
        )
        if files:
            return send_file(files[0], as_attachment=True)
        else:
            return "Download failed", 500
    except subprocess.CalledProcessError as e:
        return f"Error running yt-dlp: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
