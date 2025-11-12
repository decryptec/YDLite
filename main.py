import json
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def url_download():
    data = request.get_json()

    url = data.get("url")
    if not url:
        return jsonify({
            "error": "Missing 'url' parameter in request"
        }), 400

    options = data.get("options")
    if isinstance(options, dict):
        ydl_opts = options
    else:
        ydl_opts = {
            "format": "best",
            "outtmpl": "%(title)s.%(ext)s"
        }

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
                "info": sanitized_info
            }

            return jsonify(response)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
