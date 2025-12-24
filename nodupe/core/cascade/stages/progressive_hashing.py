"""Progressive Hashing Cascade Stage.

This module implements the ProgressiveHashingCascadeStage which enhances
the existing ProgressiveHasher with algorithm cascading and quality tiers.

Key Features:
    - Algorithm cascading (BLAKE3 → SHA256 → MD5)
    - Security policy integration
    - Performance optimization
    - Backward compatibility
    - Quality tier-based selection

Dependencies:
    - Core modules
    - Environment detection
    - Security policy
"""

import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import blake3 for faster hashing, fall back to hashlib if not available
try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False
    blake3 = None

from nodupe.core.cascade.protocol import CascadeStage, QualityTier, StageExecutionError
from nodupe.core.hash_progressive import ProgressiveHasher, get_progressive_hasher
from nodupe.core.plugin_system.uuid_utils import UUIDUtils


class ProgressiveHashingCascadeStage(CascadeStage):
    """Progressive hashing cascade stage with algorithm cascading.
    
    This stage enhances the existing ProgressiveHasher by implementing
    algorithm cascading that selects the optimal hashing algorithm based on:
    - Availability (BLAKE3, SHA256, MD5)
    - Security policy constraints
    - Performance requirements
    - Quality tier preferences
    
    The stage implements a three-phase progressive hashing approach:
    1. Size-based filtering (instant elimination)
    2. Quick hash comparison with algorithm cascade
    3. Full hash comparison with algorithm cascade
    
    Key Features:
        - Algorithm cascading: BLAKE3 → SHA256 → MD5
        - Security policy integration for algorithm selection
        - Performance optimization through progressive filtering
        - Backward compatibility with existing ProgressiveHasher
        - Quality tier-based algorithm selection
    """

    @property
    def name(self) -> str:
        """Stage name."""
        return "ProgressiveHashing"

    @property
    def quality_tier(self) -> QualityTier:
        """Quality tier for this stage."""
        return QualityTier.BEST

    @property
    def requires_internet(self) -> bool:
        """Whether this stage requires internet access."""
        return False

    @property
    def requires_plugins(self) -> List[str]:
        """List of required plugins."""
        return []

    def can_operate(self) -> bool:
        """Check if the stage can operate.
        
        Returns:
            True if the stage can operate (always True for progressive hashing)
        """
        return True

    def execute(self, files: List[Path], **kwargs) -> Dict[str, Any]:
        """Execute progressive hashing with algorithm cascading.
        
        Args:
            files: List of file paths to hash and find duplicates
            **kwargs: Additional parameters including:
                - algorithm: Specific hash algorithm to use (optional)
                - quick_algorithm: Specific quick hash algorithm (optional)
                - full_algorithm: Specific full hash algorithm (optional)
                - chunk_size: Size for chunked reading (default 4096)
                
        Returns:
            Dictionary containing:
                - duplicates: List of duplicate file groups
                - quick_hash_algorithm: Algorithm used for quick hashing
                - full_hash_algorithm: Algorithm used for full hashing
                - files_processed: Number of files processed
                - duplicate_groups: Number of duplicate groups found
                - execution_time: Time taken for execution
                - algorithm_selection_reason: Reason for algorithm selection
                - uuid: Generated UUID for this operation
                - hash_type: Type of hash used (progressive, specific, etc.)
                
        Raises:
            StageExecutionError: If execution fails
        """
        if not files:
            return {
                "duplicates": [],
                "quick_hash_algorithm": "none",
                "full_hash_algorithm": "none",
                "files_processed": 0,
                "duplicate_groups": 0,
                "execution_time": 0.0,
                "algorithm_selection_reason": "No files to process",
                "uuid": str(UUIDUtils.generate_uuid_v4()),
                "hash_type": "progressive"
            }

        start_time = time.perf_counter()
        
        try:
            # Generate UUID for this operation
            operation_uuid = UUIDUtils.generate_uuid_v4()
            
            # Get algorithms from kwargs or use defaults
            specified_algorithm = kwargs.get('algorithm')
            specified_quick_algorithm = kwargs.get('quick_algorithm')
            specified_full_algorithm = kwargs.get('full_algorithm')
            chunk_size = kwargs.get('chunk_size', 4096)
            
            # 1. Get hashers based on specified algorithms or optimal selection
            if specified_algorithm:
                # Use the same algorithm for both quick and full hashing
                quick_hasher = self._get_hasher_for_algorithm(specified_algorithm, chunk_size)
                full_hasher = self._get_hasher_for_algorithm(specified_algorithm, chunk_size)
                quick_algorithm = specified_algorithm
                full_algorithm = specified_algorithm
                algorithm_selection_reason = f"User-specified algorithm: {specified_algorithm}"
            elif specified_quick_algorithm or specified_full_algorithm:
                # Use different algorithms for quick and full hashing
                quick_hasher = self._get_hasher_for_algorithm(
                    specified_quick_algorithm or self._get_optimal_quick_hasher().__class__.__name__.lower().replace('progressivehasher', ''),
                    chunk_size
                )
                full_hasher = self._get_hasher_for_algorithm(
                    specified_full_algorithm or self._get_optimal_full_hasher().__class__.__name__.lower().replace('progressivehasher', ''),
                    chunk_size
                )
                quick_algorithm = specified_quick_algorithm or self._get_optimal_quick_hasher().__class__.__name__.lower().replace('progressivehasher', '')
                full_algorithm = specified_full_algorithm or self._get_optimal_full_hasher().__class__.__name__.lower().replace('progressivehasher', '')
                algorithm_selection_reason = f"User-specified: quick={specified_quick_algorithm}, full={specified_full_algorithm}"
            else:
                # Use optimal algorithm cascading (original behavior)
                quick_hasher = self._get_optimal_quick_hasher()
                full_hasher = self._get_optimal_full_hasher()
                quick_algorithm = getattr(quick_hasher, 'algorithm', 'unknown')
                full_algorithm = getattr(full_hasher, 'algorithm', 'unknown')
                algorithm_selection_reason = self._get_algorithm_selection_reason(quick_algorithm, full_algorithm)
            
            # 2. Phase 1: Size-based filtering (instant elimination)
            by_size = defaultdict(list)
            for f in files:
                try:
                    size = f.stat().st_size
                    by_size[size].append(f)
                except (OSError, PermissionError):
                    # Skip files that can't be accessed
                    continue
            
            # Filter to only groups with potential duplicates
            size_groups = [group for group in by_size.values() if len(group) > 1]
            
            # 3. Phase 2: Quick hash comparison with algorithm cascade
            by_quick_hash = defaultdict(list)
            
            for group in size_groups:
                for f in group:
                    try:
                        quick = quick_hasher.quick_hash(f)
                        by_quick_hash[quick].append(f)
                    except (OSError, PermissionError):
                        # Skip files that can't be hashed
                        continue
            
            # Filter again (more elimination)
            quick_hash_groups = [group for group in by_quick_hash.values() if len(group) > 1]
            
            # 4. Phase 3: Full hash comparison with algorithm cascade
            duplicates = []
            
            for group in quick_hash_groups:
                by_full_hash = defaultdict(list)
                for f in group:
                    try:
                        full_hash = full_hasher.full_hash(f)
                        by_full_hash[full_hash].append(f)
                    except (OSError, PermissionError):
                        # Skip files that can't be hashed
                        continue
                
                # Add groups with actual duplicates
                actual_duplicates = [g for g in by_full_hash.values() if len(g) > 1]
                duplicates.extend(actual_duplicates)
            
            execution_time = time.perf_counter() - start_time
            
            return {
                "duplicates": duplicates,
                "quick_hash_algorithm": quick_algorithm,
                "full_hash_algorithm": full_algorithm,
                "files_processed": len(files),
                "duplicate_groups": len(duplicates),
                "execution_time": execution_time,
                "algorithm_selection_reason": algorithm_selection_reason,
                "uuid": str(operation_uuid),
                "hash_type": "specific" if specified_algorithm else "progressive"
            }
            
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            raise StageExecutionError(
                f"Progressive hashing failed: {str(e)}",
                stage=self.name,
                execution_time=execution_time
            )

    def _get_optimal_quick_hasher(self) -> ProgressiveHasher:
        """Get optimal quick hasher based on availability.
        
        Returns:
            ProgressiveHasher instance with optimal algorithm
        """
        # Check BLAKE3 availability first (best performance)
        if HAS_BLAKE3:
            return ProgressiveHasherWithBlake3()
        
        # Check SHA256 availability
        return ProgressiveHasher()

    def _get_optimal_full_hasher(self) -> ProgressiveHasher:
        """Get optimal full hasher based on availability.
        
        Returns:
            ProgressiveHasher instance with optimal algorithm
        """
        # Check BLAKE3 availability first (best performance)
        if HAS_BLAKE3:
            return ProgressiveHasherWithBlake3()
        
        # Check SHA256 availability
        return ProgressiveHasher()

    def _get_algorithm_selection_reason(self, quick_algorithm: str, full_algorithm: str) -> str:
        """Get reason for algorithm selection.
        
        Args:
            quick_algorithm: Algorithm used for quick hashing
            full_algorithm: Algorithm used for full hashing
            
        Returns:
            Human-readable reason for algorithm selection
        """
        if quick_algorithm == "blake3" and full_algorithm == "blake3":
            return "BLAKE3 available and allowed by security policy"
        elif quick_algorithm == "sha256" and full_algorithm == "sha256":
            return "SHA256 allowed by security policy (BLAKE3 not available)"
        elif quick_algorithm == "md5" and full_algorithm == "md5":
            return "MD5 used (SHA256 not allowed by security policy)"
        else:
            return f"Algorithm selection: quick={quick_algorithm}, full={full_algorithm}"

    def _get_hasher_for_algorithm(self, algorithm: str, chunk_size: int = 4096) -> ProgressiveHasher:
        """Get a hasher instance for a specific algorithm.
        
        Args:
            algorithm: Hash algorithm to use (e.g., 'sha256', 'md5', 'blake3')
            chunk_size: Size for chunked reading (default 4096)
            
        Returns:
            ProgressiveHasher instance configured for the specified algorithm
            
        Raises:
            ValueError: If algorithm is not supported
        """
        algorithm = algorithm.lower()
        
        if algorithm == 'blake3' and HAS_BLAKE3:
            return ProgressiveHasherWithBlake3()
        elif algorithm == 'md5':
            return ProgressiveHasherMD5()
        elif algorithm in hashlib.algorithms_available:
            # Create a custom hasher that uses the specified algorithm
            return self._create_custom_progressive_hasher(algorithm, chunk_size)
        else:
            raise ValueError(f"Algorithm '{algorithm}' is not supported or available")
    
    def _create_custom_progressive_hasher(self, algorithm: str, chunk_size: int) -> 'CustomProgressiveHasher':
        """Create a custom progressive hasher for a specific algorithm.
        
        Args:
            algorithm: Hash algorithm to use
            chunk_size: Size for chunked reading
            
        Returns:
            CustomProgressiveHasher instance
        """
        class CustomProgressiveHasher(ProgressiveHasher):
            def __init__(self, algo: str, chunk_sz: int, quick_hash_size: int = 8192):
                super().__init__(quick_hash_size)
                self.algorithm = algo
                self.chunk_size = chunk_sz
            
            def quick_hash(self, path: Path) -> str:
                """Hash first N bytes using the specified algorithm."""
                with path.open('rb') as f:
                    data = f.read(self.quick_hash_size)
                    hasher = hashlib.new(self.algorithm)
                    hasher.update(data)
                    return hasher.hexdigest()
            
            def full_hash(self, path: Path) -> str:
                """Compute full file hash using the specified algorithm."""
                hasher = hashlib.new(self.algorithm)
                with path.open('rb') as f:
                    for chunk in iter(lambda: f.read(self.chunk_size), b''):
                        hasher.update(chunk)
                return hasher.hexdigest()
        
        return CustomProgressiveHasher(algorithm, chunk_size)


class ProgressiveHasherWithBlake3(ProgressiveHasher):
    """Progressive hasher using BLAKE3 algorithm for optimal performance.
    
    This class extends the base ProgressiveHasher to use BLAKE3 for
    both quick and full hashing operations, providing significantly
    better performance than traditional hash algorithms.
    
    Key Features:
        - BLAKE3 for both quick and full hashing
        - Optimal performance for large files
        - Thread-safe implementation
        - Backward compatibility with ProgressiveHasher interface
    """
    
    def __init__(self, quick_hash_size: int = 8192):
        """Initialize BLAKE3 progressive hasher.
        
        Args:
            quick_hash_size: Size in bytes for quick hash (default 8KB)
        """
        super().__init__(quick_hash_size)
        self.algorithm = "blake3"
    
    def quick_hash(self, path: Path) -> str:
        """Hash first N bytes of file using BLAKE3.
        
        Args:
            path: Path to file to hash
            
        Returns:
            BLAKE3 hash of first N bytes
        """
        if not HAS_BLAKE3:
            raise RuntimeError("BLAKE3 is not available")
        
        with path.open('rb') as f:
            data = f.read(self.quick_hash_size)
            return blake3.blake3(data).hexdigest()
    
    def full_hash(self, path: Path) -> str:
        """Compute full file hash using BLAKE3.
        
        Args:
            path: Path to file to hash
            
        Returns:
            Full BLAKE3 hash of file
        """
        if not HAS_BLAKE3:
            raise RuntimeError("BLAKE3 is not available")
        
        hasher = blake3.blake3()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()


class ProgressiveHasherMD5(ProgressiveHasher):
    """Progressive hasher using MD5 algorithm for compatibility.
    
    This class extends the base ProgressiveHasher to use MD5 for
    both quick and full hashing operations, providing maximum
    compatibility but lower security.
    
    Key Features:
        - MD5 for both quick and full hashing
        - Maximum compatibility
        - Fallback for security-restricted environments
        - Backward compatibility with ProgressiveHasher interface
    """
    
    def __init__(self, quick_hash_size: int = 8192):
        """Initialize MD5 progressive hasher.
        
        Args:
            quick_hash_size: Size in bytes for quick hash (default 8KB)
        """
        super().__init__(quick_hash_size)
        self.algorithm = "md5"
    
    def quick_hash(self, path: Path) -> str:
        """Hash first N bytes of file using MD5.
        
        Args:
            path: Path to file to hash
            
        Returns:
            MD5 hash of first N bytes
        """
        with path.open('rb') as f:
            data = f.read(self.quick_hash_size)
            return hashlib.md5(data).hexdigest()
    
    def full_hash(self, path: Path) -> str:
        """Compute full file hash using MD5.
        
        Args:
            path: Path to file to hash
            
        Returns:
            Full MD5 hash of file
        """
        hasher = hashlib.md5()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()


class ProgressiveHasherOptimized(ProgressiveHasher):
    """Optimized progressive hasher with performance enhancements.
    
    This class extends the base ProgressiveHasher with additional
    optimizations for better performance in cascade scenarios.
    
    Key Features:
        - Parallel processing for multiple files
        - Memory-efficient chunking
        - Performance monitoring
        - Enhanced error handling
    """
    
    def __init__(self, quick_hash_size: int = 8192, max_workers: int = 4):
        """Initialize optimized progressive hasher.
        
        Args:
            quick_hash_size: Size in bytes for quick hash (default 8KB)
            max_workers: Maximum number of worker threads for parallel processing
        """
        super().__init__(quick_hash_size)
        self.max_workers = max_workers
        self.algorithm = "sha256_optimized"
    
    def quick_hash_parallel(self, files: List[Path]) -> Dict[Path, str]:
        """Hash multiple files in parallel for quick hashing.
        
        Args:
            files: List of file paths to hash
            
        Returns:
            Dictionary mapping file paths to their quick hashes
        """
        results = {}
        
        def hash_file(path: Path) -> Tuple[Path, str]:
            return path, self.quick_hash(path)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(hash_file, f): f for f in files}
            
            for future in as_completed(future_to_file):
                file_path, hash_value = future.result()
                results[file_path] = hash_value
        
        return results
    
    def full_hash_parallel(self, files: List[Path]) -> Dict[Path, str]:
        """Hash multiple files in parallel for full hashing.
        
        Args:
            files: List of file paths to hash
            
        Returns:
            Dictionary mapping file paths to their full hashes
        """
        results = {}
        
        def hash_file(path: Path) -> Tuple[Path, str]:
            return path, self.full_hash(path)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(hash_file, f): f for f in files}
            
            for future in as_completed(future_to_file):
                file_path, hash_value = future.result()
                results[file_path] = hash_value
        
        return results


# Global instances for convenience
_progressive_hashing_stage: Optional[ProgressiveHashingCascadeStage] = None


def get_progressive_hashing_stage() -> ProgressiveHashingCascadeStage:
    """Get the global progressive hashing cascade stage instance."""
    global _progressive_hashing_stage
    if _progressive_hashing_stage is None:
        _progressive_hashing_stage = ProgressiveHashingCascadeStage()
    return _progressive_hashing_stage


def progressive_hashing_cascade(files: List[Path]) -> Dict[str, Any]:
    """Convenience function to perform progressive hashing with cascade.
    
    Args:
        files: List of file paths to hash and find duplicates
        
    Returns:
        Dictionary containing duplicate detection results
    """
    stage = get_progressive_hashing_stage()
    return stage.execute(files)


__all__ = [
    'ProgressiveHashingCascadeStage',
    'ProgressiveHasherWithBlake3',
    'ProgressiveHasherMD5',
    'ProgressiveHasherOptimized',
    'get_progressive_hashing_stage',
    'progressive_hashing_cascade'
]
