"""
Audio Stitching Tool for the Agentic AI Podcast Generator.

This tool stitches individual audio segment files into a single
final podcast file using the built-in wave library.
"""

import os
import wave
from pathlib import Path
from typing import Optional


def stitch_audio_segments(
    output_dir: str = "output",
    silence_duration_ms: int = 500,
    output_filename: str = "final_podcast.wav"
) -> dict:
    """
    Stitch all audio segment files in a directory into a single podcast file.

    Scans the given output directory recursively for files matching the pattern
    ``segment_*.wav``, sorts them by name (which preserves index order),
    and combines them into one WAV file using the wave library.
    The individual segment files are kept intact.

    Args:
        output_dir (str): Directory containing the segment WAV files
                          (default: "output").
        silence_duration_ms (int): Ignored in this implementation.
        output_filename (str): Name of the final stitched file
                               (default: "final_podcast.wav").

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - output_path: Absolute path to the final podcast file
            - total_duration_seconds: Total duration in seconds
            - num_segments: Number of segments that were combined
            - segment_files: List of segment file paths that were used
    """
    try:
        output_path = Path(output_dir)
        if not output_path.exists():
            return {
                "status": "error",
                "error": f"Output directory does not exist: {output_dir}"
            }

        # Discover and sort segment files
        # We convert to list and sort to ensure a consistent, predictable order
        all_wavs = list(output_path.rglob("segment_*.wav"))
        segment_files = sorted(all_wavs, key=lambda p: p.name)

        if not segment_files:
            return {
                "status": "error",
                "error": f"No segment_*.wav files found in {output_dir} or its subdirectories."
            }

        final_output_path = output_path / output_filename
        
        # Ensure we don't try to read the file we are currently writing to
        # (though rglob("segment_*.wav") shouldn't match "final_podcast.wav")
        segment_files = [f for f in segment_files if f.absolute() != final_output_path.absolute()]

        total_duration_seconds = 0
        successful_segments = []
        
        # We first open the output file
        with wave.open(str(final_output_path), 'wb') as outfile:
            params_set = False
            
            for file_path in segment_files:
                try:
                    with wave.open(str(file_path), 'rb') as infile:
                        params = infile.getparams()
                        
                        # Validate that the file has channels and frames
                        if params.nchannels == 0:
                            print(f"Warning: Skipping {file_path} because it has 0 channels.")
                            continue
                        
                        if not params_set:
                            # Set parameters based on the first valid file
                            outfile.setparams(params)
                            params_set = True
                        
                        # Write frames to output
                        frames = infile.readframes(params.nframes)
                        outfile.writeframes(frames)
                        
                        # Calculate duration
                        total_duration_seconds += params.nframes / params.framerate
                        successful_segments.append(str(file_path.absolute()))
                        
                except Exception as e:
                    print(f"Warning: Failed to process {file_path}: {e}")
                    continue

            if not params_set:
                return {
                    "status": "error",
                    "error": "Could not set audio parameters. No valid wave segments were found."
                }

        return {
            "status": "success",
            "output_path": str(final_output_path.absolute()),
            "total_duration_seconds": round(total_duration_seconds, 2),
            "num_segments": len(successful_segments),
            "segment_files": successful_segments
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Internal error during audio stitching: {str(e)}"
        }
