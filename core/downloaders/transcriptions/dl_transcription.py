"""
core.py

Core download functions for YouTube content using yt-dlp and transcript APIs.
Handles download of audio (mp3), video (mp4), and video transcripts.

Dependencies:
- yt_dlp
- youtube_transcript_api
"""
import sys
from typing import List, Dict, Any, Optional, Tuple
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Import logging
from .logger_utils.logger_utils import setup_logger

# Setup logger for this module
logger = setup_logger("core")

# -------------------- Core Functions --------------------

def get_video_info(url: str) -> Optional[Dict]:
    logger.debug(f"Extracting video info for URL: {url}")
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.debug(f"Extracted info for video: {info.get('title', 'Unknown title')} (ID: {info.get('id', 'Unknown ID')})")
            logger.debug(f"Found {len(info.get('formats', []))} formats")
            return info
    except Exception as e:
        logger.error(f"Failed to extract video info for {url}: {e}")
        return None


# -------------------- Transcript Metadata --------------------

def _get_transcript_list(video_id: str):
    """Utility function to get transcript list with API compatibility handling."""
    try:
        api = YouTubeTranscriptApi()
        return api.list(video_id)
    except AttributeError:
        return YouTubeTranscriptApi.list(video_id)


def list_transcript_metadata(video_id: str) -> List[Dict[str, Any]]:
    logger.debug(f"Listing transcript metadata for video_id: {video_id}")
    try:
        transcript_list = _get_transcript_list(video_id)
    except Exception as e:
        logger.error(f"Failed to get transcript list for {video_id}: {e}")
        return []

    meta = []
    for t in transcript_list:
        is_generated = getattr(t, "is_generated", False)
        language_code = getattr(t, "language_code", None)
        
        # Better default detection: manual transcripts are preferred, then English auto-generated
        is_default = (not is_generated) or (is_generated and language_code in ['en', 'en-US', 'en-GB'])
        
        transcript_meta = {
            "language_code": language_code,
            "language": getattr(t, "language", None),
            "is_generated": is_generated,
            "is_translatable": getattr(t, "is_translatable", None),
            "can_translate_to": getattr(t, "translation_languages", []),
            "is_default": is_default
        }
        
        logger.debug(f"Transcript metadata: {transcript_meta}")
        meta.append(transcript_meta)
    
    logger.debug(f"Total transcripts found: {len(meta)}")
    return meta


def print_and_select_default_transcript(video_id: str, preferred_language: Optional[str] = None) -> Optional[Dict[str, Any]]:
    logger.debug(f"Starting transcript discovery for video_id: {video_id}, preferred_language: {preferred_language}")
    
    # If no preferred language provided, check config for default preference
    if not preferred_language:
        try:
            from .utils.path_utils import load_config
            config = load_config()
            config_languages = config.get("transcripts", {}).get("preferred_languages", [])
            if config_languages:
                preferred_language = config_languages[0]  # Use first preferred language from config
                logger.debug(f"Using preferred language from config: {preferred_language}")
        except Exception as e:
            logger.debug(f"Could not load config for language preference: {e}")
    
    print("\nTranscript Info")
    print("-" * 40)
    try:
        rows = list_transcript_metadata(video_id)
        logger.debug(f"Found {len(rows)} transcript metadata rows")
        
        if not rows:
            logger.warning("No transcripts found")
            print("No transcripts found.")
            return None

        default_transcript = None
        manual_transcripts = []
        auto_generated_transcripts = []
        
        for i, r in enumerate(rows):
            logger.debug(f"Transcript {i}: {r}")
            
            # Categorize transcripts
            if not r["is_generated"]:
                manual_transcripts.append(r)
                logger.debug(f"Found manual transcript: {r['language_code']} - {r['language']}")
            else:
                auto_generated_transcripts.append(r)
                logger.debug(f"Found auto-generated transcript: {r['language_code']} - {r['language']}")
            
            tag = "[DEFAULT]" if r["is_default"] else ""
            print(
                f"{(r['language_code'] or '-'): <8} | "
                f"{(r['language'] or '-'): <24} | "
                f"generated: {r['is_generated']} | "
                f"translatable: {r['is_translatable']} {tag}"
            )
            if r["is_default"]:
                default_transcript = r
                logger.debug(f"Found explicit default transcript: {r}")

        # Enhanced selection logic with language preference priority
        if not default_transcript:
            logger.debug("No explicit default found, applying enhanced fallback logic")
            all_transcripts = manual_transcripts + auto_generated_transcripts
            
            # Priority 1: Check for preferred language (from CLI --lang or config)
            if preferred_language:
                preferred_transcript = next((t for t in all_transcripts if t['language_code'] == preferred_language), None)
                if preferred_transcript:
                    default_transcript = preferred_transcript
                    logger.info(f"Selected preferred language transcript: {preferred_transcript['language']} ({preferred_transcript['language_code']})")
            
            # Priority 2: Prefer manual transcripts over auto-generated (if no preferred language match)
            if not default_transcript and manual_transcripts:
                default_transcript = manual_transcripts[0]
                logger.debug(f"Selected first manual transcript as default: {default_transcript}")
            
            # Priority 3: Look for English auto-generated
            elif not default_transcript and auto_generated_transcripts:
                english_auto = next((t for t in auto_generated_transcripts if t['language_code'] in ['en', 'en-US', 'en-GB']), None)
                if english_auto:
                    default_transcript = english_auto
                    logger.debug(f"Selected English auto-generated transcript as default: {default_transcript}")
                else:
                    # Priority 4: Fallback to first available auto-generated
                    default_transcript = auto_generated_transcripts[0]
                    logger.debug(f"Selected first auto-generated transcript as default: {default_transcript}")

        if default_transcript:
            logger.info(f"Final selected transcript: {default_transcript['language']} ({default_transcript['language_code']})")
            print(f"\nSelected default transcript: {default_transcript['language']} ({default_transcript['language_code']})")
        else:
            logger.warning("No suitable transcript found for selection")
            print("\nNo suitable transcript found.")

        return default_transcript

    except (TranscriptsDisabled, NoTranscriptFound):
        print("Transcripts are disabled or not found for this video.")
        return None
    except Exception as e:
        print(f"Error fetching transcript info: {e}")
        return None


def preview_transcript(video_id: str, language_code: str = None, include_metadata: bool = True) -> Optional[Dict[str, Any]]:
    """
    Generate a preview of transcript content without downloading.
    
    Args:
        video_id: YouTube video ID
        language_code: Specific language code, or None to use default selection
        include_metadata: Whether to include rich metadata analysis
    
    Returns:
        Dictionary with preview information, or None if not available
    """
    logger.debug(f"Generating transcript preview for video_id: {video_id}, language: {language_code}")
    
    try:
        from .transcript_processor import TranscriptProcessor
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
        
        # If no language specified, find the default
        if language_code is None:
            default_transcript = print_and_select_default_transcript(video_id, preferred_language=None)
            if not default_transcript:
                return None
            language_code = default_transcript.get('language_code')
        
        # Fetch transcript data
        transcript_list = _get_transcript_list(video_id)
        transcript_data = None
        
        for transcript in transcript_list:
            if hasattr(transcript, 'language_code') and transcript.language_code == language_code:
                transcript_data = transcript.fetch()
                logger.debug(f"✅ Found transcript for preview using transcript list method")
                break
        
        if not transcript_data:
            # Fallback method
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[language_code])
                logger.debug(f"✅ Found transcript for preview using get_transcript fallback method")
            except Exception:
                logger.warning(f"No transcript available for preview")
                return None
        
        if not transcript_data:
            return None
        
        # Generate basic preview using processor
        processor = TranscriptProcessor()
        preview_data = processor.generate_preview(transcript_data)
        preview_data['language_code'] = language_code
        preview_data['video_id'] = video_id
        
        # Add rich metadata if requested
        if include_metadata:
            try:
                from .metadata_collector import MetadataCollector
                from .utils.path_utils import load_config
                
                config = load_config()
                if config.get("metadata_collection", {}).get("enabled", True):
                    collector = MetadataCollector(config)
                    
                    # Analyze transcript content
                    transcript_analysis = collector.analyze_transcript_content(transcript_data)
                    
                    # Add content insights to preview
                    if transcript_analysis.get('content_analysis'):
                        content_analysis = transcript_analysis['content_analysis']
                        preview_data['content_insights'] = {
                            'keywords': [kw['keyword'] for kw in content_analysis.get('keywords', [])[:5]],
                            'topics': content_analysis.get('topics', [])[:3],
                            'content_category': content_analysis.get('content_type', {}).get('primary_category', 'Unknown'),
                            'language_detected': content_analysis.get('language_analysis', {}).get('detected_language', 'Unknown')
                        }
                    
                    # Add quality insights
                    if transcript_analysis.get('quality_assessment'):
                        quality = transcript_analysis['quality_assessment']
                        preview_data['quality_insights'] = {
                            'quality_score': quality.get('quality_score', 0),
                            'quality_category': quality.get('quality_category', 'Unknown'),
                            'artifact_ratio': quality.get('artifact_ratio', 0)
                        }
                    
                    # Add content metrics
                    if transcript_analysis.get('content_metrics'):
                        metrics = transcript_analysis['content_metrics']
                        preview_data['content_metrics'] = {
                            'speaking_rate_wpm': metrics.get('speaking_rate_wpm', 0),
                            'lexical_diversity': round(metrics.get('lexical_diversity', 0), 2),
                            'readability': transcript_analysis.get('content_analysis', {}).get('language_analysis', {}).get('readability_level', 'Unknown')
                        }
                    
                    logger.debug("Enhanced preview with metadata insights")
                
            except Exception as e:
                logger.warning(f"Could not add metadata insights to preview: {e}")
                # Continue without metadata - basic preview is still useful
        
        logger.info(f"✅ Transcript preview generated for {video_id} ({language_code})")
        return preview_data
        
    except (TranscriptsDisabled, NoTranscriptFound):
        logger.warning(f"Transcripts are disabled or not found for video {video_id}")
        return None
    except Exception as e:
        logger.error(f"Error generating transcript preview: {str(e)}")
        return None


def print_transcript_preview(video_id: str, language_code: str = None):
    """Print enhanced transcript preview to console."""
    preview = preview_transcript(video_id, language_code)
    
    if not preview:
        print("❌ No transcript preview available")
        return
    
    print(f"\n📄 Transcript Preview ({preview.get('language_code', 'unknown')})")
    print("-" * 60)
    print(preview['preview_text'])
    
    if 'statistics' in preview:
        stats = preview['statistics']
        print(f"\n📊 Statistics:")
        print(f"   • Word count: {stats['word_count']:,}")
        print(f"   • Character count: {stats['character_count']:,}")
        print(f"   • Estimated reading time: {stats['estimated_reading_time_minutes']} minutes")
    
    if 'quality_indicators' in preview:
        quality = preview['quality_indicators']
        print(f"\n🔍 Quality Indicators:")
        print(f"   • Quality estimate: {quality['quality_estimate']}")
        print(f"   • Average entry length: {quality['average_entry_length']:.1f} characters")
        print(f"   • Has timestamps: {'Yes' if quality['has_timestamps'] else 'No'}")
    
    # 🆕 Enhanced metadata display
    if 'content_insights' in preview:
        insights = preview['content_insights']
        print(f"\n🎯 Content Insights:")
        print(f"   • Category: {insights.get('content_category', 'Unknown')}")
        print(f"   • Language: {insights.get('language_detected', 'Unknown')}")
        if insights.get('keywords'):
            print(f"   • Key topics: {', '.join(insights['keywords'])}")
        if insights.get('topics'):
            print(f"   • Main subjects: {', '.join(insights['topics'])}")
    
    if 'quality_insights' in preview:
        quality_insights = preview['quality_insights']
        print(f"\n🎖️ Quality Assessment:")
        print(f"   • Overall quality: {quality_insights.get('quality_category', 'Unknown')} ({quality_insights.get('quality_score', 0):.1f}/100)")
        artifact_ratio = quality_insights.get('artifact_ratio', 0)
        if artifact_ratio > 0:
            print(f"   • Artifact ratio: {artifact_ratio:.1%}")
    
    if 'content_metrics' in preview:
        metrics = preview['content_metrics']
        print(f"\n📈 Content Metrics:")
        if metrics.get('speaking_rate_wpm', 0) > 0:
            print(f"   • Speaking rate: {metrics['speaking_rate_wpm']} words/minute")
        print(f"   • Readability: {metrics.get('readability', 'Unknown')}")
        print(f"   • Lexical diversity: {metrics.get('lexical_diversity', 0):.2f}")
    
    print(f"\n💾 Total entries available: {preview['total_entries']}")
    
    # 🆕 LLM suitability indicator
    if 'quality_insights' in preview and 'statistics' in preview:
        quality_score = preview['quality_insights'].get('quality_score', 0)
        word_count = preview['statistics'].get('word_count', 0)
        
        if quality_score >= 80 and 100 <= word_count <= 3000:
            print(f"✅ Excellent for LLM analysis")
        elif quality_score >= 70 and 50 <= word_count <= 5000:
            print(f"✅ Good for LLM analysis")
        elif quality_score >= 60:
            print(f"⚠️ Fair for LLM analysis - may need cleaning")
        else:
            print(f"❌ Poor quality - manual review recommended")


# -------------------- Display Helpers --------------------

def print_basic_info(info: Optional[Dict]):
    """Print basic video information with defensive None handling."""
    if info is None:
        print("\n❌ No video information available")
        return
        
    print("\nVideo Metadata")
    print("-" * 40)
    print(f"Title       : {info.get('title', 'Unknown')}")
    print(f"Uploader    : {info.get('uploader', 'Unknown')}")
    print(f"Duration    : {info.get('duration', 0)} seconds")
    print(f"View Count  : {info.get('view_count', 'Unknown')}")
    print(f"Upload Date : {info.get('upload_date', 'Unknown')}")
    description = info.get('description', '')
    if description:
        print(f"Description : {description[:300]}...\n")
    else:
        print(f"Description : No description available\n")


# -------------------- Main Entry Point --------------------

def main():
    print("=== YouTube Video Info Fetcher ===")
    url = input("Enter YouTube video URL: ").strip()
    if not url:
        print("URL cannot be empty.")
        return

    try:
        info = get_video_info(url)
        print_basic_info(info)

        if info is None:
            print("❌ Cannot proceed without video information. Please check the URL and try again.")
            sys.exit(1)

        formats = info.get('formats', [])

        default_transcript = print_and_select_default_transcript(info.get("id"), preferred_language=None)

        if default_transcript:
            print(f"Default transcript language: {default_transcript.get('language')}")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
