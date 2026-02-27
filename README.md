# 🎙️ Agentic AI Podcast Generator

An AI-powered podcast generator that transforms any topic into a complete podcast episode using Google's Agent Development Kit (ADK) and Chatterbox TTS.

## Features

- **Multi-Agent Architecture**: Four specialized AI agents working in sequence
  - 🔍 **Researcher**: Gathers information from web sources
  - 📝 **Summarizer**: Synthesizes research into key themes
  - ✍️ **Scriptwriter**: Creates engaging Host/Expert dialogue
  - 🎤 **Producer**: Generates audio using Chatterbox TTS

- **Multiple Interfaces**:
  - Command-line interface with progress indicators
  - Streamlit web UI with audio player
  - ADK web UI compatibility

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
copy .env.example .env

# Edit .env and add your Google GenAI API key
# GOOGLE_GENAI_API_KEY=your_api_key_here
```

### 3. Run the Generator

**CLI:**
```bash
python main.py "The future of artificial intelligence"
```

**Web UI:**
```bash
streamlit run streamlit_app.py
```

**ADK Web:**
```bash
adk web
```

## Output

Generated files are saved to the `output/` directory:
- `segment_XXX_host.wav` - Individual dialogue segments
- `segment_XXX_expert.wav` - Individual dialogue segments  
- `final_podcast.wav` - Complete stitched podcast

## Requirements

- Python 3.11+
- Google GenAI API key
- CUDA-capable GPU (recommended for Chatterbox TTS)
- FFmpeg (for audio stitching)

## Project Structure

```
ai_podcast/
├── agents/           # ADK agent definitions
├── tools/            # Custom tools (research, TTS, audio)
├── output/           # Generated audio files
├── agent.py          # Root agent for ADK
├── main.py           # CLI entry point
├── streamlit_app.py  # Web interface
└── requirements.txt  # Dependencies
```

## License

MIT
