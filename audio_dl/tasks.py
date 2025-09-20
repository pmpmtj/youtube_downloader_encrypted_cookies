"""Background tasks for audio downloads (django-background-tasks).

This module defines a single task function that can be enqueued via
django-background-tasks. It downloads the YouTube audio to MEDIA_ROOT/downloads/audio.
"""

from pathlib import Path
from typing import Dict, Any
from background_task import background

from django.conf import settings

# Reuse your existing core downloader
# (keeps behavior identical between sync and async paths)
from core.downloaders.audio.download_audio import download_audio
from core.shared_utils.url_utils import YouTubeURLSanitizer, YouTubeURLError


@background(schedule=0)  # Run immediately
def process_youtube_audio(url: str, task_id: str = None):
    """Download audio for the given URL into MEDIA_ROOT/downloads/audio.
    
    Args:
        url: YouTube URL to download
        task_id: Optional task identifier for tracking
    """
    try:
        # Validate YouTube URL before processing
        if not YouTubeURLSanitizer.is_youtube_url(url):
            print(f"Background task {task_id} failed: Invalid YouTube URL")
            return

        # Ensure output directory exists
        output_dir = Path(settings.MEDIA_ROOT) / 'downloads' / 'audio'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Delegate to the shared downloader (URL sanitization happens there)
        result = download_audio(url, output_dir=str(output_dir))

        # Log the result (you could store this in a custom model for better tracking)
        if result and result.get('success'):
            print(f"Background task {task_id} completed successfully: {result.get('filename')}")
        else:
            print(f"Background task {task_id} failed: {result.get('error') if result else 'Unknown error'}")
            
    except Exception as e:
        print(f"Background task {task_id} encountered an exception: {str(e)}")
