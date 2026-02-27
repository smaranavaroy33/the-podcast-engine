"""
Script Pipeline Agent for the Agentic AI Podcast Generator.

This module defines a SequentialAgent that runs only the text-generation
stages of the pipeline: Research -> Summarize -> Scriptwrite.

Audio generation is handled programmatically after this pipeline completes,
which is far more reliable than having an LLM agent call a TTS tool
20-30 times sequentially.
"""

from google.adk.agents import SequentialAgent

from agents.researcher import researcher_agent
from agents.summarizer import summarizer_agent
from agents.scriptwriter import scriptwriter_agent


# Create the Script-only Pipeline
# This orchestrates: Research -> Summarize -> Script
# Audio generation happens outside this pipeline for reliability
script_pipeline_agent = SequentialAgent(
    name="ScriptPipelineAgent",
    description="""
    A podcast script generation pipeline that:
    1. Researches the given topic using web search
    2. Summarizes the research into key themes and talking points
    3. Creates an engaging dialogue script between Host and Expert
    
    Input: A plain text topic (e.g., "The future of renewable energy")
    Output: A JSON script stored in session state under the 'script' key
    """,
    sub_agents=[
        researcher_agent,       # Step 1: Research the topic
        summarizer_agent,       # Step 2: Synthesize research into summary
        scriptwriter_agent,     # Step 3: Convert summary to dialogue script
    ]
)
