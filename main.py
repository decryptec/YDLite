import os
import subprocess
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

form_html = """
<!doctype html>
<html>
  <head>
    <title>LAN Downloader</title>
  </head>
  <body>
    <h2>Download YouTube</h2>
    <form method="POST" action="/download">
      <label>Video URL:</label><br>
      <input type="text" name="url" required><br><br>

      <h3>Options:</h3>
      <input type="checkbox" name="options" value="add_metadata"> Add Metadata<br>
      <input type="checkbox" name="options" value="write_subs"> Download Subtitles<br>
      <input type="checkbox" name="options" value="embed_thumbnail"> Embed Thumbnail<br>
      <input type="checkbox" name="options" value="extract_audio"> Extract Audio<br>
      <input type="radio" name="format" value="mp3" checked> MP3 Audio<br>
      <input type="radio" name="format" value="mp4"> MP4 Video<br><br>
      <input type="checkbox" name="options" value="delete_after"> Delete after download<br><br>

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
    chosen_format = request.form.get("format")

    cmd = ["yt-dlp", "-o", "%(title)s.%(ext)s"]

    if "add_metadata" in selected_options:
        cmd += ["--add-metadata"]
    if "write_subs" in selected_options:
        cmd += ["--write-subs", "--sub-lang", "en"]
    if "embed_thumbnail" in selected_options:
        cmd += ["--embed-thumbnail"]

    if chosen_format == "mp3":
        cmd += ["--extract-audio", "--audio-format", "mp3"]
    elif chosen_format == "mp4":
        cmd += ["-f", "mp4"]

    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"yt-dlp failed:\n{result.stderr}", 500

    files = sorted(
        [f for f in os.listdir(".") if os.path.isfile(f)],
        key=lambda x: os.path.getmtime(x),
        reverse=True
    )
    if files:
        filename = files[0]
        response = send_file(filename, as_attachment=True)
        if "delete_after" in selected_options:
            try:
                os.remove(filename)
            except Exception:
                pass
        return response
    else:
        return "Download failed", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
