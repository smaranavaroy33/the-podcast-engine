"""
Chatterbox TTS Tool for the Agentic AI Podcast Generator.

This tool generates audio segments using Chatterbox TTS model with different
voice personas for the podcast hosts:
  - Host:   Lovely, warm FEMALE voice (voice-cloned from reference audio)
  - Expert: Confident, authoritative MALE voice (voice-cloned from reference audio)
"""

import os
import torch
from pathlib import Path
from typing import Optional

# Fix: perth's PerthImplicitWatermarker may be None if its native
# dependency is missing. Patch it with DummyWatermarker so Chatterbox
# can still load and generate audio (just without watermarking).
try:
    import perth
    if perth.PerthImplicitWatermarker is None:
        from perth.dummy_watermarker import DummyWatermarker
        perth.PerthImplicitWatermarker = DummyWatermarker
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Voice Profiles for each speaker
# ---------------------------------------------------------------------------
# Each profile defines the reference audio file for voice cloning and
# Chatterbox generation parameters that shape the voice personality.
#
#   audio_prompt_path : Path to a short (~10 s) reference WAV clip used for
#                       zero-shot voice cloning.
#   exaggeration      : Emotional expressiveness (0.25 – 2.0, default 0.5).
#   cfg_weight        : Classifier-free guidance / pacing (0.0 – 1.0).
#   temperature       : Generation randomness.
# ---------------------------------------------------------------------------

VOICE_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "voice_references"

VOICE_PROFILES = {
    "Host": {
        # Lovely, warm female voice – slightly more expressive & natural
        "ref_filename": "host_female_ref.wav",
        "exaggeration": 0.65,
        "cfg_weight": 0.5,
        "temperature": 0.8,
    },
    "Expert": {
        # Confident, authoritative male voice – steadier, measured delivery
        "ref_filename": "expert_male_ref.wav",
        "exaggeration": 0.4,
        "cfg_weight": 0.6,
        "temperature": 0.75,
    },
}


# Global model cache to avoid reloading
_model_cache = {}


def _ensure_voice_references():
    """
    Auto-generate reference audio clips if they do not exist yet.

    Uses edge-tts (Microsoft's free Neural TTS) to create short reference
    clips that Chatterbox will use for voice cloning.
    """
    VOICE_REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

    all_present = all(
        (VOICE_REFERENCES_DIR / p["ref_filename"]).exists()
        for p in VOICE_PROFILES.values()
    )
    if all_present:
        return  # Nothing to do

    # Import and run the generator
    try:
        import asyncio
        from tools.generate_voice_refs import generate_reference_clips

        print("Voice reference clips not found — generating them now...")
        asyncio.run(generate_reference_clips(str(VOICE_REFERENCES_DIR)))
    except Exception as e:
        print(f"Warning: Could not auto-generate voice references: {e}")
        print("Falling back to default Chatterbox voice for all speakers.")


def get_tts_model(device: Optional[str] = None):
    """
    Get or initialize the Chatterbox TTS model.

    Args:
        device (str, optional): Device to use ('cuda' or 'cpu').
                               Defaults to CUDA/ROCm if available.

    Returns:
        ChatterboxTTS: The initialized TTS model.
    """
    global _model_cache

    if device is None:
        # Check for AMD GPU / ROCm support
        is_rocm = hasattr(torch.version, 'hip')
        
        if is_rocm:
            # Configure ROCm environment for AMD GPUs on Windows/Linux
            # RX 9060 XT is likely RDNA 3/4. GFX 11.0.0 is a safe bet for RDNA 3.
            os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
            os.environ["HIP_VISIBLE_DEVICES"] = "0"
            
            if torch.cuda.is_available():
                device = "cuda"
                print(f"Chatterbox: AMD GPU detected. Utilizing ROCm/HIP acceleration on {torch.cuda.get_device_name(0)}.")
            else:
                # Force cuda even if is_available is false, as env overrides might fix it during model load
                device = "cuda"
                print("Chatterbox: AMD GPU build detected. Forcing ROCm acceleration (CUDA-compatible API).")
        else:
            device = os.getenv(
                "TTS_DEVICE", "cuda" if torch.cuda.is_available() else "cpu"
            )

    if device not in _model_cache:
        try:
            from chatterbox.tts import ChatterboxTTS

            _model_cache[device] = ChatterboxTTS.from_pretrained(device=device)
            print(f"Chatterbox TTS model loaded on {device}")
        except Exception as e:
            # Fallback to CPU if GPU initialization fails
            if device == "cuda":
                print(f"Warning: GPU acceleration failed ({e}). Falling back to CPU.")
                return get_tts_model(device="cpu")
            raise RuntimeError(f"Failed to load Chatterbox TTS model: {e}")

    return _model_cache[device]


def generate_audio_segment(
    text: str,
    speaker: str,
    output_dir: str = "output",
    segment_index: int = 0,
) -> dict:
    """
    Generate an audio segment for a given text using Chatterbox TTS.

    The function selects a voice profile based on the *speaker* parameter:
      - "Host"   → lovely, warm female voice
      - "Expert" → confident, authoritative male voice

    Voice cloning is performed when reference audio is available; otherwise
    Chatterbox falls back to its default voice with per-speaker tuning.

    Args:
        text (str): The text content to convert to speech.
        speaker (str): Speaker identifier — "Host" or "Expert".
        output_dir (str): Directory to save the audio file (default: "output").
        segment_index (int): Index of the segment for filename ordering.

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - file_path: Absolute path to the generated audio file
            - speaker: The speaker identifier
            - duration_estimate: Estimated duration in seconds
    """
    try:
        import torchaudio as ta

        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Make sure voice reference clips are available
        _ensure_voice_references()

        # Get the TTS model
        model = get_tts_model()

        # ---- Build per-speaker generation kwargs ----
        profile = VOICE_PROFILES.get(speaker, VOICE_PROFILES["Host"])

        gen_kwargs = {
            "exaggeration": profile["exaggeration"],
            "cfg_weight": profile["cfg_weight"],
            "temperature": profile["temperature"],
        }

        # Use reference audio for voice cloning when available
        ref_path = VOICE_REFERENCES_DIR / profile["ref_filename"]
        if ref_path.exists():
            gen_kwargs["audio_prompt_path"] = str(ref_path)
            print(
                f"  🎙  [{speaker}] Using voice reference: {ref_path.name} "
                f"(exag={profile['exaggeration']}, cfg={profile['cfg_weight']})"
            )
        else:
            print(
                f"  🎙  [{speaker}] No reference audio — using default voice "
                f"(exag={profile['exaggeration']}, cfg={profile['cfg_weight']})"
            )

        # Generate audio with speaker-specific voice
        wav = model.generate(text, **gen_kwargs)

        # Create filename with speaker and index
        filename = f"segment_{segment_index:03d}_{speaker.lower()}.wav"
        file_path = output_path / filename

        # Ensure wav is a 2D tensor (channels, frames)
        if wav.ndim == 1:
            wav = wav.unsqueeze(0)

        # Convert to 16-bit PCM for maximum compatibility with the wave library
        # Chatterbox output is typically normalized float32
        wav_pcm = (wav * 32767).clamp(-32768, 32767).to(torch.int16)

        # Save the audio file
        ta.save(str(file_path), wav_pcm, model.sr)

        # Estimate duration (samples / sample_rate)
        duration_estimate = wav.shape[-1] / model.sr

        return {
            "status": "success",
            "file_path": str(file_path.absolute()),
            "speaker": speaker,
            "segment_index": segment_index,
            "duration_estimate": round(duration_estimate, 2),
            "sample_rate": model.sr,
        }

    except ImportError as e:
        return {
            "status": "error",
            "error": (
                f"Chatterbox TTS not installed. "
                f"Please run: pip install chatterbox-tts. Error: {e}"
            ),
            "speaker": speaker,
            "segment_index": segment_index,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "speaker": speaker,
            "segment_index": segment_index,
        }


def generate_podcast_audio(script: list, output_dir: str = "output") -> dict:
    """
    Generate audio for an entire podcast script.

    Args:
        script (list): List of dialogue entries with 'speaker' and 'text' keys.
                      Example: [{"speaker": "Host", "text": "Welcome!"}, ...]
        output_dir (str): Directory to save audio files.

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - audio_files: List of generated file paths
            - total_segments: Number of segments generated
    """
    # Ensure voice references exist before starting batch generation
    _ensure_voice_references()

    audio_files = []
    errors = []

    for idx, entry in enumerate(script):
        speaker = entry.get("speaker", "Host")
        text = entry.get("text", "")

        if not text.strip():
            continue

        result = generate_audio_segment(
            text=text,
            speaker=speaker,
            output_dir=output_dir,
            segment_index=idx,
        )

        if result["status"] == "success":
            audio_files.append(result["file_path"])
        else:
            errors.append(f"Segment {idx}: {result.get('error', 'Unknown error')}")

    if errors:
        return {
            "status": "partial" if audio_files else "error",
            "audio_files": audio_files,
            "total_segments": len(audio_files),
            "errors": errors,
        }

    return {
        "status": "success",
        "audio_files": audio_files,
        "total_segments": len(audio_files),
        "output_directory": str(Path(output_dir).absolute()),
    }
