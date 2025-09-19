# audio_dl/api.py
import glob, os, tempfile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from yt_dlp import YoutubeDL

@api_view(["POST"])
def download_audio_api(request):
    url = (request.data.get("url") or "").strip()
    if not url:
        return Response({"detail": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

    tmpdir = tempfile.mkdtemp(prefix="yt_")
    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)

    if not filepath or not os.path.exists(filepath):
        files = glob.glob(os.path.join(tmpdir, "*"))
        if not files:
            return Response({"detail": "Download failed"}, status=status.HTTP_400_BAD_REQUEST)
        filepath = files[0]

    filename = os.path.basename(filepath)
    fileobj = open(filepath, "rb")
    # DRF can return a Django FileResponse directly
    from django.http import FileResponse
    return FileResponse(fileobj, as_attachment=True, filename=filename)