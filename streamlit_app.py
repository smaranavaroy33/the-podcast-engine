"""
Streamlit Web UI for the Agentic AI Podcast Generator.

This provides a user-friendly web interface for generating podcasts
with real-time progress visualization and audio playback.
"""

import streamlit as st
import asyncio
import os
import json
import threading
import zipfile
import io
import shutil
import time
import re
import html
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ollama runs locally — no API keys needed

# Page configuration
st.set_page_config(
    page_title="The Podcast Engine",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stage-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stage-active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .stage-complete {
        background: #10B981;
        color: white;
    }
    .stage-pending {
        background: #E5E7EB;
        color: #6B7280;
    }
    .script-box {
        background: #1F2937;
        color: #E5E7EB;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: monospace;
        max-height: 400px;
        overflow-y: auto;
    }
    .host-line {
        color: #60A5FA;
        margin: 0.5rem 0;
    }
    .expert-line {
        color: #34D399;
        margin: 0.5rem 0;
    }
    .thoughts-container {
        max-height: 1000px;
        overflow-y: auto;
        padding: 0.75rem;
        background: #111827;
        border-radius: 0.5rem;
        border: 1px solid #374151;
        margin-top: 0.5rem;
    }
    .thought-item {
        font-size: 0.85rem;
        color: #9CA3AF;
        margin-bottom: 0.8rem;
        padding-left: 0.75rem;
        border-left: 2px solid #6366F1;
        line-height: 1.5;
        white-space: pre-wrap;
    }
    /* Style the tabs */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center;
        gap: 24px;
    }
    div[data-testid="stTabs"] [data-baseweb="tab"] {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)


def create_zip_of_output():
    """Create a ZIP archive of all files in the output directory."""
    buf = io.BytesIO()
    output_dir = Path("output")
    if not output_dir.exists():
        return None
    
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for file in output_dir.glob("*.*"):
            if file.is_file():
                z.write(file, file.name)
    
    return buf.getvalue()


from tools.chatterbox_tool import generate_audio_segment
from tools.stitch_tool import stitch_audio_segments

# Configure audio tools (ffmpeg is no longer required for basic wave stitching)
def init_session_state():
    """Initialize session state variables."""
    if "pipeline_running" not in st.session_state:
        st.session_state.pipeline_running = False
    if "current_stage" not in st.session_state:
        st.session_state.current_stage = 0
    if "research_data" not in st.session_state:
        st.session_state.research_data = None
    if "summary" not in st.session_state:
        st.session_state.summary = None
    if "script" not in st.session_state:
        st.session_state.script = None
    if "audio_files" not in st.session_state:
        st.session_state.audio_files = []
    if "thoughts" not in st.session_state:
        st.session_state.thoughts = []
    if "final_podcast" not in st.session_state:
        # Check if final podcast already exists from previous run
        if os.path.exists("output/final_podcast.wav"):
            st.session_state.final_podcast = "output/final_podcast.wav"
        else:
            st.session_state.final_podcast = None
    if "pipeline_error" not in st.session_state:
        st.session_state.pipeline_error = None
    if "pipeline_complete" not in st.session_state:
        st.session_state.pipeline_complete = False
    if "topic" not in st.session_state:
        st.session_state.topic = ""


def parse_script_json(script_text: str) -> list:
    """
    Parse the script JSON from the LLM output, handling markdown fences.
    
    Args:
        script_text: Raw script text (may include ```json fences)
    
    Returns:
        list: Parsed script entries [{speaker, text}, ...]
    """
    text = script_text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


async def run_pipeline_async(topic: str, results: dict):
    """
    Run the podcast pipeline and collect results.
    
    Stage 1-3: Use ADK agents (Research -> Summarize -> Script)
    Stage 4: Directly generate audio using Chatterbox TTS (no LLM agent)
    Stage 5: Stitch audio segments into final podcast
    
    Args:
        topic: The podcast topic
        results: Dictionary to store results (shared with main thread)
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    
    from agents.podcast_pipeline import podcast_pipeline_agent
    from tools.chatterbox_tool import generate_audio_segment
    from tools.stitch_tool import stitch_audio_segments
    
    results["thoughts"] = []
    def add_thought(t):
        results["thoughts"].append(t)
    
    add_thought("Initializing AI agents and establishing connection to local model...")
    add_thought("Configuring ADK Runner with podcast pipeline specifications...")
    
    APP_NAME = "ai_podcast_streamlit"
    USER_ID = "streamlit_user"
    SESSION_ID = f"session_{hash(topic) % 10000}"
    
    # ── Stage 1-3: Run script generation pipeline ──
    results["_stage"] = "Generating script (research → summarize → write)..."
    add_thought(f"Starting research on: '{topic}'")
    add_thought("Analyzing the topic to identify core research themes and relevant sub-topics...")
    add_thought("Allocating computational resources for the Multi-Agent orchestrator...")
    
    session_service = InMemorySessionService()
    add_thought("Creating in-memory session service to track agent state...")
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    runner = Runner(
        agent=podcast_pipeline_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    
    content = types.Content(
        role='user',
        parts=[types.Part(text=f"Create a podcast about: {topic}")]
    )
    
    # Run the 3-agent pipeline and collect events
    add_thought("Broadcasting research objective to the Agentic Network...")
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if hasattr(event, 'author') and event.author:
            if hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    # 1. Capture direct 'thought' attribute if present (GenAI SDK)
                    if hasattr(part, 'thought') and part.thought:
                        thought_text = part.thought
                        if thought_text:
                            add_thought(f"🧠 {event.author} Thinking: {html.escape(thought_text)}")
                    
                    # 2. Capture 'text' attribute (could contain <think> tags)
                    if hasattr(part, 'text') and part.text:
                        text_val = part.text
                        # Extract <think> content if present (common for DeepSeek R1)
                        think_matches = re.findall(r'<think>(.*?)</think>', text_val, re.DOTALL)
                        for match in think_matches:
                            if match.strip():
                                add_thought(f"🧠 {event.author} Thought Process: {html.escape(match.strip())}")
                        
                        # Store main content (excluding <think> tags for clean tabs)
                        clean_text = re.sub(r'<think>.*?</think>', '', text_val, flags=re.DOTALL).strip()
                        if clean_text:
                            if "Researcher" in event.author:
                                if not results.get("research_data"):
                                    add_thought("Researcher Agent: Activating search tools to crawl web sources...")
                                    add_thought("Researcher Agent: Filtering results for credibility and relevance...")
                                    add_thought("Researcher Agent: Compiling raw intelligence data...")
                                results["research_data"] = clean_text
                            elif "Summarizer" in event.author:
                                if not results.get("summary"):
                                    add_thought("Summarizer Agent: Ingesting raw research for thematic analysis...")
                                    add_thought("Summarizer Agent: Identifying critical insights and expert talking points...")
                                    add_thought("Summarizer Agent: Structuring the narrative outline...")
                                results["summary"] = clean_text
                            elif "Scriptwriter" in event.author:
                                if not results.get("script"):
                                    add_thought("Scriptwriter Agent: Converting summary into natural conversational dialogue...")
                                    add_thought("Scriptwriter Agent: Assigning personas (Host vs. Expert) to dialogue nodes...")
                                    add_thought("Scriptwriter Agent: Optimizing script for TTS pacing and tone...")
                                results["script"] = clean_text
    
    add_thought("Script generation complete. Performing final validation on JSON structure...")
    
    # Fallback: retrieve from ADK session state
    try:
        add_thought("Synchronizing final session state from ADK service...")
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )
        if session and hasattr(session, 'state') and session.state:
            if not results.get("research_data") and session.state.get("research_data"):
                results["research_data"] = session.state["research_data"]
            if not results.get("summary") and session.state.get("summary"):
                results["summary"] = session.state["summary"]
            if not results.get("script") and session.state.get("script"):
                results["script"] = session.state["script"]
    except Exception:
        add_thought("Warning: Minor sync delay in session state retrieval.")
        pass
    
    # ── Stage 4: Generate audio directly (no LLM agent) ──
    script_text = results.get("script")
    if not script_text:
        results["_audio_error"] = "No script was generated — cannot produce audio."
        add_thought("Critical Error: Pipeline interrupted due to missing script data.")
        return
    
    try:
        add_thought("Parsing script JSON into dialogue segments...")
        script_entries = parse_script_json(script_text)
        add_thought(f"Detected {len(script_entries)} unique dialogue segments for synthesis.")
    except (json.JSONDecodeError, TypeError) as e:
        results["_audio_error"] = f"Failed to parse script JSON: {e}"
        add_thought("Error: Invalid JSON format detected in generated script.")
        return
    
    results["_stage"] = "Generating audio segments with Chatterbox TTS..."
    add_thought("Warming up the Chatterbox TTS engine for neural voice synthesis...")
    add_thought("Loading Speaker 1 (Host: Expressive Female) and Speaker 2 (Expert: Authoritative Male) profiles...")
    
    output_dir = "output"
    generated_files = []
    audio_errors = []
    
    for idx, entry in enumerate(script_entries):
        speaker = entry.get("speaker", "Host")
        text = entry.get("text", "")
        if not text.strip():
            continue
        
        results["_stage"] = f"Generating audio segment {idx + 1}/{len(script_entries)} ({speaker})..."
        if speaker == "Host":
            add_thought(f"Segment {idx+1}: Synthesizing neural female voice with 0.65 exaggeration...")
        else:
            add_thought(f"Segment {idx+1}: Synthesizing neural male voice with 0.4 measured delivery...")
        
        add_thought(f"Processing text-to-waveform: '{text}'")
        
        # Directly call the TTS tool (no LLM involvement)
        result = generate_audio_segment(
            text=text,
            speaker=speaker,
            segment_index=idx,
            output_dir=output_dir
        )
        
        if result["status"] == "success":
            generated_files.append(result["file_path"])
            add_thought(f"Successfully generated {os.path.basename(result['file_path'])} ({result['duration_estimate']}s)")
        else:
            add_thought(f"Warning: Failed to synthesize segment {idx+1}. Error: {result.get('error', 'Unknown')}")
            audio_errors.append(f"Segment {idx} ({speaker}): {result.get('error', 'Unknown')}")
    
    if audio_errors:
        results["_audio_error"] = f"{len(audio_errors)} segment(s) failed: " + "; ".join(audio_errors)
    
    # ── Stage 5: Stitch audio segments ──
    if generated_files:
        results["_stage"] = "Stitching audio segments..."
        add_thought("Neural synthesis complete. Starting post-production sequence...")
        add_thought("Analyzing segment headers for PCM parameter consistency...")
        add_thought(f"Concatenating {len(generated_files)} WAV buffers into linear stream...")
        
        from tools.stitch_tool import stitch_audio_segments
        stitch_result = stitch_audio_segments(
            output_dir=output_dir,
            output_filename="final_podcast.wav"
        )
        
        if stitch_result["status"] == "success":
            results["final_podcast"] = stitch_result["output_path"]
            results["audio_files"] = generated_files
            add_thought("Calculating total duration and encoding final WAV headers...")
            add_thought(f"Final podcast generated: {stitch_result['total_duration_seconds']}s of total playtime.")
            add_thought("Finalizing files and preparing the podcast for playback.")
        else:
            results["_audio_error"] = f"Audio stitching failed: {stitch_result.get('error', 'Unknown')}"
            add_thought("Error: Post-production stitching failed.")


def run_pipeline_in_thread(topic: str, results: dict):
    """
    Run the async pipeline in a new event loop on a separate thread.
    
    Args:
        topic: The podcast topic
        results: Dictionary to store results
    """
    # Re-load .env in this thread to ensure env vars are available
    load_dotenv()
    
    # Ollama runs locally — no API key setup needed
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_pipeline_async(topic, results))
        results["_status"] = "complete"
    except Exception as e:
        results["_status"] = "error"
        results["_error"] = str(e)
    finally:
        loop.close()

def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎙️ The Podcast Engine</h1>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #6B7280; margin-bottom: 2rem;'>"
        "Turning the world's knowledge into your next episode."
        "</p>",
        unsafe_allow_html=True
    )
    
    # Note: Ollama runs locally — no API key needed
    
    # Sidebar
    with st.sidebar:        
        # Render progress when running
        # if st.session_state.current_stage > 0:
        #     render_progress_stages(st.session_state.current_stage)
        
        # Display thinking process thoughts
        if st.session_state.thoughts and not st.session_state.pipeline_running:
            st.markdown("### 🧠 Thinking Process")
            st.markdown("---")

            thoughts_html = "".join([f'<div class="thought-item">→ {t}</div>' for t in st.session_state.thoughts])
            st.markdown(f'<div class="thoughts-container">{thoughts_html}</div>', unsafe_allow_html=True)
        
    # Main content
    left_spacer, center_col, right_spacer = st.columns([1, 2, 1])
    
    with center_col:
        # Topic input
        topic = st.text_input(
            "📌 Enter your podcast topic",
            placeholder="e.g., The future of renewable energy",
            disabled=st.session_state.pipeline_running,
            key="topic"
        )
        
        # Generate and Clear buttons
        btn_col1, btn_col2 = st.columns([3, 1])
        
        with btn_col1:
            if st.button(
                "🚀 Generate Podcast",
                type="primary",
                disabled=st.session_state.pipeline_running or not topic,
                use_container_width=True
            ):
                # ... [reset session state] ...
                # Reset previous results
                st.session_state.research_data = None
                st.session_state.summary = None
                st.session_state.script = None
                st.session_state.audio_files = []
                st.session_state.thoughts = []
                st.session_state.final_podcast = None
                st.session_state.pipeline_error = None
                st.session_state.pipeline_complete = False
                st.session_state.pipeline_running = True
                st.session_state.current_stage = 1
                
                # Shared results dict (thread-safe for simple assignments)
                results = {"thoughts": []}
                
                # Show thoughts in sidebar placeholder
                st.sidebar.markdown("---")
                thoughts_placeholder = st.sidebar.empty()
                
                # Show a spinner while the pipeline runs
                with st.spinner("🎙️ Generating podcast... This may take several minutes. Please wait."):
                    # Run pipeline in a background thread to avoid blocking
                    # Streamlit's event loop
                    thread = threading.Thread(
                        target=run_pipeline_in_thread,
                        args=(topic, results)
                    )
                    thread.start()
                    
                    # Dynamic polling for thoughts
                    while thread.is_alive():
                        if results.get("thoughts"):
                            st.session_state.thoughts = results["thoughts"]
                            with thoughts_placeholder.container():
                                st.markdown("### 🧠 Thinking Process")
                                thoughts_html = "".join([f'<div class="thought-item">→ {t}</div>' for t in st.session_state.thoughts])
                                st.markdown(f'<div class="thoughts-container">{thoughts_html}</div>', unsafe_allow_html=True)
                        time.sleep(1)
                    
                    thread.join()  # Final cleanup
                
                # Transfer results to session state
                if results.get("research_data"):
                    st.session_state.research_data = results["research_data"]
                if results.get("summary"):
                    st.session_state.summary = results["summary"]
                if results.get("script"):
                    st.session_state.script = results["script"]
                if results.get("audio_files"):
                    st.session_state.audio_files = results["audio_files"]
                if results.get("final_podcast"):
                    st.session_state.final_podcast = results["final_podcast"]
                
                # Update final state
                st.session_state.pipeline_running = False
                
                if results.get("_status") == "error":
                    st.session_state.pipeline_error = results.get("_error", "Unknown error")
                    st.session_state.current_stage = 0
                else:
                    st.session_state.pipeline_complete = True
                    st.session_state.current_stage = 6
                    # Show audio errors as warnings (script was still generated)
                    if results.get("_audio_error"):
                        st.session_state.pipeline_error = results["_audio_error"]
                
                st.rerun()
    
        with btn_col2:
            if st.button("🗑️ Clear", use_container_width=True):
                for key in ["research_data", "summary", "script", "audio_files",
                            "final_podcast", "pipeline_error", "pipeline_complete", "thoughts"]:
                    st.session_state[key] = None if key != "thoughts" else []
                st.session_state.current_stage = 0
                st.session_state.pipeline_running = False
                st.rerun()
    
    st.markdown("---")
    
    # Show error if pipeline failed
    if st.session_state.pipeline_error:
        st.error(f"❌ Pipeline error: {st.session_state.pipeline_error}")
    
    # Show success message
    if st.session_state.pipeline_complete:
        st.success("✅ Podcast generated successfully!")
    
    # Tabs for intermediate outputs — show whenever we have ANY data
    has_any_data = (
        st.session_state.script or
        st.session_state.summary or
        st.session_state.research_data
    )
    
    if has_any_data or st.session_state.current_stage > 0:
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Research", "📋 Summary", "📝 Script", "🎧 Podcast"])
        
        with tab1:
            if st.session_state.research_data:
                st.markdown(st.session_state.research_data)
            else:
                st.info("Research data will appear here after generation")

        with tab2:
            if st.session_state.summary:
                st.markdown(st.session_state.summary)
            else:
                st.info("Summary will appear here after generation")

        with tab3:
            if st.session_state.script:
                st.markdown("### Generated Script")
                try:
                    # Try to parse as JSON — handle markdown-wrapped JSON too
                    script_text = st.session_state.script.strip()
                    # Strip markdown code fences if present
                    if script_text.startswith("```"):
                        lines = script_text.split("\n")
                        # Remove first line (```json) and last line (```)
                        lines = [l for l in lines if not l.strip().startswith("```")]
                        script_text = "\n".join(lines)
                    
                    script_data = json.loads(script_text)
                    for entry in script_data:
                        speaker = entry.get("speaker", "Unknown")
                        text = entry.get("text", "")
                        color = "#60A5FA" if speaker == "Host" else "#34D399"
                        st.markdown(
                            f'<p style="color: {color};"><strong>{speaker}:</strong> {text}</p>',
                            unsafe_allow_html=True
                        )
                except (json.JSONDecodeError, TypeError, AttributeError):
                    # If not valid JSON, display as plain text
                    st.text(st.session_state.script)
            else:
                st.info("Script will appear here after generation")
        
        with tab4:
            st.markdown("### 🎧 Your Full Podcast")
            
            # Use same path detection logic
            final_path = st.session_state.final_podcast or "output/final_podcast.wav"
            
            if os.path.exists(final_path):
                if not st.session_state.final_podcast:
                    st.session_state.final_podcast = final_path
                
                #st.success("✅ Podcast is ready to play!")
                with open(final_path, "rb") as f:
                    st.audio(f.read(), format="audio/wav")
                
                # Download buttons section
                btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
                
                with btn_col2:
                    # Final WAV download
                    with open(st.session_state.final_podcast, "rb") as f:
                        # Use the exact topic text for the filename
                        download_filename = f"{st.session_state.topic}.wav" if st.session_state.topic else "podcast.wav"
                        st.download_button(
                            label="🎙️ Download Final Podcast",
                            data=f.read(),
                            file_name=download_filename,
                            mime="audio/wav",
                            use_container_width=True,
                            key="main_final_wav"
                        )
                
            else:
                # Option to stitch if segments exist
                output_path = Path("output")
                existing_segments = sorted(list(output_path.glob("segment_*.wav")))
                
                if existing_segments:
                    st.warning(f"Found {len(existing_segments)} audio segments. Stitch them into a single podcast to listen here.")
                    if st.button("🔧 Stitch All Segments Now"):
                        with st.spinner("Stitching segments chronologically..."):
                            result = stitch_audio_segments(output_dir="output")
                            if result["status"] == "success":
                                st.session_state.final_podcast = result["output_path"]
                                st.success("✅ Podcast stitched successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Stitching failed: {result.get('error', 'Unknown error')}")
                else:
                    st.info("The full podcast audio will appear here after the generation pipeline completes.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #9CA3AF; font-size: 0.875rem;'>"
        "Powered by Ollama + Google ADK and Chatterbox TTS"
        "</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
