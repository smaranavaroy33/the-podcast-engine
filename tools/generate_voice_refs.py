"""
Generate Voice Reference Audio Clips for Podcast Hosts.

This script uses edge-tts (Microsoft's free TTS service) to create
short reference audio clips that Chatterbox uses for voice cloning:
  - Host: A lovely, warm female voice
  - Expert: A confident, authoritative male voice

Usage:
    python tools/generate_voice_refs.py

The reference clips are saved to voice_references/ and are automatically
picked up by chatterbox_tool.py during podcast generation.
"""

import asyncio
import os
from pathlib import Path


# Voice configuration
# edge-tts voice IDs: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support
VOICE_CONFIGS = {
    "host": {
        "voice": "en-US-AvaNeural",      # Expressive, Friendly female voice
        "text": (
            "Hey everyone! Welcome back to the show. I'm really, really excited "
            "to dive into today's topic. It's something that's been on my mind "
            "for a while, you know? So, yeah... I've brought in a real expert to "
            "help us break it all down. Let's get into it!"
        ),
        "filename": "host_female_ref.wav",
    },
    "expert": {
        "voice": "en-US-AndrewNeural",    # Warm, Confident, Authentic male voice
        "text": (
            "Thanks for the warm intro. You know, it's actually a pretty complex "
            "subject, but... well, I think we can make it really approachable. "
            "There's a lot of nuance here that people often miss, and I'm looking "
            "forward to sharing some of those insights today."
        ),
        "filename": "expert_male_ref.wav",
    },
}


async def generate_reference_clips(output_dir: str = "voice_references"):
    """Generate reference audio clips using edge-tts and convert to WAV."""
    try:
        import edge_tts
    except ImportError:
        print("edge-tts not installed. Installing...")
        os.system("pip install edge-tts")
        import edge_tts

    import torchaudio as ta

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for role, config in VOICE_CONFIGS.items():
        filepath = output_path / config["filename"]

        if filepath.exists():
            print(f"  [SKIP] {role} reference already exists: {filepath}")
            continue

        print(f"  [GEN]  Generating {role} reference with voice '{config['voice']}'...")

        # edge-tts outputs MP3 — save to a temp file first, then convert to WAV
        mp3_path = filepath.with_suffix(".mp3")
        communicate = edge_tts.Communicate(config["text"], config["voice"])
        await communicate.save(str(mp3_path))

        # Convert MP3 → WAV using torchaudio (already available in environment)
        waveform, sample_rate = ta.load(str(mp3_path))
        ta.save(str(filepath), waveform, sample_rate)
        mp3_path.unlink()  # Clean up the temp MP3

        duration_ms = int(waveform.shape[-1] / sample_rate * 1000)
        print(f"  [OK]   Saved to {filepath} (WAV, {duration_ms}ms, {sample_rate}Hz)")

    print("\nVoice reference generation complete!")
    print(f"Files are in: {output_path.absolute()}")




def main():
    print("=" * 50)
    print("  Voice Reference Generator")
    print("=" * 50)
    asyncio.run(generate_reference_clips())


if __name__ == "__main__":
    main()
