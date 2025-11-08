import json
import yt_dlp
import flask

URL = input("Insert URL: ")

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
  info = ydl.extract_info(URL, downdload=False)

  print(json.dumps(ydl.sanitize_info(info)))
