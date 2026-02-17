"""Filesystem Module.

Safe filesystem operations using standard library only.

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation

Key Features:
    - Safe file reading with error handling
    - Safe file writing with atomic operations
    - Path validation and sanitization
    - File existence checking
    - Directory operations

Dependencies:
    - pathlib (standard library)
    - os (standard library)
"""

import contextlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional


class FilesystemError(Exception):
    """Filesystem operation error"""


class Filesystem:
    """Handle safe filesystem operations.

    All operations use standard library only and include comprehensive
    error handling with graceful degradation.
    """

    @staticmethod
    def safe_read(file_path: Path, max_size: Optional[int] = None) -> bytes:
        """Safely read a file with size limits and error handling.

        Args:
            file_path: Path to file to read
            max_size: Maximum file size in bytes (None = no limit)

        Returns:
            File contents as bytes

        Raises:
            FilesystemError: If file cannot be read or exceeds size limit
        """
        try:
            # Convert to Path object if string
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Check if file exists
            if not file_path.exists():
                raise FilesystemError(f"File does not exist: {file_path}")

            # Check if it's a file (not directory)
            if not file_path.is_file():
                raise FilesystemError(f"Path is not a file: {file_path}")

            # Check file size if limit specified
            if max_size is not None:
                file_size = file_path.stat().st_size
                if file_size > max_size:
                    raise FilesystemError(
                        f"File size {file_size} exceeds limit {max_size}: {file_path}"
                    )

            # Read file
            return file_path.read_bytes()

        except OSError as e:
            raise FilesystemError(
                f"Failed to read file {file_path}: {e}"
            ) from e

    @staticmethod
    def safe_write(file_path: Path, data: bytes, atomic: bool = True) -> None:
        """Safely write to a file with atomic operations.

        Args:
            file_path: Path to file to write
            data: Data to write (bytes)
            atomic: Use atomic write (write to temp then rename)

        Raises:
            FilesystemError: If file cannot be written
        """
        try:
            # Convert to Path object if string
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if atomic:
                # Atomic write: write to temp file then rename
                # This ensures file is never partially written
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=file_path.parent, prefix=f".{file_path.name}.tmp"
                )
                try:
                    # Write to temp file
                    os.write(temp_fd, data)
                    os.close(temp_fd)

                    # Rename temp file to target (atomic on POSIX)
                    shutil.move(temp_path, file_path)
                except Exception:
                    # Clean up temp file on error
                    with contextlib.suppress(OSError):
                        os.unlink(temp_path)
                    raise
            else:
                # Direct write
                file_path.write_bytes(data)

        except OSError as e:
            raise FilesystemError(
                f"Failed to write file {file_path}: {e}"
            ) from e

    @staticmethod
    def validate_path(file_path: Path, must_exist: bool = False) -> bool:
        """Validate file path.

        Args:
            file_path: Path to validate
            must_exist: If True, path must exist

        Returns:
            True if path is valid

        Raises:
            FilesystemError: If path is invalid
        """
        try:
            # Convert to Path object if string
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Resolve to absolute path
            resolved = file_path.resolve()

            # Check if must exist
            if must_exist and not resolved.exists():
                raise FilesystemError(f"Path does not exist: {file_path}")

            return True

        except (OSError, RuntimeError) as e:
            raise FilesystemError(f"Invalid path {file_path}: {e}") from e

    @staticmethod
    def get_size(file_path: Path) -> int:
        """Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes

        Raises:
            FilesystemError: If file size cannot be determined
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            return file_path.stat().st_size

        except OSError as e:
            raise FilesystemError(
                f"Failed to get file size {file_path}: {e}"
            ) from e

    @staticmethod
    def list_directory(dir_path: Path, pattern: str = "*") -> list[Path]:
        """List files in directory matching pattern.

        Args:
            dir_path: Directory path
            pattern: Glob pattern (default: "*")

        Returns:
            List of matching file paths

        Raises:
            FilesystemError: If directory cannot be listed
        """
        try:
            if isinstance(dir_path, str):
                dir_path = Path(dir_path)

            if not dir_path.is_dir():
                raise FilesystemError(f"Path is not a directory: {dir_path}")

            return list(dir_path.glob(pattern))

        except OSError as e:
            raise FilesystemError(
                f"Failed to list directory {dir_path}: {e}"
            ) from e

    @staticmethod
    def ensure_directory(dir_path: Path) -> None:
        """Ensure directory exists, create if necessary.

        Args:
            dir_path: Directory path

        Raises:
            FilesystemError: If directory cannot be created
        """
        try:
            if isinstance(dir_path, str):
                dir_path = Path(dir_path)

            dir_path.mkdir(parents=True, exist_ok=True)

        except OSError as e:
            raise FilesystemError(
                f"Failed to create directory {dir_path}: {e}"
            ) from e

    @staticmethod
    def remove_file(file_path: Path, missing_ok: bool = True) -> None:
        """Safely remove a file.

        Args:
            file_path: Path to file to remove
            missing_ok: If True, don't raise error if file doesn't exist

        Raises:
            FilesystemError: If file cannot be removed
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            file_path.unlink(missing_ok=missing_ok)

        except OSError as e:
            raise FilesystemError(
                f"Failed to remove file {file_path}: {e}"
            ) from e

    @staticmethod
    def copy_file(src: Path, dst: Path, overwrite: bool = False) -> None:
        """Safely copy a file.

        Args:
            src: Source file path
            dst: Destination file path
            overwrite: If True, overwrite existing destination file

        Raises:
            FilesystemError: If file cannot be copied
        """
        try:
            if isinstance(src, str):
                src = Path(src)
            if isinstance(dst, str):
                dst = Path(dst)

            if not src.exists():
                raise FilesystemError(f"Source file does not exist: {src}")

            if dst.exists() and not overwrite:
                raise FilesystemError(f"Destination file exists: {dst}")

            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(src, dst)

        except OSError as e:
            raise FilesystemError(
                f"Failed to copy file {src} to {dst}: {e}"
            ) from e

    @staticmethod
    def move_file(src: Path, dst: Path, overwrite: bool = False) -> None:
        """Safely move a file.

        Args:
            src: Source file path
            dst: Destination file path
            overwrite: If True, overwrite existing destination file

        Raises:
            FilesystemError: If file cannot be moved
        """
        try:
            if isinstance(src, str):
                src = Path(src)
            if isinstance(dst, str):
                dst = Path(dst)

            if not src.exists():
                raise FilesystemError(f"Source file does not exist: {src}")

            if dst.exists() and not overwrite:
                raise FilesystemError(f"Destination file exists: {dst}")

            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(src), str(dst))

        except OSError as e:
            raise FilesystemError(
                f"Failed to move file {src} to {dst}: {e}"
            ) from e
