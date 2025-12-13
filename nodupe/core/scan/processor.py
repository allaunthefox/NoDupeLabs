# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File processor for metadata extraction and duplicate detection.

This module provides file processing functionality including metadata extraction,
hashing, and duplicate detection using only standard library.

Key Features:
    - File metadata extraction
    - Cryptographic hashing
    - Duplicate detection
    - Batch processing
    - Error handling

Dependencies:
    - hashlib (standard library)
    - os (standard library)
    - typing (standard library)
"""

import os
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Callable
from .walker import FileWalker

class FileProcessor:
    """File processor for metadata extraction and duplicate detection.

    Responsibilities:
    - Process files and extract metadata
    - Calculate file hashes
    - Detect duplicates
    - Handle processing errors
    - Support batch operations
    """

    def __init__(self, file_walker: Optional[FileWalker] = None):
        """Initialize file processor.

        Args:
            file_walker: Optional FileWalker instance
        """
        self.file_walker = file_walker or FileWalker()
        self._hash_algorithm = 'sha256'
        self._hash_buffer_size = 65536  # 64KB buffer

    def process_files(self, root_path: str, file_filter: Optional[Callable[[Any], bool]] = None,
                     on_progress: Optional[Callable[[Any], None]] = None) -> List[Dict[str, Any]]:
        """Process files in directory and return processed file information.

        Args:
            root_path: Root directory to process
            file_filter: Optional function to filter files
            on_progress: Optional callback for progress updates

        Returns:
            List of processed file information
        """
        # First, walk the directory to get file list
        files = self.file_walker.walk(root_path, file_filter, on_progress)

        # Then process each file to add hashes and other metadata
        processed_files = []
        for i, file_info in enumerate(files):
            try:
                processed_file = self._process_single_file(file_info)

                if processed_file:
                    processed_files.append(processed_file)

                # Update progress
                if on_progress and (i % 10 == 0 or i == len(files) - 1):
                    progress = {
                        'files_processed': i + 1,
                        'total_files': len(files),
                        'current_file': file_info['path']
                    }
                    on_progress(progress)

            except Exception as e:
                print(f"[WARNING] Error processing file {file_info['path']}: {e}")
                continue

        return processed_files

    def _process_single_file(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single file and return enhanced file information.

        Args:
            file_info: Basic file information

        Returns:
            Enhanced file information with hash and metadata
        """
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_info['path'])

            # Create enhanced file info
            processed_file = {
                **file_info,
                'hash': file_hash,
                'hash_algorithm': self._hash_algorithm,
                'is_duplicate': False,
                'duplicate_of': None
            }

            return processed_file

        except Exception as e:
            print(f"[WARNING] Error processing file {file_info['path']}: {e}")
            return None

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate cryptographic hash of file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal hash string
        """
        try:
            hasher = hashlib.new(self._hash_algorithm)

            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(self._hash_buffer_size)
                    if not data:
                        break
                    hasher.update(data)

            return hasher.hexdigest()

        except Exception as e:
            print(f"[WARNING] Error calculating hash for {file_path}: {e}")
            raise

    def detect_duplicates(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect duplicates in list of files.

        Args:
            files: List of file information

        Returns:
            List of files with duplicate information updated
        """
        if not files:
            return files

        # Group files by hash
        hash_groups = {}
        for file_info in files:
            if 'hash' not in file_info or not file_info['hash']:
                continue

            file_hash = file_info['hash']
            if file_hash not in hash_groups:
                hash_groups[file_hash] = []
            hash_groups[file_hash].append(file_info)

        # Mark duplicates
        for file_hash, group in hash_groups.items():
            if len(group) > 1:
                # Sort by file size (largest is likely original)
                group.sort(key=lambda x: x['size'], reverse=True)

                # First file is original, rest are duplicates
                original_file = group[0]
                for duplicate_file in group[1:]:
                    duplicate_file['is_duplicate'] = True
                    duplicate_file['duplicate_of'] = original_file['path']

        return files

    def batch_process_files(self, file_paths: List[str],
                          on_progress: Optional[Callable[[Any], None]] = None) -> List[Dict[str, Any]]:
        """Process multiple files in batch.

        Args:
            file_paths: List of file paths to process
            on_progress: Optional progress callback

        Returns:
            List of processed file information
        """
        processed_files = []

        for i, file_path in enumerate(file_paths):
            try:
                if not os.path.isfile(file_path):
                    continue

                file_info = self._get_basic_file_info(file_path)
                processed_file = self._process_single_file(file_info)

                if processed_file:
                    processed_files.append(processed_file)

                # Update progress
                if on_progress and (i % 10 == 0 or i == len(file_paths) - 1):
                    progress = {
                        'files_processed': i + 1,
                        'total_files': len(file_paths),
                        'current_file': file_path
                    }
                    on_progress(progress)

            except Exception as e:
                print(f"[WARNING] Error processing file {file_path}: {e}")
                continue

        return processed_files

    def _get_basic_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic file information for a single file.

        Args:
            file_path: Path to file

        Returns:
            Basic file information dictionary
        """
        try:
            stat = os.stat(file_path)

            return {
                'path': file_path,
                'relative_path': os.path.basename(file_path),
                'name': os.path.basename(file_path),
                'extension': os.path.splitext(file_path)[1].lower(),
                'size': stat.st_size,
                'modified_time': int(stat.st_mtime),
                'created_time': int(stat.st_ctime),
                'is_directory': False,
                'is_file': True,
                'is_symlink': os.path.islink(file_path)
            }
        except Exception as e:
            print(f"[WARNING] Error getting file info for {file_path}: {e}")
            raise

    def set_hash_algorithm(self, algorithm: str) -> None:
        """Set hash algorithm to use.

        Args:
            algorithm: Hash algorithm name (e.g., 'sha256', 'md5')
        """
        if algorithm.lower() not in hashlib.algorithms_available:
            raise ValueError(f"Hash algorithm {algorithm} not available")

        self._hash_algorithm = algorithm.lower()

    def get_hash_algorithm(self) -> str:
        """Get current hash algorithm.

        Returns:
            Current hash algorithm name
        """
        return self._hash_algorithm

    def set_hash_buffer_size(self, buffer_size: int) -> None:
        """Set buffer size for hash calculation.

        Args:
            buffer_size: Buffer size in bytes
        """
        if buffer_size <= 0:
            raise ValueError("Buffer size must be positive")

        self._hash_buffer_size = buffer_size

    def get_hash_buffer_size(self) -> int:
        """Get current hash buffer size.

        Returns:
            Current buffer size in bytes
        """
        return self._hash_buffer_size

def create_file_processor(file_walker: Optional[FileWalker] = None) -> FileProcessor:
    """Create and return a FileProcessor instance.

    Args:
        file_walker: Optional FileWalker instance

    Returns:
        FileProcessor instance
    """
    return FileProcessor(file_walker)
