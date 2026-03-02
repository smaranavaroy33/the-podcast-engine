"""
Researcher Agent for the Agentic AI Podcast Generator.

This agent performs in-depth research on topics using web search tools.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from tools.research_tool import search_web
from prompts.instructions import RESEARCHER_INSTRUCTION


# Model configuration - Ollama local model via LiteLlm
OLLAMA_MODEL = LiteLlm(
                        model="ollama_chat/deepseek-v3.1:671b-cloud",
                        temperature = 0.2)

# Create the Researcher Agent
researcher_agent = LlmAgent(
    name="ResearcherAgent",
    model=OLLAMA_MODEL,
    instruction=RESEARCHER_INSTRUCTION,
    description="An expert researcher that gathers comprehensive information on topics using web search tools.",
    tools=[search_web],
    output_key="research_data"
)