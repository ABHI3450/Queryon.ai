"""
Storage Service
===============
Abstraction layer for file storage (local filesystem or S3).

WHY THIS EXISTS:
- Decouples the application from a specific storage backend
- Start with local filesystem for development
- Swap to S3 in production by changing one config value
- All other code just calls storage.save() and storage.get_url()

DESIGN PATTERN: Strategy Pattern
- StorageBackend is the interface
- LocalStorage and S3Storage are concrete strategies
- get_storage_backend() is the factory function
"""

import os
import uuid
import shutil
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings


logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract interface for file storage operations."""
    
    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str, subdir: str = "") -> str:
        """
        Save a file and return its storage path/key.
        
        Args:
            file_bytes: Raw file content
            filename: Original filename (used for extension)
            subdir: Optional subdirectory (e.g., "uploads", "charts")
            
        Returns:
            Storage path/key that can be used to retrieve the file
        """
        ...
    
    @abstractmethod
    def get_file_path(self, storage_key: str) -> str:
        """Get the absolute filesystem path or URL for a stored file."""
        ...
    
    @abstractmethod
    def read_file(self, storage_key: str) -> bytes:
        """Read a file's content by its storage key."""
        ...
    
    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """Delete a file. Returns True if successful."""
        ...
    
    @abstractmethod
    def file_exists(self, storage_key: str) -> bool:
        """Check if a file exists in storage."""
        ...


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.
    
    Used for development and testing. Files are stored under
    a configurable directory (default: ./storage/).
    
    Directory structure:
        storage/
        ├── uploads/      # User-uploaded CSV/Excel files
        │   └── {uuid}_{filename}
        └── charts/       # Generated chart images
            └── {uuid}/
                └── chart_{finding_id}.png
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.storage_local_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorage initialized at: {self.base_path.resolve()}")
    
    def save_file(self, file_bytes: bytes, filename: str, subdir: str = "") -> str:
        # Generate a unique filename to prevent collisions
        unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
        
        # Build the full path
        target_dir = self.base_path / subdir if subdir else self.base_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = target_dir / unique_name
        file_path.write_bytes(file_bytes)
        
        # Return relative path as storage key
        storage_key = str(file_path.relative_to(self.base_path))
        logger.info(f"Saved file: {storage_key} ({len(file_bytes)} bytes)")
        return storage_key
    
    def get_file_path(self, storage_key: str) -> str:
        """Return the absolute path for serving/reading."""
        return str((self.base_path / storage_key).resolve())
    
    def read_file(self, storage_key: str) -> bytes:
        file_path = self.base_path / storage_key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {storage_key}")
        return file_path.read_bytes()
    
    def delete_file(self, storage_key: str) -> bool:
        file_path = self.base_path / storage_key
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {storage_key}")
            return True
        return False
    
    def file_exists(self, storage_key: str) -> bool:
        return (self.base_path / storage_key).exists()
    
    def ensure_directory(self, subdir: str) -> str:
        """Create a subdirectory and return its absolute path."""
        dir_path = self.base_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        return str(dir_path.resolve())


def get_storage_backend() -> StorageBackend:
    """
    Factory function: returns the appropriate storage backend
    based on configuration.
    
    Usage:
        storage = get_storage_backend()
        key = storage.save_file(data, "report.csv", subdir="uploads")
    """
    if settings.storage_backend == "s3":
        # Future: return S3Storage(...)
        logger.warning("S3 storage not yet implemented, falling back to local")
        return LocalStorage()
    
    return LocalStorage()
