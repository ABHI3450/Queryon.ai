"""
Admin & Monitoring API Router
=============================
Provides usage statistics, failed job tracking, and system health metrics.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models import get_db, UserModel, JobModel, ReportModel, UploadModel, JobStatusEnum
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/stats", summary="Get administrative dashboard metrics")
async def get_admin_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns platform usage metrics, total reports generated, and failed job counts.
    """
    # Count totals
    total_users_res = await db.execute(select(func.count(UserModel.id)))
    total_users = total_users_res.scalar() or 0

    total_uploads_res = await db.execute(select(func.count(UploadModel.id)))
    total_uploads = total_uploads_res.scalar() or 0

    total_reports_res = await db.execute(select(func.count(ReportModel.id)))
    total_reports = total_reports_res.scalar() or 0

    failed_jobs_res = await db.execute(
        select(func.count(JobModel.id)).where(JobModel.status == JobStatusEnum.FAILED.value)
    )
    failed_jobs = failed_jobs_res.scalar() or 0

    # Recent failed jobs details
    recent_failed_res = await db.execute(
        select(JobModel)
        .where(JobModel.status == JobStatusEnum.FAILED.value)
        .order_by(JobModel.created_at.desc())
        .limit(10)
    )
    recent_failed = recent_failed_res.scalars().all()

    failed_list = [
        {
            "job_id": job.id,
            "upload_id": job.upload_id,
            "error": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
        for job in recent_failed
    ]

    return {
        "system_status": "operational",
        "llm_enabled": settings.llm_enabled,
        "metrics": {
            "total_users": total_users,
            "total_uploads": total_uploads,
            "total_reports": total_reports,
            "failed_jobs_count": failed_jobs,
        },
        "recent_failures": failed_list,
    }
