# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Archive Handler Module.

Archive file detection and extraction using standard library only.

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation

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

import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional

from nodupe.core.archive_interface import ArchiveHandlerInterface
from nodupe.core.container import container as global_container
from nodupe.tools.compression_standard.engine_logic import Compression
from nodupe.tools.mime.mime_logic import MIMEDetection


class ArchiveHandlerError(Exception):  # pylint: disable=redefined-outer-name
    """Archive handling error"""

class ArchiveHandler(ArchiveHandlerInterface):
    """Handle archive file detection and extraction.

    Responsibilities:
    - Detect archive files
    - Extract archive contents
    - Manage temporary directories
    - Clean up extracted files
    """

    def __init__(self):
        """Initialize archive handler."""
        self._temp_dirs: list[str] = []
        # Prefer tool-provided detector
        mime_tool = global_container.get_service('mime_tool')
        # Use type: ignore to suppress Pylance warnings since we check for None
        self._mime_detector = mime_tool if mime_tool is not None else MIMEDetection()  # type: ignore[assignment]

    def is_archive_file(self, file_path: str) -> bool:
        """Check if file is an archive.

        Args:
            file_path: Path to file

        Returns:
            True if file is an archive
        """
        try:
            mime_type = self._mime_detector.detect_mime_type(file_path)
            if mime_type is None:
                return False
            # Handle case where is_archive might return None
            is_archive_result = self._mime_detector.is_archive(mime_type)
            return is_archive_result if is_archive_result is not None else False
        except Exception:  # pylint: disable=broad-except
            return False

    def detect_archive_format(self, file_path: str) -> Optional[str]:
        """Detect archive format from MIME type or file extension.

        Args:
            file_path: Path to file

        Returns:
            Detected format ('zip', 'tar', etc.) or None if unknown
        """
        if not Path(file_path).exists():
            return None

        mime_type = self._mime_detector.detect_mime_type(file_path)
        if mime_type is None:
            mime_type = MIMEDetection.detect_mime_type(file_path)

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
            path_lower = file_path.lower()
            if path_lower.endswith('.zip'):
                archive_format = 'zip'
            elif path_lower.endswith('.tar'):
                archive_format = 'tar'
            elif path_lower.endswith('.tar.gz') or path_lower.endswith('.tgz'):
                archive_format = 'tar.gz'
            elif path_lower.endswith('.tar.bz2') or path_lower.endswith('.tbz2'):
                archive_format = 'tar.bz2'
            elif path_lower.endswith('.tar.xz') or path_lower.endswith('.txz'):
                archive_format = 'tar.xz'
            elif path_lower.endswith('.tar.lzma'):
                archive_format = 'tar.lzma'

        return archive_format

    def extract_archive(
        self,
        archive_path: str,
        extract_to: Optional[str] = None,
        PASSWORD_REMOVED: Optional[bytes] = None
    ) -> dict[str, str]:
        """Extract archive contents to directory.

        Args:
            archive_path: Path to archive file
            extract_to: Directory to extract to (None = create temp directory)
            PASSWORD_REMOVED: Optional password for encrypted archives

        Returns:
            Dictionary mapping relative paths within archive to absolute paths on disk

        Raises:
            FileNotFoundError: If archive file does not exist
            ArchiveHandlerError: If extraction fails
        """
        try:
            archive_path_obj = Path(archive_path)
            if not archive_path_obj.exists():
                raise FileNotFoundError(f"Archive file not found: {archive_path}")

            # Create extraction directory if not provided
            if extract_to is None:
                temp_dir = tempfile.mkdtemp(prefix='nodupe_archive_')
                self._temp_dirs.append(temp_dir)
                extract_dir = Path(temp_dir)
            else:
                extract_dir = Path(extract_to)
                extract_dir.mkdir(parents=True, exist_ok=True)

            # Detect archive format
            archive_format = self.detect_archive_format(archive_path)
            if not archive_format:
                mime_type = MIMEDetection.detect_mime_type(archive_path)
                raise ArchiveHandlerError(f"Unsupported archive format: {mime_type}")

            # Extract archive
            extracted_paths = Compression.extract_archive(
                archive_path_obj,
                extract_dir,
                archive_format,
                PASSWORD_REMOVED
            )

            # Convert to dictionary of relative paths to absolute strings
            # This matches the API expected by the tests
            result = {}
            for p in extracted_paths:
                try:
                    rel_path = str(p.relative_to(extract_dir))
                    result[rel_path] = str(p)
                except ValueError:
                    # Fallback if somehow not relative
                    result[p.name] = str(p)

            return result

        except (FileNotFoundError, zipfile.BadZipFile, tarfile.TarError):
            raise
        except Exception as e:
            # Check if the cause is one of the types we should re-raise
            if hasattr(e, '__cause__') and isinstance(
                e.__cause__,
                (zipfile.BadZipFile, tarfile.TarError, PermissionError, OSError)
            ):
                cause = e.__cause__
                if isinstance(cause, BaseException):
                    raise cause from e  # pylint: disable=raising-non-exception
            raise ArchiveHandlerError(
                f"Failed to extract archive {archive_path}: {e}"
            ) from e

    def create_archive(
        self,
        output_path: str,
        files: list[str],
        archive_format: Optional[str] = None
    ) -> str:
        """Create an archive from a list of files.

        Args:
            output_path: Path where archive will be created
            files: List of file paths to include
            archive_format: Archive format (default: detect from output_path)

        Returns:
            Path to created archive
        """
        try:
            # Detect format
            if not archive_format:
                archive_format = self.detect_archive_format(output_path) or 'zip'

            if archive_format == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in files:
                        p = Path(f)
                        if p.exists():
                            zf.write(p, arcname=p.name)
            elif archive_format.startswith('tar'):
                mode = 'w:gz' if 'gz' in archive_format else 'w'
                with tarfile.open(output_path, mode) as tf:
                    for f in files:
                        p = Path(f)
                        if p.exists():
                            tf.add(p, arcname=p.name)
            else:
                raise ArchiveHandlerError(
                    f"Unsupported creation format: {archive_format}"
                )

            return output_path

        except ArchiveHandlerError:
            raise
        except Exception as e:
            raise ArchiveHandlerError(
                f"Failed to create archive {output_path}: {e}"
            ) from e

    def get_archive_contents_info(
        self,
        archive_path: str,
        base_path: str
    ) -> list[dict[str, Any]]:
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
            for relative_path, absolute_path in extracted_files.items():
                file_path = Path(absolute_path)
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        archive_rel_path = (
                            str(Path(archive_path).name) + '/' + relative_path
                        )

                        file_info = {
                            'path': str(file_path),
                            'relative_path': archive_rel_path,
                            'name': file_path.name,
                            'suffix': file_path.suffix.lower(),
                            'size': stat.st_size,
                            'modified_time': int(stat.st_mtime),
                            'created_time': int(stat.st_ctime),
                            'is_directory': False,
                            'is_file': True,
                            'is_symlink': file_path.is_symlink(),
                            'is_archive_content': True,
                            'archive_source': archive_path,
                            'archive_path': archive_rel_path
                        }
                        file_infos.append(file_info)

                    except Exception as e:  # pylint: disable=broad-except
                        print(
                            f"[WARNING] Error processing extracted "
                            f"file {file_path}: {e}"
                        )
                        continue

            return file_infos

        except Exception as e:  # pylint: disable=broad-except
            print(
                f"[WARNING] Error getting archive contents "
                f"for {archive_path}: {e}"
            )
            return []

    def cleanup(self) -> None:
        """Clean up temporary directories.

        Remove all temporary directories created during extraction.
        """
        for temp_dir in self._temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:  # pylint: disable=broad-except
                print(
                    f"[WARNING] Error cleaning up temporary "
                    f"directory {temp_dir}: {e}"
                )

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
