# transcriptions_dl/views.py
import os
from django.http import HttpResponseBadRequest, FileResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.downloaders.transcriptions.dl_transcription import download_transcript_files, get_video_info
from core.shared_utils.security_utils import get_client_ip, log_request_info
from core.shared_utils.rate_limiting import get_download_stats, is_ip_allowed
from cookie_management.cookie_manager import get_user_cookies
from django.conf import settings


@login_required
def download_form(request):
    """Transcript download form view."""
    if request.method == "POST":
        url = (request.POST.get("url") or "").strip()
        if not url:
            return HttpResponseBadRequest("Missing URL.")

        # Get selected formats
        selected_formats = request.POST.getlist('formats')
        if not selected_formats:
            messages.error(request, "Please select at least one transcript format.")
            return redirect('transcriptions_dl:download_form')

        # Get user-specific download directory for transcripts
        user_download_dir = request.user.get_download_directory('transcripts')
        
        # Call the core download function with user-specific directory
        try:
            # Log request and get user tracking information
            log_request_info(request, "transcript_download")
            user_ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Get user cookies for authentication
            user_cookies = get_user_cookies(request.user)
            
            # Download transcript files using the core function with selected formats
            success = download_transcript_files(url, output_dir=str(user_download_dir), formats=selected_formats)
            
            if not success:
                return HttpResponseBadRequest("Failed to download transcript files.")
            
            # Get video info for response
            video_info = get_video_info(url)
            video_id = video_info.get('id', 'unknown') if video_info else 'unknown'
            
            # Find the generated files
            transcript_files = _find_transcript_files(user_download_dir, video_id)
            
            # Server-only storage - show success message and redirect
            format_names = [_get_format_display_name(fmt) for fmt in selected_formats]
            messages.success(request, f'Transcripts downloaded successfully to server: {", ".join(format_names)}')
            return redirect('transcriptions_dl:download_form')
            
        except Exception as e:
            error_text = str(e)
            if "Sign in to confirm you're not a bot" in error_text or "not a bot" in error_text:
                messages.error(request, (
                    "YouTube requires authentication for this request. "
                    "Please upload your YouTube cookies using the Cookie Management page. "
                    "Go to Dashboard → Manage Cookies to upload your cookies.txt file."
                ))
            else:
                messages.error(request, f"Error: {error_text}")
            return HttpResponseBadRequest(f"Error: {e}")

    # Add rate limiting info to context
    client_ip = get_client_ip(request)
    download_stats = get_download_stats(client_ip)
    
    # Get cookie status
    from cookie_management.cookie_manager import get_cookie_status
    cookie_status = get_cookie_status(request.user)
    
    context = {
        'download_stats': download_stats,
        'ip_allowed': is_ip_allowed(client_ip),
        'cookie_status': cookie_status
    }
    
    return render(request, "transcriptions_dl/download_form.html", context)


def _find_transcript_files(download_dir, video_id):
    """Find generated transcript files in the download directory."""
    import glob
    
    if not os.path.exists(download_dir):
        return {}
    
    # Look for files with the video_id pattern
    pattern = os.path.join(download_dir, f"{video_id}_*")
    files = glob.glob(pattern)
    
    transcript_files = {}
    
    for file_path in files:
        filename = os.path.basename(file_path)
        if filename.endswith('_clean.txt'):
            transcript_files['clean'] = file_path
        elif filename.endswith('_timestamped.txt'):
            transcript_files['timestamped'] = file_path
        elif filename.endswith('_structured.json'):
            transcript_files['structured'] = file_path
    
    return transcript_files




def _get_format_display_name(format_type):
    """Get display name for format type."""
    format_names = {
        'clean': 'Clean Text',
        'timestamped': 'Timestamped Text',
        'structured': 'Structured JSON'
    }
    return format_names.get(format_type, format_type)


def public_landing(request):
    """Public landing page that redirects to login or dashboard."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, "public_landing.html")