"""
Job Status & Report API Routes
===============================
Provides real-time job tracking (SSE) and report retrieval.

WHY SSE INSTEAD OF WEBSOCKETS:
- SSE is unidirectional (server → client) — perfect for progress updates
- Works over standard HTTP (no upgrade needed), HTTP/2 multiplexes natively
- Browser's EventSource API handles reconnection automatically
- Much simpler to implement and debug than WebSockets
- WebSockets would be overkill — we don't need client → server messages here
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.schemas import JobStatusResponse, ReportResponse
from app.api.uploads import _job_statuses, _job_results, _job_metadata


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["jobs"])


@router.get(
    "/jobs/{job_id}/status",
    summary="Get current job status (snapshot)",
    response_model=JobStatusResponse,
)
async def get_job_status(job_id: str):
    """
    Returns a single snapshot of the job's current status.
    Use this for one-off checks. For real-time updates, use the SSE stream.
    """
    status = _job_statuses.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return status


@router.get(
    "/jobs/{job_id}/stream",
    summary="Stream real-time job status updates (SSE)",
    description="Opens a Server-Sent Events connection. Events are sent as the pipeline progresses.",
)
async def stream_job_status(job_id: str):
    """
    SSE endpoint — streams job status updates to the frontend.
    
    The frontend connects with:
        const es = new EventSource('/api/jobs/{job_id}/stream');
        es.addEventListener('status', (e) => { ... });
    
    Events are sent every time the pipeline status changes.
    Connection auto-closes when job reaches a terminal state (completed/failed).
    
    IMPLEMENTATION NOTE (Phase 1):
    We poll the in-memory dict every 1 second. In Phase 2 with Redis,
    this becomes a Pub/Sub subscriber — much more efficient.
    """
    if job_id not in _job_statuses and job_id not in _job_metadata:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    async def event_generator():
        """
        Generator that yields SSE events.
        Polls the status dict and sends updates until the job completes.
        """
        last_status = None
        timeout_counter = 0
        max_timeout = 600  # 10 minutes max connection
        
        while timeout_counter < max_timeout:
            current_status = _job_statuses.get(job_id, {})
            
            # Only send an event if the status has changed
            if current_status != last_status:
                yield {
                    "event": "status",
                    "data": json.dumps(current_status),
                }
                last_status = current_status.copy() if current_status else None
                
                # Close connection on terminal states
                status_value = current_status.get("status", "")
                if status_value in ("completed", "failed"):
                    # Send the final result if available
                    result = _job_results.get(job_id)
                    if result:
                        yield {
                            "event": "complete",
                            "data": json.dumps({"job_id": job_id, "success": result.get("success", False)}),
                        }
                    break
            
            await asyncio.sleep(1)  # Poll interval
            timeout_counter += 1
        
        # If we hit timeout, send a timeout event
        if timeout_counter >= max_timeout:
            yield {
                "event": "timeout",
                "data": json.dumps({"job_id": job_id, "message": "Connection timed out"}),
            }
    
    return EventSourceResponse(event_generator())


@router.get(
    "/reports/{job_id}",
    summary="Get the full analysis report",
    response_model=ReportResponse,
)
async def get_report(job_id: str):
    """
    Returns the complete analysis report for a finished job.
    
    Includes:
    - Cleaning summary (what was fixed in the data)
    - Findings (trends, patterns, outliers)
    - Chart file paths
    - Full markdown report
    - Agent timing information
    """
    result = _job_results.get(job_id)
    if not result:
        # Check if job exists but hasn't completed
        if job_id in _job_statuses:
            status = _job_statuses[job_id].get("status", "unknown")
            raise HTTPException(
                status_code=202,
                detail=f"Report not ready yet. Job status: {status}",
            )
        raise HTTPException(status_code=404, detail=f"Report for job {job_id} not found")
    
    return result


@router.get(
    "/reports",
    summary="List all reports (Phase 1: in-memory)",
)
async def list_reports():
    """
    Returns a list of all completed reports.
    In Phase 2, this queries the database with pagination.
    """
    reports = []
    for job_id, result in _job_results.items():
        meta = _job_metadata.get(job_id, {})
        reports.append({
            "job_id": job_id,
            "filename": meta.get("filename", "unknown"),
            "status": "completed" if result.get("success") else "failed",
            "findings_count": len(result.get("findings", [])),
            "total_duration_seconds": result.get("total_duration_seconds", 0),
        })
    return {"reports": reports}


@router.get(
    "/reports/{job_id}/charts/{filename}",
    summary="Serve a chart image",
)
async def get_chart_image(job_id: str, filename: str):
    """
    Serves a generated chart image file.
    
    In Phase 2 with S3, this returns a signed URL instead.
    """
    from fastapi.responses import FileResponse
    from app.services.storage import get_storage_backend
    import os
    
    storage = get_storage_backend()
    chart_path = storage.get_file_path(f"charts/{job_id}/{filename}")
    
    if not os.path.exists(chart_path):
        raise HTTPException(status_code=404, detail="Chart not found")
    
    return FileResponse(
        path=chart_path,
        media_type="image/png",
        filename=filename,
    )
