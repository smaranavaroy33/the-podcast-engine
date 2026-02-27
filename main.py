"""
Main CLI Entry Point for the Agentic AI Podcast Generator.

This script provides a command-line interface to run the podcast
generation pipeline with a given topic.
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def run_podcast_pipeline(topic: str, output_dir: str = "output") -> dict:
    """
    Run the complete podcast generation pipeline.
    
    Args:
        topic (str): The podcast topic to research and generate.
        output_dir (str): Directory for output audio files.
    
    Returns:
        dict: Pipeline results including generated files.
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    
    from agents.podcast_pipeline import podcast_pipeline_agent
    from tools.stitch_tool import stitch_audio_segments
    
    # Configuration
    APP_NAME = "ai_podcast_generator"
    USER_ID = "user"
    SESSION_ID = f"session_{hash(topic) % 10000}"
    
    print(f"\n{'='*60}")
    print(f"🎙️  AI Podcast Generator")
    print(f"{'='*60}")
    print(f"📋 Topic: {topic}")
    print(f"📁 Output: {output_dir}/")
    print(f"{'='*60}\n")
    
    # Initialize session and runner
    session_service = InMemorySessionService()
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
    
    # Create user message
    content = types.Content(
        role='user',
        parts=[types.Part(text=f"Create a podcast about: {topic}")]
    )
    
    # Track pipeline progress
    print("🔍 Stage 1: Researching topic...")
    
    final_response = None
    stage = 1
    
    # Run the pipeline
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        # Track which agent is running
        if hasattr(event, 'author') and event.author:
            agent_name = event.author
            if "Researcher" in agent_name and stage == 1:
                print("   → Gathering information from multiple sources...")
            elif "Summarizer" in agent_name and stage == 1:
                stage = 2
                print("✅ Research complete!\n")
                print("📝 Stage 2: Synthesizing summary...")
            elif "Scriptwriter" in agent_name and stage == 2:
                stage = 3
                print("✅ Summary complete!\n")
                print("✍️  Stage 3: Writing podcast script...")
            elif "Producer" in agent_name and stage == 3:
                stage = 4
                print("✅ Script complete!\n")
                print("🎤 Stage 4: Generating audio...")
        
        # Capture final response
        if event.is_final_response():
            final_response = event.content.parts[0].text if event.content.parts else None
    
    print("✅ Audio generation complete!\n")
    
    # Post-processing: Stitch audio files
    print("🔧 Post-processing: Stitching audio segments...")
    
    from tools.stitch_tool import stitch_audio_segments
    stitch_result = stitch_audio_segments(
        output_dir=output_dir,
        output_filename="final_podcast.wav"
    )
    
    if stitch_result["status"] == "success":
        print(f"✅ Final podcast created: {stitch_result['output_path']}")
    else:
        print(f"⚠️  Stitching failed: {stitch_result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*60}")
    print("🎉 Podcast Generation Complete!")
    print(f"{'='*60}\n")
    
    return {
        "topic": topic,
        "output_dir": output_dir,
        "final_response": final_response
    }


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="AI Podcast Generator - Create podcasts from any topic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "The future of artificial intelligence"
  python main.py "Climate change solutions" --output ./podcasts
  python main.py "History of the Internet" -o custom_output
        """
    )
    
    parser.add_argument(
        "topic",
        type=str,
        help="The topic for the podcast (in quotes)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory for audio files (default: output)"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not os.getenv("OLLAMA_API_BASE"):
        print("ℹ️  OLLAMA_API_BASE not set — defaulting to http://localhost:11434")
    
    # Run the pipeline
    try:
        result = asyncio.run(run_podcast_pipeline(args.topic, args.output))
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
