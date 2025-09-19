# save as: download_audio.py
import sys
from ..shared_downloader import download_audio as shared_download_audio

def download_audio(url: str, output_dir: str = None) -> dict:
    """
    Download audio from YouTube URL using shared downloader.
    
    Args:
        url: YouTube URL to download
        output_dir: Directory to save file (defaults to current working directory)
    
    Returns:
        dict: {
            'success': bool,
            'filepath': str or None,
            'filename': str or None,
            'error': str or None
        }
    """
    result = shared_download_audio(url, output_dir)
    
    # Return in the original format for backward compatibility
    return {
        'success': result['success'],
        'filepath': result['filepath'],
        'filename': result['filename'],
        'error': result['error']
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
