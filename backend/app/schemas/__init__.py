"""
Pydantic Schemas — API Request/Response Models
===============================================
Defines the data contracts between frontend and backend.

WHY SEPARATE FROM SQLAlchemy MODELS:
- SQLAlchemy models define database structure (how data is stored)
- Pydantic schemas define API contracts (what data is sent/received)
- Keeps the API layer independent from the database layer
- Enables validation, serialization, and documentation (OpenAPI/Swagger)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════
# Upload Schemas
# ═══════════════════════════════════════

class UploadResponse(BaseModel):
    """Response after a successful file upload."""
    upload_id: str = Field(description="Unique upload identifier")
    job_id: str = Field(description="Pipeline job ID for tracking status")
    filename: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    message: str = Field(default="File uploaded successfully. Processing started.")


# ═══════════════════════════════════════
# Job / Status Schemas
# ═══════════════════════════════════════

class JobStatusResponse(BaseModel):
    """Real-time job status — used by SSE endpoint."""
    job_id: str
    status: str = Field(description="pending|cleaning|analyzing|visualizing|explaining|completed|failed")
    current_agent: str = Field(default="")
    progress_pct: float = Field(default=0.0, ge=0, le=100)
    message: str = Field(default="")
    error: Optional[str] = None


# ═══════════════════════════════════════
# Report Schemas
# ═══════════════════════════════════════

class ChartInfo(BaseModel):
    """Information about a generated chart."""
    finding_id: str
    chart_type: str
    file_path: str
    title: str


class FindingInfo(BaseModel):
    """A single analysis finding."""
    id: str
    title: str
    description: str
    importance: str
    evidence: dict = Field(default_factory=dict)
    chart_type: str = ""


class ReportResponse(BaseModel):
    """Full report response — everything the frontend needs to display."""
    job_id: str
    success: bool
    cleaning_summary: dict = Field(default_factory=dict)
    findings: list[dict] = Field(default_factory=list)
    charts: list[dict] = Field(default_factory=list)
    report_markdown: str = ""
    report_sections: dict = Field(default_factory=dict)
    agent_durations: dict = Field(default_factory=dict, description="How long each agent took")
    total_duration_seconds: float = 0.0
    error: Optional[str] = None


class ReportListItem(BaseModel):
    """Summary item for the report history list."""
    job_id: str
    filename: str
    status: str
    created_at: str
    rows_analyzed: int = 0
    findings_count: int = 0
    total_duration_seconds: float = 0.0


# ═══════════════════════════════════════
# Error Schemas
# ═══════════════════════════════════════

class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str = Field(description="Error type")
    detail: str = Field(description="Human-readable error message")
    status_code: int = Field(description="HTTP status code")


# ═══════════════════════════════════════
# Health Check
# ═══════════════════════════════════════

class HealthResponse(BaseModel):
    """API health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    llm_enabled: bool = False
    timestamp: str = ""
