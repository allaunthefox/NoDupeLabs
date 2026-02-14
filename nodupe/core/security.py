"""Security Module.

Path sanitization and security validation using standard library only.

Key Features:
    - Path sanitization (prevent directory traversal)
    - Path validation and normalization
    - Safe filename generation
    - Permission checking
    - Symlink detection
    - Standard library only (no external dependencies)

Dependencies:
    - pathlib (standard library)
    - os (standard library)
"""

import os
import re
from pathlib import Path
from typing import Optional, List


class SecurityError(Exception):
    """Security validation error"""


class Security:
    """Handle security operations.

    Provides path sanitization, validation, and security checks
    to prevent common vulnerabilities like path traversal attacks.
    """

    # Dangerous path components that should be rejected
    DANGEROUS_PATTERNS = [
        '..',           # Parent directory traversal
        '~',            # Home directory expansion
        '///',          # Multiple slashes
        '\x00',         # Null byte
        '\r',           # Carriage return
        '\n',           # Line feed
    ]

    # Characters not allowed in filenames (Windows + Unix)
    INVALID_FILENAME_CHARS = r'[<>:"|?*\x00-\x1f]'

    # Reserved Windows filenames
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
    }

    @staticmethod
    def sanitize_path(
        path: str,
        allow_absolute: bool = True,
        allow_parent: bool = False
    ) -> str:
        """Sanitize a file path to prevent directory traversal attacks.

        Args:
            path: Path to sanitize
            allow_absolute: Allow absolute paths
            allow_parent: Allow parent directory references (..)

        Returns:
            Sanitized path string

        Raises:
            SecurityError: If path contains dangerous patterns
        """
        try:
            # Convert to string if Path object
            if isinstance(path, Path):
                path = str(path)

            # Check for null bytes
            if '\x00' in path:
                raise SecurityError("Path contains null bytes")

            # Check for dangerous patterns
            if not allow_parent:
                if '..' in path:
                    raise SecurityError("Path contains parent directory reference (..)")

            # Normalize path separators
            path = path.replace('\\', '/')

            # Remove multiple consecutive slashes
            while '//' in path:
                path = path.replace('//', '/')

            # Convert to Path for normalization
            path_obj = Path(path)

            # Check if absolute path is allowed
            if path_obj.is_absolute() and not allow_absolute:
                raise SecurityError("Absolute paths not allowed")

            # Normalize the path
            try:
                normalized = path_obj.resolve()
            except (OSError, RuntimeError):
                # If resolve fails, use manual normalization
                normalized = Path(os.path.normpath(str(path_obj)))

            return str(normalized)

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Path sanitization failed: {e}") from e

    @staticmethod
    def validate_path(
        path: str,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        allowed_parent: Optional[Path] = None
    ) -> bool:
        """Validate a file path for security and existence.

        Args:
            path: Path to validate
            must_exist: If True, path must exist
            must_be_file: If True, path must be a file
            must_be_dir: If True, path must be a directory
            allowed_parent: If set, path must be within this directory

        Returns:
            True if path is valid

        Raises:
            SecurityError: If path is invalid or insecure
        """
        try:
            # Convert to Path object
            if isinstance(path, str):
                path_obj = Path(path)
            else:
                path_obj = path

            # Resolve to absolute path
            try:
                resolved = path_obj.resolve()
            except (OSError, RuntimeError) as e:
                raise SecurityError(f"Cannot resolve path: {e}") from e

            # Check if path must be within allowed parent
            if allowed_parent is not None:
                if isinstance(allowed_parent, str):
                    allowed_parent = Path(allowed_parent)

                try:
                    allowed_resolved = allowed_parent.resolve()
                    # Check if path is relative to allowed parent
                    try:
                        resolved.relative_to(allowed_resolved)
                    except ValueError:
                        raise SecurityError(
                            f"Path {resolved} is outside allowed directory {allowed_resolved}"
                        )
                except (OSError, RuntimeError) as e:
                    raise SecurityError(f"Cannot resolve allowed parent: {e}") from e

            # Check existence
            if must_exist and not resolved.exists():
                raise SecurityError(f"Path does not exist: {resolved}")

            # Check if file
            if must_be_file:
                if not resolved.exists():
                    raise SecurityError(f"File does not exist: {resolved}")
                if not resolved.is_file():
                    raise SecurityError(f"Path is not a file: {resolved}")

            # Check if directory
            if must_be_dir:
                if not resolved.exists():
                    raise SecurityError(f"Directory does not exist: {resolved}")
                if not resolved.is_dir():
                    raise SecurityError(f"Path is not a directory: {resolved}")

            return True

        except SecurityError:
            raise
        except Exception as e:
            raise SecurityError(f"Path validation failed: {e}") from e

    @staticmethod
    def sanitize_filename(
        filename: str,
        replacement: str = '_',
        max_length: int = 255
    ) -> str:
        """Sanitize a filename to be safe across platforms.

        Args:
            filename: Filename to sanitize
            replacement: Character to replace invalid characters with
            max_length: Maximum filename length

        Returns:
            Sanitized filename

        Raises:
            SecurityError: If filename cannot be sanitized
        """
        try:
            # Remove path separators
            filename = os.path.basename(filename)

            # Check for empty filename
            if not filename or filename in ('.', '..'):
                raise SecurityError("Invalid filename")

            # Replace invalid characters
            filename = re.sub(Security.INVALID_FILENAME_CHARS, replacement, filename)

            # Remove leading/trailing spaces and dots
            filename = filename.strip('. ')

            # Check for reserved names (Windows)
            name_without_ext = filename.split('.')[0].upper()
            if name_without_ext in Security.RESERVED_NAMES:
                filename = f"{replacement}{filename}"

            # Truncate to max length
            if len(filename) > max_length:
                # Try to preserve extension
                parts = filename.rsplit('.', 1)
                if len(parts) == 2:
                    name, ext = parts
                    max_name_length = max_length - len(ext) - 1
                    filename = f"{name[:max_name_length]}.{ext}"
                else:
                    filename = filename[:max_length]

            # Final check
            if not filename:
                raise SecurityError("Filename became empty after sanitization")

            return filename

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Filename sanitization failed: {e}") from e

    @staticmethod
    def is_safe_path(path: str, base_directory: str) -> bool:
        """Check if a path is safe (within base directory).

        Args:
            path: Path to check
            base_directory: Base directory that path must be within

        Returns:
            True if path is safe
        """
        try:
            # Convert to Path objects
            path_obj = Path(path).resolve()
            base_obj = Path(base_directory).resolve()

            # Check if path is relative to base
            try:
                path_obj.relative_to(base_obj)
                return True
            except ValueError:
                return False

        except (OSError, RuntimeError):
            return False

    @staticmethod
    def check_permissions(
        path: str,
        readable: bool = False,
        writable: bool = False,
        executable: bool = False
    ) -> bool:
        """Check file permissions.

        Args:
            path: Path to check
            readable: Check if readable
            writable: Check if writable
            executable: Check if executable

        Returns:
            True if all requested permissions are available

        Raises:
            SecurityError: If path doesn't exist or permissions insufficient
        """
        try:
            # Convert to Path object
            if isinstance(path, str):
                path_obj = Path(path)
            else:
                path_obj = path

            # Check existence
            if not path_obj.exists():
                raise SecurityError(f"Path does not exist: {path}")

            # Check read permission
            if readable and not os.access(str(path_obj), os.R_OK):
                raise SecurityError(f"Path not readable: {path}")

            # Check write permission
            if writable and not os.access(str(path_obj), os.W_OK):
                raise SecurityError(f"Path not writable: {path}")

            # Check execute permission
            if executable and not os.access(str(path_obj), os.X_OK):
                raise SecurityError(f"Path not executable: {path}")

            return True

        except SecurityError:
            raise
        except Exception as e:
            raise SecurityError(f"Permission check failed: {e}") from e

    @staticmethod
    def is_symlink(path: str) -> bool:
        """Check if path is a symbolic link.

        Args:
            path: Path to check

        Returns:
            True if path is a symbolic link
        """
        try:
            if isinstance(path, str):
                path = Path(path)
            return path.is_symlink()
        except (OSError, RuntimeError):
            return False

    @staticmethod
    def resolve_symlink(path: str, follow_symlinks: bool = True) -> str:
        """Resolve symbolic links.

        Args:
            path: Path to resolve
            follow_symlinks: If False, don't follow symlinks

        Returns:
            Resolved path

        Raises:
            SecurityError: If path cannot be resolved
        """
        try:
            if isinstance(path, str):
                path = Path(path)

            if follow_symlinks:
                resolved = path.resolve()
            else:
                resolved = path

            return str(resolved)

        except (OSError, RuntimeError) as e:
            raise SecurityError(f"Cannot resolve symlink: {e}") from e

    @staticmethod
    def validate_extension(
        filename: str,
        allowed_extensions: List[str]
    ) -> bool:
        """Validate file extension against allowed list.

        Args:
            filename: Filename to check
            allowed_extensions: List of allowed extensions (with or without dot)

        Returns:
            True if extension is allowed

        Raises:
            SecurityError: If extension is not allowed
        """
        try:
            # Get file extension
            path = Path(filename)
            extension = path.suffix.lower()

            # Normalize allowed extensions (ensure they start with dot)
            normalized_allowed = [
                ext if ext.startswith('.') else f'.{ext}'
                for ext in allowed_extensions
            ]

            if extension not in normalized_allowed:
                raise SecurityError(
                    f"File extension '{extension}' not in allowed list: {normalized_allowed}"
                )

            return True

        except SecurityError:
            raise
        except Exception as e:
            raise SecurityError(f"Extension validation failed: {e}") from e

    @staticmethod
    def generate_safe_filename(
        base_name: str,
        extension: str = '',
        add_timestamp: bool = False
    ) -> str:
        """Generate a safe filename.

        Args:
            base_name: Base filename
            extension: File extension (with or without dot)
            add_timestamp: Add timestamp to ensure uniqueness

        Returns:
            Safe filename
        """
        try:
            # Sanitize base name
            safe_base = Security.sanitize_filename(base_name)

            # Normalize extension
            if extension and not extension.startswith('.'):
                extension = f'.{extension}'

            # Add timestamp if requested
            if add_timestamp:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_base = f"{safe_base}_{timestamp}"

            # Combine
            filename = f"{safe_base}{extension}"

            # Final sanitization
            return Security.sanitize_filename(filename)

        except Exception as e:
            raise SecurityError(f"Safe filename generation failed: {e}") from e
