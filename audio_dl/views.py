# youtube_downloader/audio_dl/views.py
import os
import glob
import tempfile
from django.http import FileResponse, HttpResponseBadRequest
from django.shortcuts import render
from yt_dlp import YoutubeDL

def index(request):
    if request.method == "POST":
        url = (request.POST.get("url") or "").strip()
        if not url:
            return HttpResponseBadRequest("Missing URL.")

        tmpdir = tempfile.mkdtemp(prefix="yt_")
        outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)

            # Fallback in case postprocessing/format picks a different ext
            if not os.path.exists(filepath):
                files = glob.glob(os.path.join(tmpdir, "*"))
                filepath = files[0] if files else None

            if not filepath or not os.path.exists(filepath):
                return HttpResponseBadRequest("Download failed.")

            filename = os.path.basename(filepath)
            fileobj = open(filepath, "rb")
            return FileResponse(fileobj, as_attachment=True, filename=filename)

        except Exception as e:
            return HttpResponseBadRequest(f"Error: {e}")

    return render(request, "index.html")
