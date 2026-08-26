"""
Multi-Agent Data Analyst — Main Application
============================================
FastAPI application entry point.

This is the single file you run to start the backend server:
    uvicorn app.main:app --reload

It wires together:
- CORS middleware (for frontend communication)
- API routes (uploads, jobs, reports)
- Health check endpoint
- Structured logging
- Static file serving for charts

WHY FastAPI:
- Native async support (critical for SSE endpoints)
- Auto-generated OpenAPI docs (visit /docs when running)
- Pydantic integration for request/response validation
- Dependency injection system (used in Phase 2 for auth)
"""

import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api import api_router
from app.utils.logging import setup_logging


# ── Lifespan (startup/shutdown) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Startup: configure logging, create storage directories, initialize DB tables.
    Shutdown: cleanup resources.
    """
    # ── STARTUP ──
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info(f"  {settings.app_name}")
    logger.info(f"  Environment: {settings.app_env}")
    logger.info(f"  LLM (Groq): {'[ENABLED]' if settings.llm_enabled else '[DISABLED] (rule-based mode)'}")
    logger.info(f"  Storage: {settings.storage_backend}")
    logger.info("=" * 60)
    
    # Validate production secrets
    if settings.is_production:
        settings.validate_production_secrets()
    
    # Ensure storage directories exist
    settings.storage_path  # This creates the dir via the property
    
    # Initialize DB tables for Phase 2
    # Database migration check
    # In production, use: alembic upgrade head
    # In development, auto-create tables for convenience
    try:
        from app.models import engine, Base
        if not settings.is_production:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized (dev mode auto-create).")
        else:
            logger.info("Production mode: Use 'alembic upgrade head' to manage database schema.")
    except Exception as e:
        logger.warning(f"Database initialization notice: {e}")
    
    yield  # App is running
    
    # ── SHUTDOWN ──
    logger.info("Application shutting down...")


# ── App Factory ──────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description=(
        "A multi-agent AI pipeline that analyzes uploaded CSV/Excel files. "
        "Agents: Data Cleaner → Analyst → Visualizer → Explainer."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    lifespan=lifespan,
)


# ── CORS Middleware ──────────────────────────────────────────
# Allows the Next.js frontend (different port/domain) to call our API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mount Static Files ──────────────────────────────────────
# Serve generated charts as static files
# In Phase 2, this gets replaced with S3 signed URLs
import os
storage_dir = str(settings.storage_path)
if os.path.isdir(storage_dir):
    app.mount(
        "/static/storage",
        StaticFiles(directory=storage_dir),
        name="storage",
    )


# ── Include API Routes ──────────────────────────────────────
app.include_router(api_router)


# ── Global Exception Handlers ────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure all HTTP errors return consistent JSON structure."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return structured JSON."""
    logger = logging.getLogger(__name__)
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "detail": "Internal server error" if settings.is_production else str(exc),
        },
    )


# ── Health Check ─────────────────────────────────────────────
@app.get("/api/health", tags=["system"])
async def health_check():
    """
    Health check endpoint — used by load balancers and monitoring.
    Returns app status, LLM availability, and current timestamp.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "llm_enabled": settings.llm_enabled,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Root Redirect ────────────────────────────────────────────
@app.get("/", tags=["system"])
async def root():
    """Root endpoint — redirects to API docs."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "docs": "/docs",
        "health": "/api/health",
    }


# ── Direct Run Support ──────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
    )
