# transcriptions_dl/api.py
import os
import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from core.shared_utils.url_utils import YouTubeURLSanitizer, YouTubeURLError
from core.shared_utils.app_config import APP_CONFIG
from core.shared_utils.security_utils import get_client_ip, log_request_info
from cookie_management.cookie_manager import get_user_cookies

# Import the transcript downloader
from core.downloaders.transcriptions.dl_transcription import (
    download_transcript_files, 
    preview_transcript,
    get_video_info
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def download_transcript_api(request):
    """Synchronous transcript download API endpoint."""
    url = (request.data.get("url") or "").strip()
    if not url:
        return Response({"detail": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate YouTube URL before processing
    try:
        if not YouTubeURLSanitizer.is_youtube_url(url):
            return Response({"detail": "Invalid YouTube URL"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": f"URL validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # Get user-specific download directory for transcripts
    user_download_dir = request.user.get_download_directory('transcripts')
    
    # Check if user wants to download to remote (from request data)
    download_to_remote = request.data.get('download_to_remote', False)
    
    # Get user tracking information
    user_ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Log request
    log_request_info(request, "transcript_download")
    
    # Get user cookies for authentication
    user_cookies = get_user_cookies(request.user)
    
    try:
        # Use the core transcript download function
        success = download_transcript_files(url, output_dir=str(user_download_dir))
        
        if not success:
            return Response({"detail": "Failed to download transcript"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get video info for response
        video_info = get_video_info(url)
        video_id = video_info.get('id', 'unknown') if video_info else 'unknown'
        
        # Find the generated files
        transcript_files = _find_transcript_files(user_download_dir, video_id)
        
        if download_to_remote and transcript_files:
            # Return the first file (clean format) for download
            file_path = transcript_files.get('clean')
            if file_path and os.path.exists(file_path):
                filename = os.path.basename(file_path)
                fileobj = open(file_path, "rb")
                return FileResponse(fileobj, as_attachment=True, filename=filename)
        
        # Return file info as JSON (server-only storage)
        return Response({
            'success': True,
            'message': 'Transcript files downloaded successfully to server',
            'video_info': {
                'title': video_info.get('title', 'Unknown') if video_info else 'Unknown',
                'uploader': video_info.get('uploader', 'Unknown') if video_info else 'Unknown',
                'duration': video_info.get('duration', 0) if video_info else 0,
                'video_id': video_id
            },
            'file_paths': transcript_files,
            'download_source': 'api'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_text = str(e)
        if "Sign in to confirm you're not a bot" in error_text or "not a bot" in error_text:
            return Response({
                "detail": "YouTube requires authentication for this request. Please upload your YouTube cookies using the Cookie Management page."
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": f"Error: {error_text}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def download_transcript_api_async(request):
    """Queue a transcript download job and return a task id (HTTP 202)."""
    url = (request.data.get("url") or "").strip()
    if not url:
        return Response({"detail": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate YouTube URL before queuing
    try:
        if not YouTubeURLSanitizer.is_youtube_url(url):
            return Response({"detail": "Invalid YouTube URL"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": f"URL validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # Get user-specific download directory for transcripts
    user_download_dir = request.user.get_download_directory('transcripts')
    
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # Get user tracking information
    user_ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Queue the background task
    from transcriptions_dl.tasks import process_transcript_download
    process_transcript_download(
        url, 
        task_id=task_id, 
        output_dir=str(user_download_dir),
        user_id=request.user.id,
        user_ip=user_ip,
        user_agent=user_agent,
        repeat=0
    )

    # Build URLs for status and result endpoints
    from django.urls import reverse
    status_url = request.build_absolute_uri(reverse("transcript_job_status", args=[task_id]))
    result_url = request.build_absolute_uri(reverse("transcript_job_result", args=[task_id]))

    return Response({
        "task_id": task_id,
        "status": "queued",
        "status_url": status_url,
        "result_url": result_url,
    }, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transcript_job_status(request, job_id: str):
    """Return current task status (placeholder - no DB integration yet)."""
    # TODO: Implement with database integration
    return Response({
        "detail": "Status checking not implemented yet - requires database integration"
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transcript_job_result(request, job_id: str):
    """Return job result (placeholder - no DB integration yet)."""
    # TODO: Implement with database integration
    return Response({
        "detail": "Result retrieval not implemented yet - requires database integration"
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transcript_preview_api(request):
    """Preview transcript before downloading."""
    url = request.GET.get("url", "").strip()
    if not url:
        return Response({"detail": "Missing 'url' parameter"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate YouTube URL
    try:
        if not YouTubeURLSanitizer.is_youtube_url(url):
            return Response({"detail": "Invalid YouTube URL"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": f"URL validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get video info first
        video_info = get_video_info(url)
        if not video_info:
            return Response({"detail": "Could not extract video information"}, status=status.HTTP_400_BAD_REQUEST)
        
        video_id = video_info.get('id')
        if not video_id:
            return Response({"detail": "Could not extract video ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get transcript preview
        preview_data = preview_transcript(video_id)
        
        if not preview_data:
            return Response({"detail": "No transcript available for this video"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'video_info': {
                'title': video_info.get('title', 'Unknown'),
                'uploader': video_info.get('uploader', 'Unknown'),
                'duration': video_info.get('duration', 0),
                'video_id': video_id
            },
            'transcript_preview': preview_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_text = str(e)
        if "Sign in to confirm you're not a bot" in error_text or "not a bot" in error_text:
            return Response({
                "detail": "YouTube requires authentication for this request. Please upload your YouTube cookies using the Cookie Management page."
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": f"Error: {error_text}"}, status=status.HTTP_400_BAD_REQUEST)


def _find_transcript_files(download_dir, video_id):
    """Find generated transcript files in the download directory."""
    import glob
    from pathlib import Path
    
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
