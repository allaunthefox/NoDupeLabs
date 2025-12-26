# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scan plugin for NoDupeLabs.

This plugin provides the scan functionality as a plugin that can be
loaded by the core system. It demonstrates how to convert existing
modules to plugins.

Key Features:
    - Directory scanning
    - File processing
    - Duplicate detection
    - Progress tracking
    - Plugin integration

Dependencies:
    - Core modules
"""

from typing import Any, Dict
import argparse
import time
import os
from pathlib import Path
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.scan.processor import FileProcessor
from nodupe.core.scan.walker import FileWalker
from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection
from nodupe.core.audit import get_audit_logger, AuditEventType
from nodupe.core.confirmation import get_confirmation_manager
from nodupe.core.plugin_system.uuid_utils import UUIDUtils

# Plugin metadata (UUID-based specification)
PLUGIN_METADATA = {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "scan",
    "display_name": "File Scanner Plugin",
    "version": "v1.0.0",
    "description": "Scan directories for duplicate files",
    "author": "NoDupeLabs Team",
    "category": "scanning",
    "dependencies": [],
    "compatibility": {
        "python": ">=3.9",
        "nodupe_core": ">=1.0.0"
    },
    "tags": ["scanning", "duplicate-detection", "file-processing"],
    "marketplace_id": "scan_550e8400-e29b-41d4-a716-446655440000"
}
from nodupe.core.hash_progressive import ProgressiveHasher, get_progressive_hasher

# Try to import rich for enhanced formatting, fall back to basic if not available
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None
    Table = None
    Progress = None
    SpinnerColumn = None
    BarColumn = None
    TextColumn = None
    rprint = print


class ScanPlugin(Plugin):
    """Scan plugin implementation."""

    def __init__(self):
        """Initialize scan plugin with UUID metadata."""
        super().__init__(PLUGIN_METADATA)

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._initialized = False

    def api_call(self, method: str, **kwargs: Any) -> Any:
        """Handle API calls to the scan plugin.
        
        Args:
            method: API method name
            **kwargs: Method arguments
            
        Returns:
            API response
            
        Raises:
            ValueError: If method is not supported
        """
        if method == 'generate_scan_uuid':
            return self._generate_scan_uuid(**kwargs)
        elif method == 'hash_file':
            return self._hash_file(**kwargs)
        elif method == 'get_available_hash_types':
            return self._get_available_hash_types(**kwargs)
        else:
            raise ValueError(f"Unsupported API method: {method}")

    def _generate_scan_uuid(self, **kwargs: Any) -> Dict[str, Any]:
        """Generate a UUID for scan operations via API.
        
        Args:
            **kwargs: Additional parameters (optional)
            
        Returns:
            Dict containing the generated UUID and metadata
        """
        try:
            scan_uuid = UUIDUtils.generate_uuid_v4()
            
            result = {
                'uuid': str(scan_uuid),
                'uuid_version': scan_uuid.version,
                'variant': str(scan_uuid.variant),
                'timestamp': scan_uuid.time,
                'urn_format': f"urn:uuid:{scan_uuid}",
                'canonical_format': str(scan_uuid),
                'generated_at': time.time()
            }
            
            # Log the UUID generation for audit purposes
            audit_logger = get_audit_logger()
            audit_logger.log_uuid_generated(str(scan_uuid), 'scan_operation')
            
            return result
            
        except Exception as e:
            return {
                'error': f"Failed to generate UUID: {str(e)}",
                'success': False
            }

    def _get_available_hash_types(self, **kwargs: Any) -> Dict[str, Any]:
        """Get available hash types supported by the system.
        
        Args:
            **kwargs: Additional parameters (optional)
            
        Returns:
            Dict containing available hash types and their properties
        """
        try:
            # Get available hash types from hashlib and blake3 if available
            available_hashes = {}
            
            # Standard hashlib algorithms
            hashlib_algorithms = [
                'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512',
                'blake2b', 'blake2s', 'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512'
            ]
            
            for algo in hashlib_algorithms:
                try:
                    hash_obj = getattr(hashlib, algo)()
                    available_hashes[algo] = {
                        'algorithm': algo,
                        'digest_size': hash_obj.digest_size,
                        'block_size': getattr(hash_obj, 'block_size', 'unknown'),
                        'type': 'standard'
                    }
                except AttributeError:
                    continue
            
            # Blake3 if available
            if 'blake3' in globals() and blake3 is not None:
                available_hashes['blake3'] = {
                    'algorithm': 'blake3',
                    'digest_size': 32,
                    'block_size': 64,
                    'type': 'fast'
                }
            
            # Progressive hashing types
            progressive_hasher = get_progressive_hasher()
            available_hashes['progressive_quick'] = {
                'algorithm': 'progressive_quick',
                'digest_size': 32,  # SHA256 digest size
                'block_size': 8192,  # Default quick hash size
                'type': 'progressive',
                'description': 'Quick hash of first N bytes for filtering'
            }
            
            available_hashes['progressive_full'] = {
                'algorithm': 'progressive_full',
                'digest_size': 32,  # SHA256 digest size or BLAKE3
                'block_size': 4096,  # Chunk size for full hashing
                'type': 'progressive',
                'description': 'Full file hash using progressive algorithm'
            }
            
            return {
                'available_hash_types': available_hashes,
                'count': len(available_hashes),
                'generated_at': time.time()
            }
            
        except Exception as e:
            return {
                'error': f"Failed to get available hash types: {str(e)}",
                'success': False
            }

    def _hash_file(self, **kwargs: Any) -> Dict[str, Any]:
        """Hash a file using the specified algorithm.
        
        Args:
            **kwargs: 
                - file_path: Path to the file to hash
                - algorithm: Hash algorithm to use (default: 'sha256')
                - chunk_size: Size of chunks to read (default: 8192)
            
        Returns:
            Dict containing hash result and metadata
        """
        try:
            file_path = kwargs.get('file_path')
            algorithm = kwargs.get('algorithm', 'sha256')
            chunk_size = kwargs.get('chunk_size', 8192)
            
            if not file_path:
                return {
                    'error': 'file_path is required',
                    'success': False
                }
            
            path = Path(file_path)
            if not path.exists():
                return {
                    'error': f'File does not exist: {file_path}',
                    'success': False
                }
            
            if not path.is_file():
                return {
                    'error': f'Path is not a file: {file_path}',
                    'success': False
                }
            
            # Check if algorithm is available
            available_types = self._get_available_hash_types()
            if not available_types.get('success', True):
                return available_types
            
            if algorithm not in available_types['available_hash_types']:
                return {
                    'error': f'Algorithm not supported: {algorithm}. Available: {list(available_types["available_hash_types"].keys())}',
                    'success': False
                }
            
            # Perform the hashing based on algorithm type
            if algorithm == 'blake3':
                if not blake3:
                    return {
                        'error': 'blake3 is not available',
                        'success': False
                    }
                
                hasher = blake3.blake3()
                with path.open('rb') as f:
                    for chunk in iter(lambda: f.read(chunk_size), b''):
                        hasher.update(chunk)
                hash_result = hasher.hexdigest()
                
            elif algorithm.startswith('progressive_'):
                progressive_hasher = get_progressive_hasher()
                if algorithm == 'progressive_quick':
                    hash_result = progressive_hasher.quick_hash(path)
                elif algorithm == 'progressive_full':
                    hash_result = progressive_hasher.full_hash(path)
                else:
                    return {
                        'error': f'Unknown progressive algorithm: {algorithm}',
                        'success': False
                    }
                    
            else:
                # Standard hashlib algorithm
                hasher = getattr(hashlib, algorithm)()
                with path.open('rb') as f:
                    for chunk in iter(lambda: f.read(chunk_size), b''):
                        hasher.update(chunk)
                hash_result = hasher.hexdigest()
            
            file_stat = path.stat()
            
            result = {
                'file_path': str(path),
                'algorithm': algorithm,
                'hash': hash_result,
                'file_size': file_stat.st_size,
                'file_mtime': file_stat.st_mtime,
                'chunk_size': chunk_size,
                'success': True,
                'generated_at': time.time()
            }
            
            # Log the hash operation for audit purposes
            audit_logger = get_audit_logger()
            audit_logger.log_file_hashed(str(path), hash_result, algorithm)
            
            return result
            
        except Exception as e:
            return {
                'error': f"Failed to hash file: {str(e)}",
                'success': False
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {
            'commands': ['scan'],
            'api_calls': [
                'generate_scan_uuid',
                'hash_file',
                'get_available_hash_types'
            ]
        }

    def _on_scan_start(self, **kwargs: Any) -> None:
        """Handle scan start event."""
        print(f"[PLUGIN] Scan started: {kwargs.get('path', 'unknown')}")

    def _on_scan_complete(self, **kwargs: Any) -> None:
        """Handle scan complete event."""
        print(f"[PLUGIN] Scan completed: {kwargs.get('files_processed', 0)} files processed")

    def register_commands(self, subparsers: Any) -> None:
        """Register scan command with argument parser."""
        scan_parser = subparsers.add_parser('scan', help='Scan directories for duplicates')
        scan_parser.add_argument('paths', nargs='+', help='Directories to scan')
        scan_parser.add_argument('--min-size', type=int, default=0, help='Minimum file size')
        scan_parser.add_argument('--max-size', type=int, help='Maximum file size')
        scan_parser.add_argument('--extensions', nargs='+', help='File extensions to include')
        scan_parser.add_argument('--exclude', nargs='+', help='Directories to exclude')
        scan_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        scan_parser.add_argument('--generate-uuid', action='store_true', help='Generate UUID for scan operation')
        scan_parser.set_defaults(func=self.execute_scan)

    def execute_scan(self, args: argparse.Namespace) -> int:
        """Execute scan command.

        Args:
            args: Command arguments including injected 'container'
        """
        try:
            # Validation
            if not args.paths:
                print("[ERROR] No paths provided. Please specify at least one directory to scan.")
                return 1
            
            # Check if paths exist
            valid_paths = []
            for path in args.paths:
                if not os.path.exists(path):
                    print(f"[ERROR] Path does not exist: {path}")
                    return 1
                valid_paths.append(path)
            
            print(f"[PLUGIN] Executing scan command: {valid_paths}")
            
            # Generate UUID for scan operation if requested
            scan_uuid = None
            if hasattr(args, 'generate_uuid') and args.generate_uuid:
                from nodupe.core.plugin_system.uuid_utils import UUIDUtils
                scan_uuid = UUIDUtils.generate_uuid_v4()
                print(f"[PLUGIN] Generated scan UUID: {scan_uuid}")
            
            # Initialize audit logger
            audit_logger = get_audit_logger()
            audit_logger.log_scan_started(valid_paths, vars(args))

            # User confirmation for large scan operations
            confirmation_mgr = get_confirmation_manager()
            if not confirmation_mgr.confirm_scan_operation(valid_paths, recursive=True):
                print("[PLUGIN] Scan operation cancelled by user.")
                return 0

            start_time = time.monotonic()

            # 1. Get services
            container = getattr(args, 'container', None)
            if not container:
                print("[ERROR] Dependency container not available")
                return 1

            db_connection = container.get_service('database')
            if not db_connection:
                print("[ERROR] Database service not available")
                return 1

            file_repo = FileRepository(db_connection)

            # Setup filter
            def file_filter(info: Dict[str, Any]) -> bool:
                if hasattr(args, 'min_size') and args.min_size and info.get('size', 0) < args.min_size:
                    return False
                if hasattr(args, 'max_size') and args.max_size and info.get('size', 0) > args.max_size:
                    return False
                if hasattr(args, 'extensions') and args.extensions:
                    ext = info.get('extension', '').lstrip('.')
                    if ext not in args.extensions:
                        return False
                return True

            # Setup progress callback
            def progress_callback(progress: Dict[str, Any]) -> None:
                if hasattr(args, 'verbose') and args.verbose:
                    print(
                        f"\rScanning... {progress['files_processed']} files ({progress['files_per_second']:.1f} f/s)", 
                        end="", flush=True)

            # 3. Process Execution
            walker = FileWalker()
            processor = FileProcessor(walker)

            all_processed_files = []

            for path in valid_paths:
                print(f"[PLUGIN] Scanning directory: {path}")
                
                # Process files
                results = processor.process_files(
                    root_path=path,
                    file_filter=file_filter,
                    on_progress=progress_callback
                )

                if results:
                    print(f"\n[PLUGIN] Found {len(results)} files in {path}")
                    all_processed_files.extend(results)

                    # Log each file processed
                    for result in results:
                        path_obj = Path(result['path'])
                        if path_obj.exists():
                            audit_logger.log_file_processed(
                                path_obj,
                                result.get('size', 0),
                                result.get('hash', '')
                            )

                    # 4. Save to Database
                    print("[PLUGIN] Saving to database...")
                    count = file_repo.batch_add_files(results)
                    print(f"[PLUGIN] Saved {count} records")
                else:
                    print(f"\n[PLUGIN] No files found in {path}")

            # 5. Detect Duplicates (In-Database)
            print("[PLUGIN] Detecting duplicates...")
            
            # Group files by hash to find duplicates
            hash_groups = {}
            for file_info in all_processed_files:
                file_hash = file_info.get('hash')
                if file_hash:
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(file_info)
            
            # Find duplicate groups (groups with more than 1 file)
            duplicate_groups = [group for group in hash_groups.values() if len(group) > 1]
            
            # Update database with duplicate information
            for group in duplicate_groups:
                if len(group) > 1:
                    # Mark first as original, rest as duplicates
                    original_path = group[0]['path']
                    original_file = file_repo.get_file_by_path(original_path)
                    if original_file:
                        # Mark as original (not duplicate)
                        file_repo.update_file(original_file['id'], is_duplicate=False, duplicate_of=None)
                    
                    for dup_info in group[1:]:
                        dup_file = file_repo.get_file_by_path(dup_info['path'])
                        if dup_file:
                            file_repo.mark_as_duplicate(dup_file['id'], original_file['id'])
                            
            print(f"[PLUGIN] Found {len(duplicate_groups)} duplicate groups")
            
            elapsed = time.monotonic() - start_time
            print(f"\n[PLUGIN] Scan complete in {elapsed:.2f}s")
            print(f"[PLUGIN] Total files processed: {len(all_processed_files)}")
            print(f"[PLUGIN] Duplicate groups found: {len(duplicate_groups)}")

            # Log scan completion with UUID if generated
            audit_logger.log_scan_completed(
                files_processed=len(all_processed_files),
                duplicates_found=len(duplicate_groups),
                scan_uuid=str(scan_uuid) if scan_uuid else None
            )

            return 0

        except Exception as e:
            print(f"[PLUGIN ERROR] Scan failed: {e}")
            import traceback
            traceback.print_exc()
            return 1


# Create plugin instance when module is loaded
scan_plugin = ScanPlugin()


def register_plugin():
    """Register plugin with core system."""
    return scan_plugin


# Export plugin interface
__all__ = ['scan_plugin', 'register_plugin']
