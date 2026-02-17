# File System Test Utilities
# Helper functions for file system operations testing

import hashlib
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock


def create_test_file_structure(
    base_path: Path,
    structure: dict[str, Union[dict, str, bytes]],
    file_permissions: int = 0o644,
    dir_permissions: int = 0o755,
) -> dict[str, Path]:
    """
    Create a complex file structure for testing.

    Args:
        base_path: Base directory path
        structure: Dictionary describing the file structure
        file_permissions: Permissions for created files
        dir_permissions: Permissions for created directories

    Returns:
        Dictionary mapping file names to their paths
    """
    created_files = {}

    for name, content in structure.items():
        full_path = base_path / name

        if isinstance(content, dict):
            # It's a directory - create it and recurse
            full_path.mkdir(exist_ok=True, mode=dir_permissions)
            created_files.update(
                create_test_file_structure(
                    full_path, content, file_permissions, dir_permissions
                )
            )
        else:
            # It's a file - create it with content
            if isinstance(content, str):
                full_path.write_text(content)
            else:
                full_path.write_bytes(content)

            # Set file permissions
            full_path.chmod(file_permissions)
            created_files[name] = full_path

    return created_files


def create_duplicate_files(
    base_path: Path,
    original_content: str,
    num_duplicates: int = 3,
    file_size: int = 1024,
) -> list[Path]:
    """
    Create multiple duplicate files for testing.

    Args:
        base_path: Directory to create files in
        original_content: Content for original file
        num_duplicates: Number of duplicate files to create
        file_size: Target file size

    Returns:
        List of created file paths
    """
    if not base_path.exists():
        base_path.mkdir(parents=True)

    files = []

    # Create original file
    original_file = base_path / "original.txt"
    if len(original_content) < file_size:
        # Pad content to reach desired size
        multiplier = (file_size // len(original_content)) + 1
        padded_content = original_content * multiplier
        original_file.write_text(padded_content[:file_size])
    else:
        original_file.write_text(original_content[:file_size])

    files.append(original_file)

    # Create duplicates
    for i in range(1, num_duplicates + 1):
        duplicate_file = base_path / f"duplicate_{i}.txt"
        shutil.copy2(original_file, duplicate_file)
        files.append(duplicate_file)

    return files


def create_files_with_varying_sizes(
    base_path: Path, sizes: list[int], content_pattern: str = "Test content "
) -> list[Path]:
    """
    Create files with varying sizes for testing.

    Args:
        base_path: Directory to create files in
        sizes: List of target file sizes in bytes
        content_pattern: Pattern to use for file content

    Returns:
        List of created file paths
    """
    if not base_path.exists():
        base_path.mkdir(parents=True)

    files = []

    for i, size in enumerate(sizes):
        file_path = base_path / f"file_{size}.txt"

        # Create content that matches the desired size
        content = (content_pattern * ((size // len(content_pattern)) + 1))[
            :size
        ]
        file_path.write_text(content)

        files.append(file_path)

    return files


def create_symlinks_and_hardlinks(
    base_path: Path, target_file: Path
) -> dict[str, list[Path]]:
    """
    Create symlinks and hardlinks for testing.

    Args:
        base_path: Directory to create links in
        target_file: Target file for links

    Returns:
        Dictionary with 'symlinks' and 'hardlinks' lists
    """
    if not base_path.exists():
        base_path.mkdir(parents=True)

    result = {"symlinks": [], "hardlinks": []}

    # Create symlinks
    for i in range(3):
        symlink = base_path / f"symlink_{i}.txt"
        try:
            symlink.symlink_to(target_file)
            result["symlinks"].append(symlink)
        except OSError:
            # Symlinks not supported on this system
            break

    # Create hardlinks
    for i in range(3):
        hardlink = base_path / f"hardlink_{i}.txt"
        try:
            hardlink.link_to(target_file)
            result["hardlinks"].append(hardlink)
        except OSError:
            # Hardlinks not supported for this file type
            break

    return result


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file using specified algorithm.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal hash string
    """
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def compare_files(file1: Path, file2: Path) -> bool:
    """
    Compare two files for identical content.

    Args:
        file1: First file path
        file2: Second file path

    Returns:
        True if files have identical content, False otherwise
    """
    if file1.stat().st_size != file2.stat().st_size:
        return False

    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        while True:
            chunk1 = f1.read(4096)
            chunk2 = f2.read(4096)

            if chunk1 != chunk2:
                return False

            if not chunk1:  # End of file
                break

    return True


def create_files_with_different_permissions(
    base_path: Path, permissions: list[int]
) -> list[Path]:
    """
    Create files with different permissions for testing.

    Args:
        base_path: Directory to create files in
        permissions: List of permission modes (e.g., 0o644, 0o755)

    Returns:
        List of created file paths
    """
    if not base_path.exists():
        base_path.mkdir(parents=True)

    files = []

    for i, perm in enumerate(permissions):
        file_path = base_path / f"perm_{oct(perm)}.txt"
        file_path.write_text(f"File with permissions {oct(perm)}")
        file_path.chmod(perm)
        files.append(file_path)

    return files


def create_nested_directory_structure(
    base_path: Path, depth: int = 3, files_per_dir: int = 2
) -> dict[str, list[Path]]:
    """
    Create a nested directory structure for testing.

    Args:
        base_path: Base directory path
        depth: Depth of nesting
        files_per_dir: Number of files per directory

    Returns:
        Dictionary mapping directory paths to their file lists
    """
    structure = {}

    def _create_nested(current_path: Path, current_depth: int):
        if current_depth > depth:
            return

        current_files = []
        for i in range(files_per_dir):
            file_path = current_path / f"file_{current_depth}_{i}.txt"
            file_path.write_text(f"Content at depth {current_depth}")
            current_files.append(file_path)

        structure[str(current_path)] = current_files

        # Create subdirectories
        for i in range(2):  # Create 2 subdirectories per level
            subdir = current_path / f"subdir_{i}"
            subdir.mkdir(exist_ok=True)
            _create_nested(subdir, current_depth + 1)

    _create_nested(base_path, 0)
    return structure


def create_files_with_timestamps(
    base_path: Path, timestamps: list[float]
) -> list[Path]:
    """
    Create files with specific timestamps for testing.

    Args:
        base_path: Directory to create files in
        timestamps: List of timestamps (seconds since epoch)

    Returns:
        List of created file paths
    """
    if not base_path.exists():
        base_path.mkdir(parents=True)

    files = []
    import time

    for i, timestamp in enumerate(timestamps):
        file_path = base_path / f"timestamp_{i}.txt"
        file_path.write_text(f"File created at {timestamp}")

        # Set file timestamps
        os.utime(file_path, (timestamp, timestamp))
        files.append(file_path)

    return files


def verify_file_structure(
    base_path: Path, expected_structure: dict[str, Union[dict, str]]
) -> bool:
    """
    Verify that a file structure matches expected structure.

    Args:
        base_path: Base directory path
        expected_structure: Expected structure dictionary

    Returns:
        True if structure matches, False otherwise
    """
    for name, expected in expected_structure.items():
        full_path = base_path / name

        if isinstance(expected, dict):
            # Should be a directory
            if not full_path.is_dir():
                return False

            if not verify_file_structure(full_path, expected):
                return False
        else:
            # Should be a file
            if not full_path.is_file():
                return False

            if isinstance(expected, str):
                # Check text content
                if full_path.read_text() != expected:
                    return False
            # Check binary content
            elif full_path.read_bytes() != expected:
                return False

    return True


def mock_file_operations() -> MagicMock:
    """
    Create a mock for file system operations.

    Returns:
        Mock object for file operations
    """
    mock = MagicMock()

    # Mock common file operations
    mock.exists.return_value = True
    mock.is_file.return_value = True
    mock.is_dir.return_value = False
    mock.read_text.return_value = "Mock file content"
    mock.read_bytes.return_value = b"Mock binary content"
    mock.write_text.return_value = None
    mock.write_bytes.return_value = None
    mock.unlink.return_value = None
    mock.rename.return_value = None
    mock.stat.return_value = os.stat_result(
        (0o100644, 0, 0, 0, 0, 0, 1024, 0, 0, 0)
    )

    return mock


def create_large_file(
    base_path: Path, size_mb: int = 10, chunk_size: int = 1024 * 1024
) -> Path:
    """
    Create a large file for performance testing.

    Args:
        base_path: Directory to create file in
        size_mb: Size of file in megabytes
        chunk_size: Chunk size for writing

    Returns:
        Path to created file
    """
    if not base_path.exists():
        base_path.mkdir(parents=True)

    file_path = base_path / f"large_{size_mb}mb.dat"
    total_size = size_mb * 1024 * 1024

    with open(file_path, "wb") as f:
        remaining = total_size
        while remaining > 0:
            write_size = min(chunk_size, remaining)
            f.write(os.urandom(write_size))
            remaining -= write_size

    return file_path
