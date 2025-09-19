# save as: download_audio.py
import sys
import os
import tempfile
from yt_dlp import YoutubeDL

def download_audio(url: str, output_dir: str = None) -> dict:
    """
    Download audio from YouTube URL.
    
    Args:
        url: YouTube URL to download
        output_dir: Directory to save file (defaults to temp directory)
    
    Returns:
        dict: {
            'success': bool,
            'filepath': str or None,
            'filename': str or None,
            'error': str or None
        }
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="yt_")
    
    outtmpl = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
        
        # Check if file was actually created
        if not filepath or not os.path.exists(filepath):
            return {
                'success': False,
                'filepath': None,
                'filename': None,
                'error': 'Download failed - file not created'
            }
        
        filename = os.path.basename(filepath)
        
        return {
            'success': True,
            'filepath': filepath,
            'filename': filename,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'filepath': None,
            'filename': None,
            'error': str(e)
        }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python download_audio.py <YouTube URL>")
        sys.exit(1)
    
    result = download_audio(sys.argv[1])
    if result['success']:
        print(f"Downloaded: {result['filename']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)
