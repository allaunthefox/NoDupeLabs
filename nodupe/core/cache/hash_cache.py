"""Hash Cache.

Cache file hashes based on path and modification time.
"""

from pathlib import Path

class HashCache:
    """Cache file hashes"""

    def __init__(self):
        self.cache = {}

    def get_hash(self, file_path: Path) -> str:
        """Get cached hash for a file"""
        # Implementation would go here
        raise NotImplementedError("Hash cache not implemented yet")

    def set_hash(self, file_path: Path, hash_value: str) -> None:
        """Set hash for a file"""
        # Implementation would go here
        raise NotImplementedError("Hash cache not implemented yet")

    def invalidate_cache(self, file_path: Path) -> None:
        """Invalidate cache for a file"""
        # Implementation would go here
        raise NotImplementedError("Hash cache not implemented yet")
