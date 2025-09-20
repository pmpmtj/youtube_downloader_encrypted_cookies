# youtube_downloader/audio_dl/views.py
from django.http import HttpResponseBadRequest, FileResponse, JsonResponse
from django.shortcuts import render
from core.downloaders.audio.download_audio import download_audio
from core.downloaders.shared_downloader import get_file_info
from core.shared_utils.app_config import APP_CONFIG

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
            
            # Check if we should download to remote location (client)
            download_to_remote = APP_CONFIG.get("download", {}).get("download_to_remote_location", "True").lower() == "true"
            
            if download_to_remote:
                # Return the file (current behavior - download dialog)
                fileobj = open(result['filepath'], "rb")
                return FileResponse(fileobj, as_attachment=True, filename=result['filename'])
            else:
                # Return file info as JSON (server-only storage)
                file_info = get_file_info(result['filepath'])
                return JsonResponse({
                    'success': True,
                    'message': 'File downloaded successfully to server',
                    'file_info': file_info,
                    'job_id': result.get('job_id'),
                    'metadata': result.get('metadata', {})
                })
            
        except Exception as e:
            return HttpResponseBadRequest(f"Error: {e}")

    return render(request, "index.html")
