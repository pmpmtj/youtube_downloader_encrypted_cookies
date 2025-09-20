# youtube_downloader/audio_dl/views.py
from django.http import HttpResponseBadRequest, FileResponse
from django.shortcuts import render
from core.downloaders.audio.download_audio import download_audio

def index(request):
    if request.method == "POST":
        url = (request.POST.get("url") or "").strip()
        if not url:
            return HttpResponseBadRequest("Missing URL.")

        # Call the core download function directly
        try:
            result = download_audio(url)
            
            if not result['success']:
                return HttpResponseBadRequest(f"Error: {result['error']}")
            
            # Return the file
            fileobj = open(result['filepath'], "rb")
            return FileResponse(fileobj, as_attachment=True, filename=result['filename'])
            
        except Exception as e:
            return HttpResponseBadRequest(f"Error: {e}")

    return render(request, "index.html")
