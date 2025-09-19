# audio_dl/api.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from core.downloaders.download_audio import download_audio

@api_view(["POST"])
def download_audio_api(request):
    url = (request.data.get("url") or "").strip()
    if not url:
        return Response({"detail": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

    # Use the core download function
    result = download_audio(url)
    
    if not result['success']:
        return Response({"detail": result['error']}, status=status.HTTP_400_BAD_REQUEST)
    
    # Return the file
    fileobj = open(result['filepath'], "rb")
    return FileResponse(fileobj, as_attachment=True, filename=result['filename'])