"""
Base Agent Module
=================
Abstract base class that all agents inherit from.

WHY THIS EXISTS:
- Enforces a consistent interface across all agents (execute method)
- Provides built-in logging, timing, and error handling
- Makes the pipeline orchestrator agent-agnostic — it just calls run()
- Easy to add new agents: just inherit BaseAgent and implement execute()

DESIGN PATTERN: Template Method
- run() is the template method (handles logging, timing, error wrapping)
- execute() is the hook method (each agent implements its specific logic)
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """
    Standardized output from every agent.
    
    WHY a dataclass instead of a dict:
    - Type safety: IDE autocompletion and error catching
    - Self-documenting: clear what each agent returns
    - Serializable: easy to convert to JSON for API responses
    """
    success: bool
    agent_name: str
    data: dict = field(default_factory=dict)        # Agent-specific output
    errors: list[str] = field(default_factory=list)  # Any errors encountered
    warnings: list[str] = field(default_factory=list) # Non-fatal issues
    duration_seconds: float = 0.0                     # How long the agent took


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the pipeline.
    
    Each agent has:
    - name: Human-readable identifier (e.g., "Data Cleaner")
    - role: Description of what this agent does (for logging/UI)
    - run(): Public method that wraps execute() with logging and error handling
    - execute(): Abstract method that subclasses implement
    
    Usage:
        class MyAgent(BaseAgent):
            name = "My Agent"
            role = "Does something specific"
            
            def execute(self, input_data: dict) -> dict:
                # Your logic here
                return {"result": "data"}
        
        agent = MyAgent()
        result = agent.run({"key": "value"})
    """
    
    name: str = "BaseAgent"
    role: str = "Base agent — should be overridden"
    
    def run(self, input_data: dict) -> AgentResult:
        """
        Template method: wraps execute() with logging, timing, and error handling.
        
        This is what the orchestrator calls. It ensures every agent:
        1. Logs when it starts and finishes
        2. Records how long it took
        3. Catches and wraps any exceptions
        
        Args:
            input_data: Dict with whatever the agent needs (varies by agent)
            
        Returns:
            AgentResult with success/failure, output data, and timing
        """
        logger.info(f"[{self.name}] Starting — {self.role}")
        start_time = time.time()
        
        try:
            # Call the agent's specific implementation
            output_data = self.execute(input_data)
            duration = time.time() - start_time
            
            logger.info(f"[{self.name}] Completed in {duration:.2f}s")
            
            return AgentResult(
                success=True,
                agent_name=self.name,
                data=output_data,
                duration_seconds=round(duration, 3),
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            logger.error(f"[{self.name}] Failed after {duration:.2f}s — {error_msg}")
            
            return AgentResult(
                success=False,
                agent_name=self.name,
                errors=[error_msg],
                duration_seconds=round(duration, 3),
            )
    
    @abstractmethod
    def execute(self, input_data: dict) -> dict:
        """
        Agent-specific logic. Subclasses MUST implement this.
        
        Args:
            input_data: Dict with agent-specific input
            
        Returns:
            Dict with agent-specific output
            
        Raises:
            Any exception — will be caught by run() and wrapped in AgentResult
        """
        ...
