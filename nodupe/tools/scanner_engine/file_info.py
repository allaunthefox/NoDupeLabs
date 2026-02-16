"""
File Information
Get basic file information using only standard library
"""

from pathlib import Path
from typing import Dict, Any


class FileInfo:
    """Get file information"""

    def __init__(self, file_path: Path):
        """TODO: Document __init__."""
        self.file_path = file_path

    def get_info(self) -> Dict[str, Any]:
        """Get file information"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File {self.file_path} does not exist")

        stat = self.file_path.stat()
        return {
            'path': str(self.file_path),
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'ctime': stat.st_ctime,
            'is_file': self.file_path.is_file(),
            'is_dir': self.file_path.is_dir(),
            'is_symlink': self.file_path.is_symlink()
        }
