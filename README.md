# 🎙️ The Podcast Engine (Agentic AI Podcast Generator)

An AI-powered podcast generator that transforms any topic into a complete podcast episode using Ollama, Google's Agent Development Kit (ADK), and Chatterbox TTS. It features a modern Streamlit web interface for real-time progress visualization and audio playback.

## Features

- Multi-Agent Architecture: Three specialized AI agents working in sequence:
  - 🔍 Researcher: Gathers information to establish core themes.
  - 📝 Summarizer: Synthesizes raw research into a structured narrative outline.
  - ✍️ Scriptwriter: Creates an engaging Host/Expert dialogue tailored for audio pacing.
- Local Neural Voice Synthesis: Utilizes Chatterbox TTS to generate expressive voices for both the Host and Expert (voice-cloned from reference audio).
- Interactive Web UI: A polished Streamlit interface to track agent thoughts in real-time, and play/download the final podcast.

## Prerequisites

- Python 3.11+
- Ollama (running locally)
- wave (for audio stitching)
- Chatterbox TTS for converting the script to audio

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Generator
Start the Streamlit application:

```bash
streamlit run podcast_app.py
```

## Project Structure

```text
ai_podcast_v3/
├── podcast_app.py      # Main Streamlit web interface
├── agents/             # ADK multi-agent definitions
├── tools/              # Custom tools (Chatterbox, Stitching, Voice Refs)
├── voice_references/   # Reference audio clips for voice cloning
├── output/             # Generated audio segments and final podcast
└── requirements.txt    # Project dependencies
```

## License

MIT
