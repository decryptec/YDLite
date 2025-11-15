import yt_dlp
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Simple HTML form with checkboxes
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
        return jsonify({"error": "Missing 'url' parameter"}), 400

    selected_options = request.form.getlist("options")

    # Map checkbox values to yt-dlp options
    ydl_opts = {
        "outtmpl": "%(title)s.%(ext)s"
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
            info = ydl.extract_info(url, download=False)
            sanitized_info = ydl.sanitize_info(info)
            error_code = ydl.download([url])

            if error_code == 0:
                status = "success"
            else:
                status = "failed"

            response = {
                "status": status,
                "info": sanitized_info,
                "options_used": ydl_opts
            }

            return jsonify(response)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
