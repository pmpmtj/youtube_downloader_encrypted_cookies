# audio_dl/api.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from core.downloaders.audio.download_audio import download_audio

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

# ---------------------- NEW: Async endpoints (django-background-tasks) ----------------------
from django.urls import reverse
from background_task.models import Task
from django.shortcuts import get_object_or_404
import uuid


@api_view(["POST"])
def download_audio_api_async(request):
    """Queue an audio download job and return a task id (HTTP 202)."""
    url = (request.data.get("url") or "").strip()
    if not url:
        return Response({"detail": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # Queue the background task
    from audio_dl.tasks import process_youtube_audio
    process_youtube_audio(url, task_id=task_id, repeat=0)

    status_url = request.build_absolute_uri(reverse("job_status", args=[task_id]))
    result_url = request.build_absolute_uri(reverse("job_result", args=[task_id]))

    return Response({
        "task_id": task_id,
        "status": "queued",
        "status_url": status_url,
        "result_url": result_url,
    }, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
def job_status(request, job_id: str):
    """Return current task status."""
    try:
        # Try to find the task by ID in the task name/description
        task = Task.objects.filter(task_name__icontains=job_id).first()
        if not task:
            return Response({"detail": "Unknown task_id"}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "task_id": job_id,
            "status": "completed" if task.task_params else "running",
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "run_at": task.run_at.isoformat() if task.run_at else None,
        }
        
        # Check if task has result stored (this is a simplified approach)
        if task.task_params:
            # Task completed - you could store results in a custom model
            data["status"] = "completed"
            
        return Response(data)
    except Exception as e:
        return Response({"detail": f"Error checking task status: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def job_result(request, job_id: str):
    """If task finished successfully, stream the generated file."""
    try:
        task = Task.objects.filter(task_name__icontains=job_id).first()
        if not task:
            return Response({"detail": "Unknown task_id"}, status=status.HTTP_404_NOT_FOUND)

        if not task.task_params:
            return Response({"detail": "Task not completed"}, status=status.HTTP_202_ACCEPTED)

        # For this simplified implementation, we'll look for the file in the media directory
        # In a real implementation, you'd store the result in a custom model
        import os
        from django.conf import settings
        
        media_dir = os.path.join(settings.MEDIA_ROOT, 'downloads', 'audio')
        files = os.listdir(media_dir) if os.path.exists(media_dir) else []
        
        if not files:
            return Response({"detail": "No file available"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the most recent file
        latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(media_dir, f)))
        filepath = os.path.join(media_dir, latest_file)
        
        try:
            fileobj = open(filepath, "rb")
            return FileResponse(fileobj, as_attachment=True, filename=latest_file)
        except OSError:
            return Response({"detail": "File not found on disk"}, status=status.HTTP_410_GONE)
            
    except Exception as e:
        return Response({"detail": f"Error retrieving result: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)