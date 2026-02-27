"""
Audio Utilities for the Agentic AI Podcast Generator.

This module provides utilities for post-processing audio files,
including stitching segments and adding transitions.
"""

from pathlib import Path
from typing import List, Optional
import os

# FFmpeg configuration removed as we now use the built-in wave library for stitching.

def stitch_audio_files(
    audio_files: List[str],
    output_path: str = "output/final_podcast.wav",
    silence_duration_ms: int = 500,
    crossfade_ms: int = 0
) -> dict:
    """
    [DEPRECATED] Stitch multiple audio files into a single podcast file.
    Use stitch_audio_segments from tools.stitch_tool instead.
    """
    from tools.stitch_tool import stitch_audio_segments
    # Redirect to the new tool which uses the wave library template
    return stitch_audio_segments(
        output_dir=str(Path(output_path).parent),
        silence_duration_ms=silence_duration_ms,
        output_filename=Path(output_path).name
    )


def add_intro_outro(
    podcast_path: str,
    intro_path: Optional[str] = None,
    outro_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> dict:
    """
    Add intro and outro music to a podcast file.
    
    Args:
        podcast_path (str): Path to the main podcast audio file.
        intro_path (str, optional): Path to intro music file.
        outro_path (str, optional): Path to outro music file.
        output_path (str, optional): Output path. Defaults to replacing input.
    
    Returns:
        dict: Status and output path information.
    """
    try:
        from pydub import AudioSegment
        
        podcast = AudioSegment.from_wav(podcast_path)
        
        if intro_path and os.path.exists(intro_path):
            intro = AudioSegment.from_file(intro_path)
            # Fade out intro
            intro = intro.fade_out(1000)
            podcast = intro + podcast
        
        if outro_path and os.path.exists(outro_path):
            outro = AudioSegment.from_file(outro_path)
            # Fade in outro
            outro = outro.fade_in(1000)
            podcast = podcast + outro
        
        final_path = output_path or podcast_path
        podcast.export(final_path, format="wav")
        
        return {
            "status": "success",
            "output_path": final_path,
            "total_duration_seconds": round(len(podcast) / 1000, 2)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_audio_info(file_path: str) -> dict:
    """
    Get information about an audio file.
    
    Args:
        file_path (str): Path to the audio file.
    
    Returns:
        dict: Audio file information including duration, channels, etc.
    """
    try:
        from pydub import AudioSegment
        
        audio = AudioSegment.from_file(file_path)
        
        return {
            "status": "success",
            "file_path": file_path,
            "duration_seconds": round(len(audio) / 1000, 2),
            "channels": audio.channels,
            "sample_width": audio.sample_width,
            "frame_rate": audio.frame_rate,
            "frame_count": int(audio.frame_count())
        }
        
    except Exception as e:
        return {
            "status": "error",
            "file_path": file_path,
            "error": str(e)
        }
