import json
import yt_dlp
import flask 

# Defined Options for yt_dlp
ydl_opts = {
    'format': 'best',
    'outtmpl': '%(title)s.%(ext)s'
}

URL = input("Insert URL: ")

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(URL, download=False)
    print(json.dumps(ydl.sanitize_info(info), indent=2))

    error_code = ydl.download([URL])
    print('Failed to download' if error_code else 'Successfully downloaded')
