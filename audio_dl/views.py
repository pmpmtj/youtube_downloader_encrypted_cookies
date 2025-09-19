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


            # Save a copy to the server's current working directory (cwd)
            filename = os.path.basename(filepath)
            
            # uncomment the following 3 lines if you want to save a copy on the server automatically
            dest_path = os.path.join(os.getcwd(), filename)
            with open(filepath, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())

            # uncomment the following 2 lines if you want to send to the browser
            fileobj = open(filepath, "rb")
            return FileResponse(fileobj, as_attachment=True, filename=filename)

        except Exception as e:
            return HttpResponseBadRequest(f"Error: {e}")

    return render(request, "index.html")
