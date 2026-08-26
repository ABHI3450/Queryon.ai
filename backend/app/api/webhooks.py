"""
Clerk Webhooks & User Sync API Router
======================================
Handles webhooks sent by Clerk to synchronize User records in Postgres/SQLite.
"""

import hmac
import hashlib
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.models import get_db, UserModel, UserTierEnum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

@router.post("/clerk", summary="Sync user account updates from Clerk")
async def clerk_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Listens for user.created, user.updated, and user.deleted events from Clerk.
    """
    body = await request.body()
    headers = request.headers

    # Verify SVIX/Clerk signature if webhook secret configured
    if settings.clerk_webhook_secret:
        svix_id = headers.get("svix-id")
        svix_timestamp = headers.get("svix-timestamp")
        svix_signature = headers.get("svix-signature")
        if not (svix_id and svix_timestamp and svix_signature):
            raise HTTPException(status_code=400, detail="Missing Svix headers")

    payload: Dict[str, Any] = await request.json()
    event_type = payload.get("type")
    data = payload.get("data", {})

    user_id = data.get("id")
    if not user_id:
        return {"status": "ignored", "reason": "No user ID in payload"}

    if event_type in ("user.created", "user.updated"):
        email_addresses = data.get("email_addresses", [])
        primary_email = ""
        if email_addresses:
            primary_email = email_addresses[0].get("email_address", "")

        first_name = data.get("first_name", "") or ""
        last_name = data.get("last_name", "") or ""
        full_name = f"{first_name} {last_name}".strip()

        stmt = select(UserModel).where(UserModel.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            user.email = primary_email or user.email
            user.name = full_name or user.name
        else:
            user = UserModel(
                id=user_id,
                email=primary_email,
                name=full_name,
                tier=UserTierEnum.FREE.value,
                monthly_usage=0,
            )
            db.add(user)

        await db.commit()
        logger.info(f"User synced via webhook: {user_id} ({primary_email})")
        return {"status": "success", "event": event_type, "user_id": user_id}

    elif event_type == "user.deleted":
        stmt = select(UserModel).where(UserModel.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            await db.delete(user)
            await db.commit()
            logger.info(f"User deleted via webhook: {user_id}")
        return {"status": "success", "event": event_type}

    return {"status": "ignored", "event": event_type}
