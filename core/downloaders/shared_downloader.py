"""
Shared downloader module for YouTube audio and video downloads.

This module provides unified functionality for downloading both audio and video
content from YouTube, with database logging and JSON artifact saving.
"""

import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Literal
from yt_dlp import YoutubeDL

from ..shared_utils.path_utils import resolve_path
from ..shared_utils.app_config import APP_CONFIG
from ..shared_utils.url_utils import YouTubeURLSanitizer, YouTubeURLError

# Initialize logger for this module
import logging
logger = logging.getLogger("shared_downloader")

# Download types
DownloadType = Literal["audio", "video"]

class DownloadJob:
    """Represents a download job with tracking and metadata."""
    
    def __init__(self, url: str, download_type: DownloadType, output_dir: Optional[str] = None):
        self.job_id = str(uuid.uuid4())
        self.url = url
        self.download_type = download_type
        self.output_dir = output_dir or os.getcwd()
        self.status = "pending"
        self.created_at = datetime.now()
        self.completed_at = None
        self.filepath = None
        self.filename = None
        self.file_size = None
        self.error = None
        self.metadata = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "url": self.url,
            "download_type": self.download_type,
            "output_dir": self.output_dir,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "filepath": self.filepath,
            "filename": self.filename,
            "file_size": self.file_size,
            "error": self.error,
            "metadata": self.metadata
        }

def sanitize_download_url(url: str) -> str:
    """
    Sanitize and validate YouTube URL before download.
    
    Args:
        url: Raw YouTube URL to sanitize
        
    Returns:
        Clean, standardized YouTube URL
        
    Raises:
        ValueError: If URL is invalid or not a YouTube URL
    """
    try:
        logger.debug(f"Sanitizing URL: {url}")
        url_info = YouTubeURLSanitizer.sanitize_url(url, preserve_metadata=True)
        logger.debug(f"URL sanitized successfully: {url_info.clean_url}")
        return url_info.clean_url
    except YouTubeURLError as e:
        error_msg = f"Invalid YouTube URL: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def get_file_info(filepath: str) -> Dict[str, Any]:
    """
    Get file information for JSON responses.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Dictionary with file information
    """
    if not filepath or not os.path.exists(filepath):
        return {
            'filename': None,
            'filepath': None,
            'size_bytes': 0,
            'size_mb': 0.0,
            'exists': False
        }
    
    try:
        stat = os.stat(filepath)
        size_bytes = stat.st_size
        size_mb = round(size_bytes / (1024 * 1024), 2)
        
        return {
            'filename': os.path.basename(filepath),
            'filepath': filepath,
            'size_bytes': size_bytes,
            'size_mb': size_mb,
            'exists': True
        }
    except Exception as e:
        logger.error(f"Error getting file info for {filepath}: {e}")
        return {
            'filename': os.path.basename(filepath) if filepath else None,
            'filepath': filepath,
            'size_bytes': 0,
            'size_mb': 0.0,
            'exists': False
        }

def get_format_selector(download_type: DownloadType) -> str:
    """Get the appropriate format selector for the download type."""
    if download_type == "audio":
        return "bestaudio/best"
    elif download_type == "video":
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]/best[ext=mp4]/best"
    else:
        raise ValueError(f"Invalid download type: {download_type}")

def get_ydl_options(download_type: DownloadType, output_template: str) -> Dict[str, Any]:
    """Get yt-dlp options for the specified download type."""
    base_options = {
        "format": get_format_selector(download_type),
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
        "restrictfilenames": True,
    }
    
    if download_type == "video":
        base_options["merge_output_format"] = "mp4"
    
    return base_options

def save_artifact(job: DownloadJob, info: Dict[str, Any]) -> str:
    """Save download metadata as JSON artifact."""
    artifact_filename = f"{job.job_id}_metadata.json"
    artifact_path = Path(job.output_dir) / artifact_filename
    
    artifact_data = {
        "job_info": job.to_dict(),
        "video_info": {
            "title": info.get("title", ""),
            "uploader": info.get("uploader", ""),
            "duration": info.get("duration", 0),
            "view_count": info.get("view_count", 0),
            "upload_date": info.get("upload_date", ""),
            "description": info.get("description", ""),
            "tags": info.get("tags", []),
            "categories": info.get("categories", []),
        },
        "download_info": {
            "format": info.get("format", ""),
            "filesize": info.get("filesize", 0),
            "fps": info.get("fps", 0),
            "width": info.get("width", 0),
            "height": info.get("height", 0),
        }
    }
    
    try:
        with open(artifact_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved artifact: {artifact_path}")
        return str(artifact_path)
    except Exception as e:
        logger.error(f"Failed to save artifact: {e}")
        return ""

def log_to_database(job: DownloadJob, user=None, user_ip=None, user_agent=None, download_source='api', task_id=None) -> bool:
    """
    Log download job to database with full tracking information.
    
    Args:
        job: DownloadJob instance with job details
        user: Django User instance (required for database logging)
        user_ip: User's IP address
        user_agent: User's browser/agent string
        download_source: Source of download ('api', 'website', 'api_async')
        task_id: Background task ID for async jobs
    
    Returns:
        bool: True if logging successful, False otherwise
    """
    try:
        # Only proceed if we have Django context (user available)
        if not user:
            logger.debug(f"Database log skipped - no user context: {job.to_dict()}")
            return True
        
        # Import Django models here to avoid circular imports
        from audio_dl.models import DownloadJob as DBJob, JobMetadata
        
        # Create or update database job record
        db_job, created = DBJob.objects.update_or_create(
            job_id=job.job_id,
            defaults={
                'task_id': task_id,
                'user': user,
                'url': job.url,
                'download_type': job.download_type,
                'status': job.status,
                'filename': job.filename,
                'filepath': job.filepath,
                'file_size': job.file_size,
                'error_message': job.error,
                'user_ip': user_ip,
                'user_agent': user_agent,
                'download_source': download_source,
                'started_at': job.created_at if job.status == 'downloading' else None,
                'completed_at': job.completed_at,
            }
        )
        
        # Create metadata record if we have metadata
        if job.metadata and created:
            JobMetadata.objects.create(
                job=db_job,
                title=job.metadata.get('title'),
                duration=job.metadata.get('duration'),
                uploader=job.metadata.get('uploader'),
                upload_date=job.metadata.get('upload_date'),
                view_count=job.metadata.get('view_count'),
                like_count=job.metadata.get('like_count'),
                format_id=job.metadata.get('format_id'),
                ext=job.metadata.get('ext'),
                vcodec=job.metadata.get('vcodec'),
                acodec=job.metadata.get('acodec'),
                filesize=job.metadata.get('filesize'),
                fps=job.metadata.get('fps'),
                raw_metadata=job.metadata,
            )
        elif job.metadata and not created:
            # Update existing metadata
            metadata, _ = JobMetadata.objects.get_or_create(job=db_job)
            metadata.title = job.metadata.get('title')
            metadata.duration = job.metadata.get('duration')
            metadata.uploader = job.metadata.get('uploader')
            metadata.upload_date = job.metadata.get('upload_date')
            metadata.view_count = job.metadata.get('view_count')
            metadata.like_count = job.metadata.get('like_count')
            metadata.format_id = job.metadata.get('format_id')
            metadata.ext = job.metadata.get('ext')
            metadata.vcodec = job.metadata.get('vcodec')
            metadata.acodec = job.metadata.get('acodec')
            metadata.filesize = job.metadata.get('filesize')
            metadata.fps = job.metadata.get('fps')
            metadata.raw_metadata = job.metadata
            metadata.save()
        
        logger.debug(f"Database job {'created' if created else 'updated'}: {db_job.job_id} - {job.status}")
        return True
        
    except Exception as e:
        logger.error(f"Database logging failed for job {job.job_id}: {e}")
        return False

def download_media(url: str, download_type: DownloadType, output_dir: Optional[str] = None, user=None, user_ip=None, user_agent=None, download_source='api', task_id=None) -> Dict[str, Any]:
    """
    Download audio or video from YouTube URL with full tracking and logging.
    
    Args:
        url: YouTube URL to download
        download_type: "audio" or "video"
        output_dir: Directory to save file (defaults to current working directory)
    
    Returns:
        dict: {
            'success': bool,
            'job_id': str,
            'filepath': str or None,
            'filename': str or None,
            'artifact_path': str or None,
            'error': str or None,
            'metadata': dict
        }
    """
    logger.info(f"Starting {download_type} download for: {url}")
    
    # Sanitize and validate URL
    try:
        sanitized_url = sanitize_download_url(url)
        logger.debug(f"Using sanitized URL: {sanitized_url}")
    except ValueError as e:
        logger.error(f"URL validation failed: {e}")
        return {
            'success': False,
            'job_id': str(uuid.uuid4()),
            'filepath': None,
            'filename': None,
            'artifact_path': None,
            'error': str(e),
            'metadata': {}
        }
    
    # Create download job with sanitized URL
    job = DownloadJob(sanitized_url, download_type, output_dir)
    job.status = "downloading"
    
    # Log to database
    log_to_database(job, user=user, user_ip=user_ip, user_agent=user_agent, download_source=download_source, task_id=task_id)
    
    # Ensure output directory exists
    output_path = Path(job.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create output template
    outtmpl = str(output_path / f"%(title)s.%(ext)s")
    
    # Get yt-dlp options
    ydl_opts = get_ydl_options(download_type, outtmpl)
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extract info first to get metadata
            info = ydl.extract_info(url, download=False)
            job.metadata = info
            
            # Now download
            ydl.download([url])
            
            # Get the actual filepath
            filepath = ydl.prepare_filename(info)
            
        # Check if file was actually created
        if not filepath or not os.path.exists(filepath):
            job.status = "failed"
            job.error = "Download failed - file not created"
            job.completed_at = datetime.now()
            log_to_database(job, user=user, user_ip=user_ip, user_agent=user_agent, download_source=download_source, task_id=task_id)
            
            return {
                'success': False,
                'job_id': job.job_id,
                'filepath': None,
                'filename': None,
                'artifact_path': None,
                'error': job.error,
                'metadata': job.metadata
            }
        
        # Update job with success info
        job.status = "completed"
        job.filepath = filepath
        job.filename = os.path.basename(filepath)
        job.completed_at = datetime.now()
        
        # Calculate file size
        try:
            job.file_size = os.path.getsize(filepath)
        except OSError:
            job.file_size = 0
        
        # Save artifact
        artifact_path = save_artifact(job, info)
        
        # Final database log
        log_to_database(job, user=user, user_ip=user_ip, user_agent=user_agent, download_source=download_source, task_id=task_id)
        
        logger.info(f"Successfully downloaded {download_type}: {job.filename}")
        
        return {
            'success': True,
            'job_id': job.job_id,
            'filepath': job.filepath,
            'filename': job.filename,
            'artifact_path': artifact_path,
            'error': None,
            'metadata': job.metadata
        }
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.completed_at = datetime.now()
        log_to_database(job, user=user, user_ip=user_ip, user_agent=user_agent, download_source=download_source, task_id=task_id)
        
        logger.error(f"Download failed: {e}")
        
        return {
            'success': False,
            'job_id': job.job_id,
            'filepath': None,
            'filename': None,
            'artifact_path': None,
            'error': job.error,
            'metadata': job.metadata
        }

def download_audio(url: str, output_dir: Optional[str] = None, user=None, user_ip=None, user_agent=None, download_source='api', task_id=None) -> Dict[str, Any]:
    """Download audio from YouTube URL."""
    return download_media(url, "audio", output_dir, user=user, user_ip=user_ip, user_agent=user_agent, download_source=download_source, task_id=task_id)

def download_video(url: str, output_dir: Optional[str] = None, user=None, user_ip=None, user_agent=None, download_source='api', task_id=None) -> Dict[str, Any]:
    """Download video from YouTube URL."""
    return download_media(url, "video", output_dir, user=user, user_ip=user_ip, user_agent=user_agent, download_source=download_source, task_id=task_id)

if __name__ == "__main__":
    # Test the downloader
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python shared_downloader.py <audio|video> <YouTube URL> [output_dir]")
        sys.exit(1)
    
    download_type = sys.argv[1]
    url = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    if download_type not in ["audio", "video"]:
        print("Download type must be 'audio' or 'video'")
        sys.exit(1)
    
    result = download_media(url, download_type, output_dir)
    
    if result['success']:
        print(f"Download successful!")
        print(f"Job ID: {result['job_id']}")
        print(f"File: {result['filename']}")
        print(f"Artifact: {result['artifact_path']}")
    else:
        print(f"Download failed: {result['error']}")
        sys.exit(1)
