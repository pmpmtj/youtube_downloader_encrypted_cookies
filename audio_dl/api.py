# audio_dl/api.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from core.downloaders.audio.download_audio import download_audio
from core.shared_utils.url_utils import YouTubeURLSanitizer, YouTubeURLError
from core.downloaders.shared_downloader import get_file_info
from core.shared_utils.app_config import APP_CONFIG

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def download_audio_api(request):
    url = (request.data.get("url") or "").strip()
    if not url:
        return Response({"detail": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate YouTube URL before processing
    try:
        if not YouTubeURLSanitizer.is_youtube_url(url):
            return Response({"detail": "Invalid YouTube URL"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": f"URL validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # Get user-specific download directory
    user_download_dir = request.user.get_download_directory()
    
    # Check if user wants to download to remote (from request data)
    download_to_remote = request.data.get('download_to_remote', True)
    
    # Use the core download function with user-specific directory
    result = download_audio(url, output_dir=str(user_download_dir))
    
    if not result['success']:
        return Response({"detail": result['error']}, status=status.HTTP_400_BAD_REQUEST)
    
    if download_to_remote:
        # Return the file (current behavior - download dialog)
        fileobj = open(result['filepath'], "rb")
        return FileResponse(fileobj, as_attachment=True, filename=result['filename'])
    else:
        # Return file info as JSON (server-only storage)
        file_info = get_file_info(result['filepath'])
        return Response({
            'success': True,
            'message': 'File downloaded successfully to server',
            'file_info': file_info,
            'job_id': result.get('job_id'),
            'metadata': result.get('metadata', {})
        }, status=status.HTTP_200_OK)

# ---------------------- NEW: Async endpoints (django-background-tasks) ----------------------
from django.urls import reverse
from background_task.models import Task
from django.shortcuts import get_object_or_404
import uuid


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def download_audio_api_async(request):
    """Queue an audio download job and return a task id (HTTP 202)."""
    url = (request.data.get("url") or "").strip()
    if not url:
        return Response({"detail": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate YouTube URL before queuing
    try:
        if not YouTubeURLSanitizer.is_youtube_url(url):
            return Response({"detail": "Invalid YouTube URL"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": f"URL validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # Get user-specific download directory
    user_download_dir = request.user.get_download_directory()
    
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # Queue the background task with user-specific directory
    from audio_dl.tasks import process_youtube_audio
    process_youtube_audio(url, task_id=task_id, output_dir=str(user_download_dir), repeat=0)

    status_url = request.build_absolute_uri(reverse("job_status", args=[task_id]))
    result_url = request.build_absolute_uri(reverse("job_result", args=[task_id]))

    return Response({
        "task_id": task_id,
        "status": "queued",
        "status_url": status_url,
        "result_url": result_url,
    }, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_status(request, job_id: str):
    """Return current task status."""
    try:
        # Look for task by checking task_params for the task_id
        task = Task.objects.filter(task_params__icontains=job_id).first()
        
        if not task:
            # Also check completed tasks
            from background_task.models import CompletedTask
            completed_task = CompletedTask.objects.filter(task_params__icontains=job_id).first()
            if completed_task:
                return Response({
                    "task_id": job_id,
                    "status": "completed",
                    "run_at": completed_task.run_at.isoformat() if completed_task.run_at else None,
                    "locked_at": completed_task.locked_at.isoformat() if completed_task.locked_at else None,
                })
            return Response({"detail": "Unknown task_id"}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "task_id": job_id,
            "status": "running" if task.locked_at is None else "completed",
            "run_at": task.run_at.isoformat() if task.run_at else None,
            "locked_at": task.locked_at.isoformat() if task.locked_at else None,
        }
            
        return Response(data)
    except Exception as e:
        return Response({"detail": f"Error checking task status: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_result(request, job_id: str):
    """If task finished successfully, stream the generated file."""
    try:
        # Look for task by checking task_params for the task_id
        from background_task.models import CompletedTask
        
        # Check if task is completed
        completed_task = CompletedTask.objects.filter(task_params__icontains=job_id).first()
        
        if not completed_task:
            # Check if task is still running
            task = Task.objects.filter(task_params__icontains=job_id).first()
            if not task:
                return Response({"detail": "Unknown task_id"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"detail": "Task not completed"}, status=status.HTTP_202_ACCEPTED)

        # For this simplified implementation, we'll look for the file in the media directory
        # In a real implementation, you'd store the result in a custom model
        import os
        from django.conf import settings
        
        media_dir = os.path.join(settings.MEDIA_ROOT, 'downloads', 'audio')
        files = os.listdir(media_dir) if os.path.exists(media_dir) else []
        
        if not files:
            return Response({"detail": "No file available"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the most recent audio file (exclude metadata files)
        audio_files = [f for f in files if not f.endswith('_metadata.json') and not f.startswith('.')]
        if not audio_files:
            return Response({"detail": "No audio file available"}, status=status.HTTP_400_BAD_REQUEST)
        
        latest_file = max(audio_files, key=lambda f: os.path.getctime(os.path.join(media_dir, f)))
        filepath = os.path.join(media_dir, latest_file)
        
        # Check if we should download to remote location (client)
        download_to_remote = APP_CONFIG.get("download", {}).get("download_to_remote_location", "True").lower() == "true"
        
        if download_to_remote:
            # Return the file (current behavior - download dialog)
            try:
                fileobj = open(filepath, "rb")
                return FileResponse(fileobj, as_attachment=True, filename=latest_file)
            except OSError:
                return Response({"detail": "File not found on disk"}, status=status.HTTP_410_GONE)
        else:
            # Return file info as JSON (server-only storage)
            file_info = get_file_info(filepath)
            return Response({
                'success': True,
                'message': 'File downloaded successfully to server',
                'file_info': file_info,
                'task_id': job_id
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({"detail": f"Error retrieving result: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)