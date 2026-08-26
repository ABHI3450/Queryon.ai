"""
Agents Package
==============
Multi-agent pipeline for data analysis.

Each agent is a self-contained module with a single responsibility:
- DataCleanerAgent: Validates and cleans raw data
- AnalystAgent: Identifies trends, patterns, and outliers
- VisualizerAgent: Generates charts for each finding
- ExplainerAgent: Writes a plain-English report

Import convenience:
    from app.agents import DataCleanerAgent, AnalystAgent, VisualizerAgent, ExplainerAgent
"""

from app.agents.base import BaseAgent, AgentResult
from app.agents.cleaner import DataCleanerAgent
from app.agents.analyst import AnalystAgent
from app.agents.visualizer import VisualizerAgent
from app.agents.explainer import ExplainerAgent

# Alias for backward compatibility
CleanerAgent = DataCleanerAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "DataCleanerAgent",
    "CleanerAgent",
    "AnalystAgent",
    "VisualizerAgent",
    "ExplainerAgent",
]
