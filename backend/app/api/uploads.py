"""
Upload API Routes
=================
Handles file upload and triggers the agent pipeline.

WHY THIS IS SEPARATE FROM THE PIPELINE:
- API layer handles HTTP concerns (validation, file parsing, response format)
- Pipeline logic lives in the orchestrator (reusable outside HTTP context)
- This route just validates input, starts a background job, and returns immediately
- The frontend then connects via SSE to track progress

FLOW:
  1. User uploads CSV/Excel via multipart form
  2. We validate file type and size
  3. Save raw file to storage
  4. Start pipeline in a background thread (don't block the HTTP response)
  5. Return job_id immediately — frontend uses it to poll status via SSE
"""

import uuid
import logging
import threading
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends

from app.config import settings
from app.schemas import UploadResponse, ErrorResponse
from app.services.orchestrator import PipelineOrchestrator, PipelineStatus
from app.services.orchestrator import PipelineOrchestrator, PipelineStatus
from app.services.storage import get_storage_backend
from app.auth import get_current_user


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["uploads"])

# ── In-memory job store (Phase 1: no database yet) ──────────
# In Phase 2 this gets replaced with PostgreSQL.
# Dict of job_id → latest PipelineStatus
_job_statuses: dict[str, dict] = {}
# Dict of job_id → full PipelineResult (once complete)
_job_results: dict[str, dict] = {}
# Dict of job_id → metadata
_job_metadata: dict[str, dict] = {}


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",  # Some browsers send this for CSV
}


def _get_file_extension(filename: str) -> str:
    """Extract file extension, lowercased."""
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

def _sanitize_filename(filename: str) -> str:
    """Remove path traversal characters from filename."""
    import os
    # Strip directory components
    filename = os.path.basename(filename)
    # Remove dangerous characters
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    return filename or "unnamed_file"


def _run_pipeline_job(job_id: str, file_bytes: bytes, filename: str) -> None:
    """
    Background worker function — runs the full agent pipeline.
    
    This runs in a separate thread so the HTTP response returns immediately.
    Updates _job_statuses dict as each agent completes (consumed by SSE endpoint).
    """
    def status_callback(status: PipelineStatus) -> None:
        _job_statuses[job_id] = status.to_dict()
    
    try:
        orchestrator = PipelineOrchestrator()
        result = orchestrator.run(
            file_bytes=file_bytes,
            filename=filename,
            job_id=job_id,
            on_status_update=status_callback,
        )
        
        # Store the full result for retrieval
        _job_results[job_id] = result.to_dict()
        
    except Exception as e:
        logger.exception(f"Pipeline job {job_id} crashed unexpectedly")
        _job_statuses[job_id] = {
            "job_id": job_id,
            "status": "failed",
            "current_agent": "",
            "progress_pct": 0,
            "message": "An unexpected error occurred",
            "error": str(e),
        }
        _job_results[job_id] = {
            "job_id": job_id,
            "success": False,
            "error": str(e),
        }


@router.post(
    "/uploads",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
    summary="Upload a CSV/Excel file for analysis",
    description="Validates the file, saves it, and starts the agent pipeline as a background job.",
)
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """
    Upload endpoint — the entry point for the entire pipeline.
    
    Validates:
    - File extension (must be .csv, .xlsx, .xls)
    - File size (must be under configured limit)
    - File is not empty
    
    Then starts the pipeline in a background thread and returns immediately.
    """
    # ── Validate filename ────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    extension = _get_file_extension(file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{extension}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    
    # ── Validate MIME type ───────────────────────────────────
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid MIME type '{file.content_type}'. Expected CSV or Excel file.",
        )
    
    # ── Sanitize filename ────────────────────────────────────
    safe_filename = _sanitize_filename(file.filename)
    
    # ── Read file content ────────────────────────────────────
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # ── Validate file size ───────────────────────────────────
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    if len(file_bytes) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f} MB). Maximum: {settings.max_file_size_mb} MB",
        )
    
    # ── Save raw file to storage ─────────────────────────────
    storage = get_storage_backend()
    storage_key = storage.save_file(file_bytes, safe_filename, subdir="uploads")
    
    # ── Generate job ID and start pipeline ───────────────────
    job_id = str(uuid.uuid4())
    
    # Store metadata
    _job_metadata[job_id] = {
        "filename": safe_filename,
        "file_size": len(file_bytes),
        "storage_key": storage_key,
    }
    
    # Initialize status
    _job_statuses[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "current_agent": "",
        "progress_pct": 0,
        "message": "Job queued, starting shortly...",
        "error": None,
    }
    
    # Start pipeline in background thread
    # (In Phase 2, this becomes a Celery/arq task)
    thread = threading.Thread(
        target=_run_pipeline_job,
        args=(job_id, file_bytes, safe_filename),
        daemon=True,
    )
    thread.start()
    
    logger.info(f"Upload accepted: {safe_filename} ({len(file_bytes)} bytes) → job {job_id}")
    
    return UploadResponse(
        upload_id=storage_key,
        job_id=job_id,
        filename=safe_filename,
        file_size=len(file_bytes),
    )


@router.get("/uploads", summary="List all uploads (Phase 1: in-memory)")
async def list_uploads():
    """Return metadata for all uploads. In Phase 2, this queries the database."""
    return {
        "uploads": [
            {
                "job_id": job_id,
                **meta,
                "status": _job_statuses.get(job_id, {}).get("status", "unknown"),
            }
            for job_id, meta in _job_metadata.items()
        ]
    }
