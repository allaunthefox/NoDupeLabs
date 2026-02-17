# pylint: disable=logging-fstring-interpolation
"""NoDupeLabs Network Tools - Network and Distributed Features

This module provides network-related functionality including remote storage,
distributed processing, and cloud synchronization with graceful degradation.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class RemoteStorageBackend(ABC):
    """Abstract base class for remote storage backends"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available"""

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to remote storage"""

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from remote storage"""

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[str]:
        """List files in remote storage"""

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete file from remote storage"""


class LocalStorageBackend(RemoteStorageBackend):
    """Local filesystem backend (always available)"""

    def __init__(self, base_dir: str = "remote_storage"):
        """TODO: Document __init__."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def is_available(self) -> bool:
        """Local storage is always available"""
        return True

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Copy file to local storage directory"""
        try:
            local_path_obj = Path(local_path)
            if not local_path_obj.exists():
                logger.error(f"Local file not found: {local_path}")
                return False

            remote_path_obj = self.base_dir / remote_path
            remote_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            with (
                open(local_path_obj, "rb") as src,
                open(remote_path_obj, "wb") as dst,
            ):
                dst.write(src.read())

            logger.info(f"Uploaded {local_path} to {remote_path}")
            return True

        except Exception as e:
            logger.exception(f"Error uploading file: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Copy file from local storage directory"""
        try:
            remote_path_obj = self.base_dir / remote_path
            if not remote_path_obj.exists():
                logger.error(f"Remote file not found: {remote_path}")
                return False

            local_path_obj = Path(local_path)
            local_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            with (
                open(remote_path_obj, "rb") as src,
                open(local_path_obj, "wb") as dst,
            ):
                dst.write(src.read())

            logger.info(f"Downloaded {remote_path} to {local_path}")
            return True

        except Exception as e:
            logger.exception(f"Error downloading file: {e}")
            return False

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in local storage"""
        try:
            files = []
            for file_path in self.base_dir.rglob(prefix + "*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.base_dir)
                    files.append(str(relative_path))
            return files
        except Exception as e:
            logger.exception(f"Error listing files: {e}")
            return []

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from local storage"""
        try:
            file_path = self.base_dir / remote_path
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted {remote_path}")
                return True
            else:
                logger.warning(f"File not found: {remote_path}")
                return False
        except Exception as e:
            logger.exception(f"Error deleting file: {e}")
            return False


class S3StorageBackend(RemoteStorageBackend):
    """AWS S3 storage backend"""

    def __init__(self, bucket_name: str = "nodupe-storage", **kwargs):
        """TODO: Document __init__."""
        self.bucket_name = bucket_name
        self._available = self._check_s3_available()
        self._client = None

        if self._available:
            try:
                import boto3

                self._client = boto3.client("s3", **kwargs)
                logger.info(f"S3 backend initialized for bucket {bucket_name}")
            except Exception as e:
                logger.exception(f"Failed to initialize S3 client: {e}")
                self._available = False

    def _check_s3_available(self) -> bool:
        """Check if S3 backend is available"""
        try:
            return True
        except ImportError:
            logger.warning("boto3 not available for S3 backend")
            return False

    def is_available(self) -> bool:
        """Check if S3 backend is available"""
        return self._available and self._client is not None

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to S3"""
        if not self.is_available():
            logger.warning("S3 backend not available, using local fallback")
            fallback = LocalStorageBackend()
            return fallback.upload_file(local_path, remote_path)

        try:
            self._client.upload_file(local_path, self.bucket_name, remote_path)
            logger.info(
                f"Uploaded {local_path} to s3://{self.bucket_name}/{remote_path}"
            )
            return True
        except Exception as e:
            logger.exception(f"Error uploading to S3: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from S3"""
        if not self.is_available():
            logger.warning("S3 backend not available, using local fallback")
            fallback = LocalStorageBackend()
            return fallback.download_file(remote_path, local_path)

        try:
            self._client.download_file(
                self.bucket_name, remote_path, local_path
            )
            logger.info(
                f"Downloaded s3://{self.bucket_name}/{remote_path} to {local_path}"
            )
            return True
        except Exception as e:
            logger.exception(f"Error downloading from S3: {e}")
            return False

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in S3 bucket"""
        if not self.is_available():
            logger.warning("S3 backend not available, using local fallback")
            fallback = LocalStorageBackend()
            return fallback.list_files(prefix)

        try:
            response = self._client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    files.append(obj["Key"])
            return files
        except Exception as e:
            logger.exception(f"Error listing S3 files: {e}")
            return []

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3"""
        if not self.is_available():
            logger.warning("S3 backend not available, using local fallback")
            fallback = LocalStorageBackend()
            return fallback.delete_file(remote_path)

        try:
            self._client.delete_object(Bucket=self.bucket_name, Key=remote_path)
            logger.info(f"Deleted s3://{self.bucket_name}/{remote_path}")
            return True
        except Exception as e:
            logger.exception(f"Error deleting from S3: {e}")
            return False


class NetworkManager:
    """Manage network operations with automatic fallback"""

    def __init__(self):
        """TODO: Document __init__."""
        self.storage_backend = self._initialize_storage_backend()

    def _initialize_storage_backend(self) -> RemoteStorageBackend:
        """Initialize the best available storage backend"""
        # Try backends in priority order
        backends_to_try = [
            ("s3", S3StorageBackend),
            ("local", LocalStorageBackend),
        ]

        for name, backend_factory in backends_to_try:
            try:
                backend = backend_factory()
                if backend.is_available():
                    logger.info(f"Using {name} storage backend")
                    return backend
            except Exception as e:
                logger.warning(f"Failed to initialize {name} backend: {e}")

        # Fallback to local if all else fails
        logger.warning("All network backends failed, using local storage")
        return LocalStorageBackend()

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file using the best available backend"""
        return self.storage_backend.upload_file(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file using the best available backend"""
        return self.storage_backend.download_file(remote_path, local_path)

    def list_files(self, prefix: str = "") -> list[str]:
        """List files using the best available backend"""
        return self.storage_backend.list_files(prefix)

    def delete_file(self, remote_path: str) -> bool:
        """Delete file using the best available backend"""
        return self.storage_backend.delete_file(remote_path)


# Module-level network manager
NETWORK_MANAGER: Optional[NetworkManager] = None


def get_network_manager() -> NetworkManager:
    """Get the global network manager"""
    global NETWORK_MANAGER
    if NETWORK_MANAGER is None:
        NETWORK_MANAGER = NetworkManager()
    return NETWORK_MANAGER


# Initialize manager on import
get_network_manager()

__all__ = [
    "LocalStorageBackend",
    "NetworkManager",
    "RemoteStorageBackend",
    "S3StorageBackend",
    "get_network_manager",
    "register_tool",
]
from .network_tool import register_tool
