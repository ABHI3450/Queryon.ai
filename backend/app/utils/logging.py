"""
Structured Logging Setup
=========================
Configures structured logging for the entire application.

WHY STRUCTURED LOGGING:
- In production, JSON logs are parseable by log aggregators (Datadog, ELK, CloudWatch)
- In development, human-readable console output for quick debugging
- Consistent format across all modules
- Easy to add context (job_id, user_id) to every log line

Switch between formats via LOG_FORMAT env var: "json" or "console"
"""

import sys
import logging

from app.config import settings


def setup_logging() -> None:
    """
    Configure logging for the application.
    
    Call this once at startup (in main.py).
    All modules that use `logging.getLogger(__name__)` will inherit this config.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Choose format based on config
    if settings.log_format == "json":
        # JSON format for production — parseable by log aggregators
        log_format = (
            '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
            '"module":"%(name)s","message":"%(message)s"}'
        )
    else:
        # Human-readable format for development
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
        )
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any existing config
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={settings.log_level}, format={settings.log_format}"
    )
