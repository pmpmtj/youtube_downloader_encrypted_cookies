# youtube_downloader/audio_dl/views.py
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from . import api

def index(request):
    if request.method == "POST":
        url = (request.POST.get("url") or "").strip()
        if not url:
            return HttpResponseBadRequest("Missing URL.")

        # Create a mock DRF request object to call the API internally
        class MockRequest:
            def __init__(self, data):
                self.data = data
        
        mock_request = MockRequest({"url": url})
        
        # Call the API function directly
        try:
            response = api.download_audio_api(mock_request)
            return response
        except Exception as e:
            return HttpResponseBadRequest(f"Error: {e}")

    return render(request, "index.html")
