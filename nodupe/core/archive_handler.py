# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Archive Handler Module.

Archive file detection and extraction using standard library only.

Key Features:
    - Archive file detection (ZIP, TAR, etc.)
    - Archive content extraction
    - Temporary file management
    - Integration with existing compression utilities
    - Standard library only (no external dependencies)

Dependencies:
    - pathlib (standard library)
    - tempfile (standard library)
    - typing (standard library)
    - nodupe.core.compression
    - nodupe.core.mime_detection
"""

import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from .compression import Compression
from .mime_detection import MIMEDetection


class ArchiveHandlerError(Exception):
    """Archive handling error"""


class ArchiveHandler:
    """Handle archive file detection and extraction.

    Responsibilities:
    - Detect archive files
    - Extract archive contents
    - Manage temporary directories
    - Clean up extracted files
    """

    def __init__(self):
        """Initialize archive handler."""
        self._temp_dirs = []

    def is_archive_file(self, file_path: str) -> bool:
        """Check if file is an archive.

        Args:
            file_path: Path to file

        Returns:
            True if file is an archive
        """
        try:
            mime_type = MIMEDetection.detect_mime_type(file_path)
            return MIMEDetection.is_archive(mime_type)
        except Exception:
            return False

    def extract_archive(self, archive_path: str, extract_to: Optional[str] = None) -> List[Path]:
        """Extract archive contents to directory.

        Args:
            archive_path: Path to archive file
            extract_to: Directory to extract to (None = create temp directory)

        Returns:
            List of extracted file paths

        Raises:
            ArchiveHandlerError: If extraction fails
        """
        try:
            archive_path_obj = Path(archive_path)
            if not archive_path_obj.exists():
                raise ArchiveHandlerError(f"Archive file not found: {archive_path}")

            # Create extraction directory if not provided
            if extract_to is None:
                temp_dir = tempfile.mkdtemp(prefix='nodupe_archive_')
                self._temp_dirs.append(temp_dir)
                extract_dir = Path(temp_dir)
            else:
                extract_dir = Path(extract_to)
                extract_dir.mkdir(parents=True, exist_ok=True)

            # Detect archive format
            mime_type = MIMEDetection.detect_mime_type(archive_path)
            format_map = {
                'application/zip': 'zip',
                'application/x-tar': 'tar',
                'application/gzip': 'tar.gz',
                'application/x-bzip2': 'tar.bz2',
                'application/x-xz': 'tar.xz',
                'application/x-lzma': 'tar.lzma',
            }

            archive_format = format_map.get(mime_type)
            if not archive_format:
                # Try to detect from extension
                if archive_path.lower().endswith('.zip'):
                    archive_format = 'zip'
                elif archive_path.lower().endswith('.tar'):
                    archive_format = 'tar'
                elif archive_path.lower().endswith('.tar.gz') or archive_path.lower().endswith('.tgz'):
                    archive_format = 'tar.gz'
                elif archive_path.lower().endswith('.tar.bz2') or archive_path.lower().endswith('.tbz2'):
                    archive_format = 'tar.bz2'
                elif archive_path.lower().endswith('.tar.xz') or archive_path.lower().endswith('.txz'):
                    archive_format = 'tar.xz'
                elif archive_path.lower().endswith('.tar.lzma'):
                    archive_format = 'tar.lzma'
                else:
                    raise ArchiveHandlerError(f"Unsupported archive format: {mime_type}")

            # Extract archive
            extracted_files = Compression.extract_archive(
                archive_path=archive_path_obj,
                output_dir=extract_dir,
                format_=archive_format  # Changed from format to format_ to avoid conflict with built-in format
            )

            return extracted_files

        except Exception as e:
            raise ArchiveHandlerError(f"Failed to extract archive {archive_path}: {e}") from e

    def get_archive_contents_info(self, archive_path: str, base_path: str) -> List[Dict[str, Any]]:
        """Get file information for archive contents.

        Args:
            archive_path: Path to archive file
            base_path: Base path for relative path calculation

        Returns:
            List of file information dictionaries for archive contents
        """
        try:
            # Extract archive to temporary directory
            extracted_files = self.extract_archive(archive_path)

            file_infos = []
            for extracted_file in extracted_files:
                if extracted_file.is_file():
                    try:
                        stat = extracted_file.stat()
                        relative_path = str(Path(archive_path).name) + '/' + str(extracted_file.relative_to(extracted_file.parent.parent))

                        file_info = {
                            'path': str(extracted_file),
                            'relative_path': relative_path,
                            'name': extracted_file.name,
                            'extension': extracted_file.suffix.lower(),
                            'size': stat.st_size,
                            'modified_time': int(stat.st_mtime),
                            'created_time': int(stat.st_ctime),
                            'is_directory': False,
                            'is_file': True,
                            'is_symlink': extracted_file.is_symlink(),
                            'is_archive_content': True,
                            'archive_source': archive_path,
                            'archive_path': relative_path
                        }
                        file_infos.append(file_info)

                    except Exception as e:
                        print(f"[WARNING] Error processing extracted file {extracted_file}: {e}")
                        continue

            return file_infos

        except Exception as e:
            print(f"[WARNING] Error getting archive contents for {archive_path}: {e}")
            return []

    def cleanup(self) -> None:
        """Clean up temporary directories.

        Remove all temporary directories created during extraction.
        """
        for temp_dir in self._temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"[WARNING] Error cleaning up temporary directory {temp_dir}: {e}")

        self._temp_dirs = []

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


def create_archive_handler() -> ArchiveHandler:
    """Create and return an ArchiveHandler instance.

    Returns:
        ArchiveHandler instance
    """
    return ArchiveHandler()
