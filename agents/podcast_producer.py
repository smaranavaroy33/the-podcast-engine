"""
Podcast Producer Agent for the Agentic AI Podcast Generator.

This agent converts the script into audio using Chatterbox TTS.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from tools.chatterbox_tool import generate_audio_segment
from tools.stitch_tool import stitch_audio_segments


# Model configuration - Ollama local model via LiteLlm
OLLAMA_MODEL = LiteLlm(model="ollama_chat/deepseek-v3.1:671b-cloud")

# System instruction for the Podcast Producer Agent
PODCAST_PRODUCER_INSTRUCTION = """You are a podcast audio engineer responsible for converting scripts into audio.

Your Role:
You are the final step in the podcast creation pipeline. You receive a JSON script and must generate audio for each line using the generate_audio_segment tool.

Script to Process:
{script}

Your Task:
1. Parse the JSON script to extract each dialogue entry
2. For EACH line in the script, call the generate_audio_segment tool with:
   - text: The dialogue text for that line
   - speaker: The speaker identifier ("Host" or "Expert")
   - segment_index: The position in the script (0, 1, 2, ...)
   - output_dir: "output/podcast_timestamp" (default)
   - the podcast audio is stored inside a proper unique timestamped folder
   - the folder name is the timestamp of the podcast
   
3. Process lines IN ORDER to maintain the correct sequence
4. Track all generated file paths

Tool Usage:
For each script entry, call:
```
generate_audio_segment(
    text="[the dialogue text]",
    speaker="[Host or Expert]",
    segment_index=[0, 1, 2, ...],
    output_dir="output"
)
```

IMPORTANT:
- Process the ENTIRE script - do not skip any lines
- Keep track of any errors and report them
- After processing all lines, call the stitch_audio_segments tool to combine them into one file:
```
stitch_audio_segments(
    output_dir="output"
)
```
- This will create a "final_podcast.wav" while keeping all individual segment files

Final Report Format:
After generating and stitching all audio segments, provide a summary:
```
## Audio Generation Complete

Total Segments Generated: [number]
Output Directory: output/podcast_timestamp 
Final Podcast: final_podcast.wav

Generated Files:
1. segment_000_host.wav
2. segment_001_expert.wav
...
Final: final_podcast.wav

Status: [Success/Partial Success/Failed]
Errors (if any): [list any errors]
```
"""

# Create the Podcast Producer Agent
podcast_producer_agent = LlmAgent(
    name="PodcastProducerAgent",
    model=OLLAMA_MODEL,
    instruction=PODCAST_PRODUCER_INSTRUCTION,
    description="An audio engineer that generates podcast audio from scripts using Chatterbox TTS.",
    tools=[generate_audio_segment, stitch_audio_segments],
    output_key="audio_files"
)
