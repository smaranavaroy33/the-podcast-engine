"""
Root Agent Module for ADK compatibility.

This is the standard entry point for ADK applications.
The root_agent variable is discovered by the ADK CLI and web UI.
"""

from agents.podcast_pipeline import podcast_pipeline_agent

# Export the root agent for ADK discovery
root_agent = podcast_pipeline_agent
