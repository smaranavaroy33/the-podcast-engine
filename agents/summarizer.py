"""
Summarizer Agent for the Agentic AI Podcast Generator.

This agent synthesizes research data into a structured summary for podcast creation.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from prompts.instructions import SUMMARIZER_INSTRUCTION

OLLAMA_MODEL = LiteLlm(
                    model="ollama_chat/deepseek-v3.1:671b-cloud",
                    temperature = 0.4)

summarizer_agent = LlmAgent(
    name="SummarizerAgent",
    model=OLLAMA_MODEL,
    instruction=SUMMARIZER_INSTRUCTION,
    description="A data analyst that synthesizes research notes into structured summaries for podcast content.",
    tools=[],
    output_key="summary"
)
