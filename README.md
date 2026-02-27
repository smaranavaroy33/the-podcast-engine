# 🎙️ The Podcast Engine

An end-to-end **Agentic AI Podcast Generator** that transforms any topic into a professional, two-host podcast episode. Built with **Google's Agent Development Kit (ADK)** for multi-agent orchestration and **Chatterbox TTS** for expressive, voice-cloned audio synthesis.

---

## 🚀 Key Features

- **Multi-Agent Pipeline**: A sequential workflow orchestrated by Google ADK.
  - 🔍 **Researcher**: Gathers real-time data using web search tools.
  - 📝 **Summarizer**: Synthesizes raw research into cohesive themes and talking points.
  - ✍️ **Scriptwriter**: Transforms research summaries into a natural, two-persona dialogue script.
  - 🎤 **Producer**: Converts the script into high-quality audio with speaker-specific voice clones.
- **Voice Cloning**: Automatically generates unique voice profiles for the "Host" (warm/expressive) and the "Expert" (measured/authoritative) using reference audio.
- **Dual Interfaces**: 
  - **CLI**: A robust command-line interface for automated pipelines.
  - **Streamlit Web UI**: An interactive dashboard with real-time progress tracking, script visualization, and integrated audio playback.
- **Native Audio Stitching**: Uses a custom, low-dependency stitching tool to combine dialogue segments into a final master file.

---

## 🛠️ System Architecture

The engine follows a strict **Research → Summarize → Script → Produce** workflow:

1.  **Research**: The `ResearcherAgent` uses `DuckDuckGo` or `Google Search` to fetch the latest information.
2.  **Analysis**: The `SummarizerAgent` extracts key insights and interesting facts.
3.  **Creative Writing**: The `ScriptwriterAgent` generates a JSON-formatted script featuring a dynamic exchange between two personas.
4.  **Synthesis**: The `PodcastProducer` (via `ChatterboxTool`) generates individual `.wav` segments for each line of dialogue.
5.  **Final Polish**: The `StitchTool` merges all segments into a single `final_podcast.wav`.

---

## 📦 Getting Started

### 1. Prerequisites
- **Python 3.11 or higher**
- **FFmpeg** (optional, for advanced audio processing via `pydub`)
- **A modern GPU** (recommended for Chatterbox TTS acceleration)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/the-podcast-engine.git
cd the-podcast-engine

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add your API keys:
```env
# Google Gemini API (Required for ADK agents)
GOOGLE_API_KEY=your_gemini_api_key

# Optional: Google Custom Search (if using Google search instead of DuckDuckGo)
GOOGLE_SEARCH_API_KEY=your_search_key
GOOGLE_SEARCH_CX=your_search_cx
```

---

## 🎮 Usage

### Option A: Command Line Interface
Run the generator directly from your terminal:
```bash
python main.py --topic "The future of solid-state batteries"
```

### Option B: Streamlit Web Dashboard
Launch the interactive web interface:
```bash
streamlit run streamlit_app.py
```
*The dashboard allows you to monitor each agent's "thoughts" and output in real-time.*

---

## 📁 Project Structure

```text
the-podcast-engine/
├── agents/              # ADK Agent definitions (Researcher, Summarizer, etc.)
├── tools/               # Custom tools for Search, TTS, and Audio Stitching
├── voice_references/    # WAV reference files for voice cloning
├── output/              # Directory for generated segments and final podcast
├── agent.py             # Root agent for ADK compatibility
├── main.py              # CLI Entry Point
├── streamlit_app.py     # Streamlit Web UI
├── requirements.txt     # Python dependencies
└── plan.md              # Architectural design document
```

---

## 🎙️ Voice Profiles
The engine uses **zero-shot voice cloning**. If the files in `voice_references/` are missing, the system automatically uses `edge-tts` to generate high-quality neural reference clips:
- **Host**: `en-US-AvaNeural` (Expressive female voice)
- **Expert**: `en-US-AndrewNeural` (Confident male voice)

---

## ⚖️ License
This project is for experimental use. Please ensure you have the rights to use the generated content and voice clones for your specific application.
