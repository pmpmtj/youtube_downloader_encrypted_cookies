# youtube_downloader/audio_dl/views.py
from django.http import HttpResponseBadRequest, FileResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.downloaders.audio.download_audio import download_audio
from core.downloaders.shared_downloader import get_file_info
from core.shared_utils.app_config import APP_CONFIG

@login_required
def index(request):
    if request.method == "POST":
        url = (request.POST.get("url") or "").strip()
        if not url:
            return HttpResponseBadRequest("Missing URL.")

        # Get user-specific download directory
        user_download_dir = request.user.get_download_directory()
        
        # Check if user wants to download to remote (checkbox state)
        download_to_remote = request.POST.get('download_to_remote') == 'on'
        
        # Call the core download function with user-specific directory
        try:
            result = download_audio(url, output_dir=str(user_download_dir))
            
            if not result['success']:
                return HttpResponseBadRequest(f"Error: {result['error']}")
            
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

    return render(request, "audio_dl/download_form.html")


def public_landing(request):
    """Public landing page that redirects to login or dashboard."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, "public_landing.html")
