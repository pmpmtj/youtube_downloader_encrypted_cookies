# save as: download_audio.py
import sys
from yt_dlp import YoutubeDL

def download_audio(url: str) -> None:
    ydl_opts = {
        "format": "bestaudio/best",  
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": False,
        "no_warnings": False,
        "noprogress": False,
        #"writeinfojson": True,

    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python download_audio.py <YouTube URL>")
        sys.exit(1)
    download_audio(sys.argv[1])
