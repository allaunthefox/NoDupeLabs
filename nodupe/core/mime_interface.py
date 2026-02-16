# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""MIME Detection Interface.

Defines the interface for MIME detection aspects to be used by plugins and core.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict
from pathlib import Path

class MIMEDetectionInterface(ABC):
    """Abstract base class for MIME detectors."""

    @abstractmethod
    def detect_mime_type(self, file_path: str, use_magic: bool = True) -> str:
        """Detect MIME type."""

    @abstractmethod
    def get_extension_for_mime(self, mime_type: str) -> Optional[str]:
        """Get file extension for MIME type."""

    @abstractmethod
    def is_text(self, mime_type: str) -> bool:
        """Check if MIME type is text."""

    @abstractmethod
    def is_image(self, mime_type: str) -> bool:
        """Check if MIME type is image."""

    @abstractmethod
    def is_audio(self, mime_type: str) -> bool:
        """Check if MIME type is audio."""

    @abstractmethod
    def is_video(self, mime_type: str) -> bool:
        """Check if MIME type is video."""

    @abstractmethod
    def is_archive(self, mime_type: str) -> bool:
        """Check if MIME type is archive."""
