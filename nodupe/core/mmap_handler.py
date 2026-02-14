"""Memory-Mapped File Handler.

Handle memory-mapped files for efficient large file processing.
"""

import mmap
import os
from contextlib import contextmanager


class MMAPHandler:
    """Handle memory-mapped file operations"""

    @staticmethod
    def create_mmap(file_path: str, access_mode: int = mmap.ACCESS_READ) -> mmap.mmap:
        """Create memory-mapped file for efficient access

        Args:
            file_path: Path to the file to map
            access_mode: Memory mapping access mode (default: ACCESS_READ)

        Returns:
            Memory-mapped file object
        """
        with open(file_path, 'rb') as f:
            # Get file size to ensure we can create the mapping
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                # For empty files, create a minimal mapping
                return mmap.mmap(-1, 1)  # Create anonymous mapping

            # Create memory mapping
            mapped_file = mmap.mmap(f.fileno(), 0, access=access_mode)
            return mapped_file

    @staticmethod
    @contextmanager
    def mmap_context(file_path: str, access_mode: int = mmap.ACCESS_READ):
        """Context manager for safe memory-mapped file operations

        Args:
            file_path: Path to the file to map
            access_mode: Memory mapping access mode
        """
        mapped_file = None
        try:
            mapped_file = MMAPHandler.create_mmap(file_path, access_mode)
            yield mapped_file
        finally:
            if mapped_file:
                mapped_file.close()

    @staticmethod
    def read_chunk(mapped_file: mmap.mmap, offset: int, size: int) -> bytes:
        """Read a chunk from memory-mapped file

        Args:
            mapped_file: Memory-mapped file object
            offset: Starting position to read from
            size: Number of bytes to read

        Returns:
            Bytes read from the mapped file
        """
        original_pos = mapped_file.tell()
        try:
            mapped_file.seek(offset)
            return mapped_file.read(size)
        finally:
            mapped_file.seek(original_pos)

    @staticmethod
    def get_file_size(mapped_file: mmap.mmap) -> int:
        """Get the size of the memory-mapped file

        Args:
            mapped_file: Memory-mapped file object

        Returns:
            Size of the file in bytes
        """
        return len(mapped_file)
