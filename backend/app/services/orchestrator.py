"""
Pipeline Orchestrator
=====================
Manages the sequential execution of agents: Cleaner → Analyst → Visualizer → Explainer.

WHY THIS EXISTS:
- Single responsibility: coordinates the pipeline, doesn't do analysis itself
- Handles data passing between agents (output of one → input of next)
- Provides real-time status updates via callback function (for SSE)
- Graceful degradation: if one agent fails, it tries to continue with what's available
- Makes it trivial to add/remove/reorder agents

DESIGN PATTERN: Pipeline / Chain of Responsibility
- Each agent is independent and doesn't know about others
- The orchestrator decides the order and data flow
- Status callback enables real-time UI updates without coupling to HTTP/SSE
"""

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

import pandas as pd

from app.agents import DataCleanerAgent, AnalystAgent, VisualizerAgent, ExplainerAgent
from app.agents.base import AgentResult
from app.services.storage import get_storage_backend


logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Pipeline job states — maps directly to what the frontend displays."""
    PENDING = "pending"
    CLEANING = "cleaning"
    ANALYZING = "analyzing"
    VISUALIZING = "visualizing"
    EXPLAINING = "explaining"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStatus:
    """Real-time status of a running pipeline job."""
    job_id: str
    status: JobStatus
    current_agent: str = ""
    progress_pct: float = 0.0
    message: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "current_agent": self.current_agent,
            "progress_pct": self.progress_pct,
            "message": self.message,
            "error": self.error,
        }


@dataclass
class PipelineResult:
    """
    Final output of the complete pipeline.
    Contains everything needed to build the report page.
    """
    job_id: str
    success: bool
    cleaning_summary: dict = field(default_factory=dict)
    findings: list = field(default_factory=list)
    charts: list = field(default_factory=list)
    report_markdown: str = ""
    report_sections: dict = field(default_factory=dict)
    agent_results: list[AgentResult] = field(default_factory=list)
    error: Optional[str] = None
    total_duration_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "success": self.success,
            "cleaning_summary": self.cleaning_summary,
            "findings": self.findings,
            "charts": self.charts,
            "report_markdown": self.report_markdown,
            "report_sections": self.report_sections,
            "agent_durations": {
                r.agent_name: r.duration_seconds for r in self.agent_results
            },
            "error": self.error,
            "total_duration_seconds": self.total_duration_seconds,
        }


# Type alias for status callback
StatusCallback = Callable[[PipelineStatus], None]


def _noop_callback(status: PipelineStatus) -> None:
    """Default callback that does nothing. Used when no UI is connected."""
    pass


class PipelineOrchestrator:
    """
    Orchestrates the sequential execution of all agents.
    
    Usage:
        orchestrator = PipelineOrchestrator()
        result = orchestrator.run(file_bytes, filename, on_status_update=my_callback)
    
    The on_status_update callback is called after each agent completes,
    enabling real-time progress tracking in the frontend via SSE.
    """
    
    def __init__(self):
        # Initialize agents — each is stateless, so they can be reused
        self.cleaner = DataCleanerAgent()
        self.analyst = AnalystAgent()
        self.visualizer = VisualizerAgent()
        self.explainer = ExplainerAgent()
        self.storage = get_storage_backend()
    
    def run(
        self,
        file_bytes: bytes,
        filename: str,
        job_id: Optional[str] = None,
        on_status_update: StatusCallback = _noop_callback,
    ) -> PipelineResult:
        """
        Run the full agent pipeline on an uploaded file.
        
        Data flow:
            file_bytes → Cleaner → Analyst → Visualizer → Explainer → Report
        
        Args:
            file_bytes: Raw uploaded file content
            filename: Original filename (for format detection)
            job_id: Optional job ID (auto-generated if not provided)
            on_status_update: Callback for real-time status (e.g., SSE push)
            
        Returns:
            PipelineResult with all outputs from every agent
        """
        import time
        start_time = time.time()
        
        job_id = job_id or str(uuid.uuid4())
        agent_results: list[AgentResult] = []
        
        logger.info(f"[Pipeline] Starting job {job_id} for file: {filename}")
        
        # ────────────────────────────────────────────────────────
        # STAGE 1: Data Cleaning
        # ────────────────────────────────────────────────────────
        on_status_update(PipelineStatus(
            job_id=job_id,
            status=JobStatus.CLEANING,
            current_agent="Data Cleaner",
            progress_pct=10.0,
            message="Validating and cleaning your data...",
        ))
        
        cleaner_result = self.cleaner.run({
            "file_bytes": file_bytes,
            "filename": filename,
        })
        agent_results.append(cleaner_result)
        
        if not cleaner_result.success:
            return self._build_failure(
                job_id, agent_results, start_time,
                f"Data cleaning failed: {'; '.join(cleaner_result.errors)}"
            )
        
        cleaned_df: pd.DataFrame = cleaner_result.data["cleaned_df"]
        cleaning_summary: dict = cleaner_result.data["summary"]
        
        logger.info(f"[Pipeline] Cleaning complete: {cleaning_summary['rows_after']} rows")
        
        # ────────────────────────────────────────────────────────
        # STAGE 2: Analysis
        # ────────────────────────────────────────────────────────
        on_status_update(PipelineStatus(
            job_id=job_id,
            status=JobStatus.ANALYZING,
            current_agent="Analyst",
            progress_pct=35.0,
            message="Analyzing trends and patterns...",
        ))
        
        analyst_result = self.analyst.run({
            "cleaned_df": cleaned_df,
            "cleaning_summary": cleaning_summary,
        })
        agent_results.append(analyst_result)
        
        if not analyst_result.success:
            # Analysis failed, but we can still try to generate a basic report
            logger.warning(f"[Pipeline] Analysis failed, continuing with empty findings")
            findings = []
        else:
            findings = analyst_result.data.get("findings", [])
        
        logger.info(f"[Pipeline] Analysis complete: {len(findings)} findings")
        
        # ────────────────────────────────────────────────────────
        # STAGE 3: Visualization
        # ────────────────────────────────────────────────────────
        charts = []
        if findings:  # Only visualize if we have findings
            on_status_update(PipelineStatus(
                job_id=job_id,
                status=JobStatus.VISUALIZING,
                current_agent="Visualizer",
                progress_pct=60.0,
                message="Generating charts...",
            ))
            
            # Create a job-specific directory for charts
            charts_dir = self.storage.ensure_directory(f"charts/{job_id}")
            
            viz_result = self.visualizer.run({
                "cleaned_df": cleaned_df,
                "findings": findings,
                "output_dir": charts_dir,
            })
            agent_results.append(viz_result)
            
            if viz_result.success:
                charts = viz_result.data.get("charts", [])
            else:
                logger.warning("[Pipeline] Visualization failed, continuing without charts")
        
        logger.info(f"[Pipeline] Visualization complete: {len(charts)} charts")
        
        # ────────────────────────────────────────────────────────
        # STAGE 4: Explanation
        # ────────────────────────────────────────────────────────
        on_status_update(PipelineStatus(
            job_id=job_id,
            status=JobStatus.EXPLAINING,
            current_agent="Explainer",
            progress_pct=80.0,
            message="Writing your report...",
        ))
        
        explainer_result = self.explainer.run({
            "cleaning_summary": cleaning_summary,
            "findings": findings,
            "charts": charts,
        })
        agent_results.append(explainer_result)
        
        if not explainer_result.success:
            return self._build_failure(
                job_id, agent_results, start_time,
                f"Report generation failed: {'; '.join(explainer_result.errors)}"
            )
        
        # ────────────────────────────────────────────────────────
        # SUCCESS: Build final result
        # ────────────────────────────────────────────────────────
        total_duration = round(time.time() - start_time, 3)
        
        # Save the report markdown to storage
        report_md = explainer_result.data.get("report_markdown", "")
        if report_md:
            report_dir = self.storage.ensure_directory(f"reports/{job_id}")
            report_path = f"{report_dir}/report.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_md)
        
        on_status_update(PipelineStatus(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            current_agent="",
            progress_pct=100.0,
            message="Report ready!",
        ))
        
        result = PipelineResult(
            job_id=job_id,
            success=True,
            cleaning_summary=cleaning_summary,
            findings=findings,
            charts=charts,
            report_markdown=report_md,
            report_sections=explainer_result.data.get("report_sections", {}),
            agent_results=agent_results,
            total_duration_seconds=total_duration,
        )
        
        logger.info(f"[Pipeline] Job {job_id} completed in {total_duration}s")
        return result
    
    def _build_failure(
        self,
        job_id: str,
        agent_results: list[AgentResult],
        start_time: float,
        error_msg: str,
    ) -> PipelineResult:
        """Build a failure result with all collected data so far."""
        import time
        total_duration = round(time.time() - start_time, 3)
        
        logger.error(f"[Pipeline] Job {job_id} failed: {error_msg}")
        
        return PipelineResult(
            job_id=job_id,
            success=False,
            agent_results=agent_results,
            error=error_msg,
            total_duration_seconds=total_duration,
        )
