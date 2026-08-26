"""
Authentication & Authorization Middleware / Dependencies
==========================================================
Verifies Clerk JWT tokens passed in HTTP Authorization headers.

WHY THIS PATTERN:
- Decentralized auth validation using Clerk's JWKS endpoint
- Protects API routes while extracting the authenticated Clerk user_id
- In development/demo mode without Clerk keys set, provides a mock user context
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient

from app.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Cache JWKS key set to avoid fetching keys on every HTTP request
_jwks_client: Optional[PyJWKClient] = None

def get_jwks_client() -> Optional[PyJWKClient]:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = settings.clerk_jwks_url
        if not jwks_url and settings.clerk_issuer_url:
            jwks_url = f"{settings.clerk_issuer_url.rstrip('/')}/.well-known/jwks.json"
        if jwks_url:
            try:
                _jwks_client = PyJWKClient(jwks_url)
            except Exception as e:
                logger.warning(f"Could not initialize PyJWKClient: {e}")
    return _jwks_client

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to verify incoming Clerk JWT tokens.
    Returns decoded user payload containing 'sub' (Clerk user ID), 'email', etc.
    """
    # If Clerk is not configured, return mock user for smooth local dev / testing
    if not settings.clerk_secret_key and not settings.clerk_jwks_url and not settings.clerk_issuer_url:
        return {
            "sub": "dev_user_123",
            "email": "developer@example.com",
            "name": "Local Developer",
            "tier": "free",
        }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    jwks_client = get_jwks_client()

    # Build decode options
    decode_options = {
        "verify_aud": False,
        "verify_iss": bool(settings.clerk_issuer_url),
    }
    
    kwargs: Dict[str, Any] = {
        "algorithms": ["RS256", "HS256"],
        "options": decode_options,
    }
    if settings.clerk_issuer_url:
        kwargs["issuer"] = settings.clerk_issuer_url

    if jwks_client:
        # Primary path: Verify signature using Clerk's JWKS public keys
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                **kwargs,
            )
            return payload
        except Exception as e:
            logger.warning(f"JWKS Verification failed: {e}")
            if settings.is_production:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid or expired authentication token: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # Fallback / Dev mode signature check or unverified decode for development
    try:
        if settings.clerk_secret_key:
            payload = jwt.decode(
                token,
                settings.clerk_secret_key,
                **kwargs,
            )
            return payload
        else:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
    except Exception as e:
        logger.error(f"JWT Verification failed: {e}")
        if not settings.is_production:
            # In local dev mode, allow unverified payload fallback if token is present
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
