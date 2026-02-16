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
import zipfile
import tarfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from nodupe.tools.compression_standard.engine_logic import Compression
from nodupe.tools.mime.mime_logic import MIMEDetection
from nodupe.core.archive_interface import ArchiveHandlerInterface
from nodupe.core.container import container as global_container

class ArchiveHandlerError(Exception):
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
        self._temp_dirs = []
        # Prefer tool-provided detector
        self._mime_detector = global_container.get_service('mime_tool')
        if not self._mime_detector:
            self._mime_detector = MIMEDetection()

    def is_archive_file(self, file_path: str) -> bool:
        """Check if file is an archive.

        Args:
            file_path: Path to file

        Returns:
            True if file is an archive
        """
        try:
            mime_type = self._mime_detector.detect_mime_type(file_path)
            return self._mime_detector.is_archive(mime_type)
        except Exception:
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

    def extract_archive(self, archive_path: str, extract_to: Optional[str] = None, password: Optional[bytes] = None) -> Dict[str, str]:
        """Extract archive contents to directory.

        Args:
            archive_path: Path to archive file
            extract_to: Directory to extract to (None = create temp directory)
            password: Optional password for encrypted archives

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
                password=password
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
            if hasattr(e, '__cause__') and isinstance(e.__cause__, (zipfile.BadZipFile, tarfile.TarError, PermissionError, OSError)):
                raise e.__cause__
            raise ArchiveHandlerError(f"Failed to extract archive {archive_path}: {e}") from e

    def create_archive(self, output_path: str, files: List[str], format: Optional[str] = None) -> str:
        """Create an archive from a list of files.

        Args:
            output_path: Path where archive will be created
            files: List of file paths to include
            format: Archive format (default: detect from output_path)

        Returns:
            Path to created archive
        """
        try:
            output_path_obj = Path(output_path)
            
            # Simple implementation wrapping compression utility for single/multi files
            # Since Compression.compress_file is for single files, we iterate or use a dedicated method.
            # Assuming Compression has create_archive or similar.
            # Checking existing code... Compression has compress_file (single) and create_archive (which calls tar/zip open 'w')?
            # Actually Compression.create_archive isn't shown in snippets but implied.
            # Let's implement it robustly using zipfile/tarfile directly here or via Compression if available.
            # To stick to "Standard Library Only" mandate and reuse Compression class logic if possible.
            
            # For this remediation, I will use Compression.compress_file if list has 1 file, 
            # or implement multi-file zip here if Compression lacks it.
            # Given previous LogCompressor implementation used zipfile directly, let's move that logic here.
            
            # Detect format
            if not format:
                format = self.detect_archive_format(output_path) or 'zip'
                
            if format == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in files:
                        p = Path(f)
                        if p.exists():
                            zf.write(p, arcname=p.name)
            elif format.startswith('tar'):
                mode = 'w:gz' if 'gz' in format else 'w'
                with tarfile.open(output_path, mode) as tf:
                    for f in files:
                        p = Path(f)
                        if p.exists():
                            tf.add(p, arcname=p.name)
            else:
                raise ArchiveHandlerError(f"Unsupported creation format: {format}")
                
            return output_path

        except Exception as e:
            raise ArchiveHandlerError(f"Failed to create archive {output_path}: {e}") from e

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
                        relative_path = str(Path(archive_path).name) + '/' + str(extracted_file.relative_to(extracted_file.parent))

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
