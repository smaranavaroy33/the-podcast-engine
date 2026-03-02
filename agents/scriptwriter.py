"""
Scriptwriter Agent for the Agentic AI Podcast Generator.

This agent converts summaries into engaging podcast dialogue scripts.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from prompts.instructions import SCRIPTWRITER_INSTRUCTION


# Model configuration - Ollama local model via LiteLlm
OLLAMA_MODEL = LiteLlm(
                      model="ollama_chat/deepseek-v3.1:671b-cloud",
                      temperature=0.7)

# Create the Scriptwriter Agent
scriptwriter_agent = LlmAgent(
    name="ScriptwriterAgent",
    model=OLLAMA_MODEL,
    instruction=SCRIPTWRITER_INSTRUCTION,
    description="A professional scriptwriter that creates engaging podcast dialogue between Host and Expert personas.",
    tools=[],  # No tools - pure creative writing
    output_key="script"
)
