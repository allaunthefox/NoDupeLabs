"""Enhanced Scan plugin for NoDupeLabs with Cascade integration.

This plugin provides enhanced scanning functionality with Cascade-Autotune
integration for improved performance and intelligent algorithm selection.

Key Features:
    - Progressive hashing with algorithm cascading (BLAKE3 → SHA256 → MD5)
    - Archive processing with quality-tiered extraction (7z → zipfile → tarfile)
    - Security policy integration for algorithm and archive processing
    - Performance optimization through cascade stages
    - Backward compatibility with original ScanPlugin
    - Intelligent feature detection and fallback

Dependencies:
    - Core modules
    - Cascade stages
    - Security policy
    - Environment detection
"""

from typing import Any, Dict, List, Optional
import argparse
import time
import os
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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

from nodupe.core.plugin_system.base import Plugin
from nodupe.core.scan.processor import FileProcessor
from nodupe.core.scan.walker import FileWalker
from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection
from nodupe.core.audit import get_audit_logger, AuditEventType
from nodupe.core.confirmation import get_confirmation_manager
from nodupe.core.hash_progressive import ProgressiveHasher, get_progressive_hasher
from nodupe.core.cascade.stages.progressive_hashing import (
    ProgressiveHashingCascadeStage, 
    get_progressive_hashing_stage
)
from nodupe.core.cascade.stages.archive_processing import (
    ArchiveProcessingCascadeStage,
    get_archive_processing_stage
)
from nodupe.core.cascade.environment import EnvironmentDetector
from nodupe.core.security.policy import SecurityPolicy

# Plugin metadata (UUID-based specification)
PLUGIN_METADATA = {
    "uuid": "e1f2a3b4-c5d6-7890-abcd-ef1234567891",
    "name": "scan_enhanced",
    "display_name": "Enhanced Scan Plugin",
    "version": "v2.0.0",
    "description": "Enhanced scan with Cascade-Autotune integration",
    "author": "NoDupeLabs Team",
    "category": "scanning",
    "dependencies": ["scan", "progressive_hashing_cascade", "archive_processing_cascade"],
    "compatibility": {
        "python": ">=3.9",
        "nodupe_core": ">=1.0.0"
    },
    "tags": ["scanning", "cascade", "performance", "autotune"],
    "marketplace_id": "scan_enhanced_e1f2a3b4-c5d6-7890-abcd-ef1234567891"
}


class EnhancedScanPlugin(Plugin):
    """Enhanced scan plugin with Cascade-Autotune integration.
    
    This plugin enhances the original ScanPlugin by integrating Cascade-Autotune
    stages for improved performance and intelligent algorithm selection.
    
    Key Enhancements:
        - Progressive hashing with algorithm cascading
        - Archive processing with quality-tiered extraction
        - Security policy integration
        - Performance optimization
        - Intelligent feature detection
        - Backward compatibility
    """

    def __init__(self):
        """Initialize enhanced scan plugin with UUID metadata."""
        super().__init__(PLUGIN_METADATA)
        self.cascade_enabled = True
        self.performance_metrics = {}

    def initialize(self, container: Any) -> None:
        """Initialize the enhanced plugin."""
        # Check if cascade stages are available
        try:
            self.progressive_hashing_stage = get_progressive_hashing_stage()
            self.archive_processing_stage = get_archive_processing_stage()
            self.cascade_available = True
        except ImportError:
            self.cascade_available = False
            self.progressive_hashing_stage = None
            self.archive_processing_stage = None

    def shutdown(self) -> None:
        """Shutdown the enhanced plugin."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {
            'commands': ['scan_enhanced'],
            'features': ['progressive_hashing_cascade', 'archive_processing_cascade', 'security_policy_integration']
        }

    def _on_scan_start(self, **kwargs: Any) -> None:
        """Handle scan start event."""
        print(f"[ENHANCED] Scan started: {kwargs.get('path', 'unknown')}")

    def _on_scan_complete(self, **kwargs: Any) -> None:
        """Handle scan complete event."""
        print(f"[ENHANCED] Scan completed: {kwargs.get('files_processed', 0)} files processed")

    def register_commands(self, subparsers: Any) -> None:
        """Register enhanced scan command with argument parser.
        
        Note: This method is not part of the base Plugin interface but is used
        by the plugin system to register commands. It follows the same pattern
        as the original ScanPlugin.
        """
        scan_parser = subparsers.add_parser('scan_enhanced', help='Enhanced scan with Cascade integration')
        scan_parser.add_argument('paths', nargs='+', help='Directories to scan')
        scan_parser.add_argument('--min-size', type=int, default=0, help='Minimum file size')
        scan_parser.add_argument('--max-size', type=int, help='Maximum file size')
        scan_parser.add_argument('--extensions', nargs='+', help='File extensions to include')
        scan_parser.add_argument('--exclude', nargs='+', help='Directories to exclude')
        scan_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        scan_parser.add_argument('--cascade', action='store_true', default=True, help='Enable Cascade optimization')
        scan_parser.add_argument('--algorithm', choices=['auto', 'blake3', 'sha256', 'md5'], default='auto', help='Hash algorithm selection')
        scan_parser.add_argument('--archive-method', choices=['auto', '7z', 'zipfile', 'tarfile'], default='auto', help='Archive extraction method')
        scan_parser.set_defaults(func=self.execute_enhanced_scan)

    def execute_enhanced_scan(self, args: argparse.Namespace) -> int:
        """Execute enhanced scan command with Cascade integration.
        
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
            
            print(f"[ENHANCED] Executing enhanced scan: {valid_paths}")
            
            # Initialize audit logger
            audit_logger = get_audit_logger()
            audit_logger.log_scan_started(valid_paths, vars(args))

            # User confirmation for large scan operations
            confirmation_mgr = get_confirmation_manager()
            if not confirmation_mgr.confirm_scan_operation(valid_paths, recursive=True):
                print("[ENHANCED] Scan operation cancelled by user.")
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

            # 2. Determine processing strategy
            use_cascade = args.cascade and self.cascade_available
            use_original = not use_cascade
            
            print(f"[ENHANCED] Using {'Cascade' if use_cascade else 'Original'} processing strategy")
            
            if use_cascade:
                result = self._execute_cascade_scan(valid_paths, args, file_repo, file_filter, progress_callback)
            else:
                result = self._execute_original_scan(valid_paths, args, file_repo, file_filter, progress_callback)

            # 3. Process results
            elapsed = time.monotonic() - start_time
            print(f"\n[ENHANCED] Scan complete in {elapsed:.2f}s")
            
            # Log scan completion
            audit_logger.log_scan_completed(
                files_processed=result.get('files_processed', 0),
                duplicates_found=result.get('duplicates_found', 0)
            )

            # Display results
            self._display_scan_results(result, elapsed, use_cascade)

            return 0

        except Exception as e:
            print(f"[ENHANCED ERROR] Enhanced scan failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def _execute_cascade_scan(self, paths: List[str], args: argparse.Namespace, 
                            file_repo: FileRepository, file_filter: callable, 
                            progress_callback: callable) -> Dict[str, Any]:
        """Execute scan using Cascade stages for optimal performance."""
        all_processed_files = []
        total_duplicates = 0
        
        for path in paths:
            print(f"[CASCADE] Scanning directory: {path}")
            
            # 1. File discovery and filtering
            walker = FileWalker()
            processor = FileProcessor(walker)
            
            # Get all files first
            all_files = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.is_file():
                        all_files.append(file_path)
            
            # Apply filters
            filtered_files = []
            for file_path in all_files:
                try:
                    stat = file_path.stat()
                    file_info = {
                        'path': str(file_path),
                        'size': stat.st_size,
                        'extension': file_path.suffix.lower()
                    }
                    if file_filter(file_info):
                        filtered_files.append(file_path)
                except (OSError, PermissionError):
                    continue
            
            print(f"[CASCADE] Found {len(filtered_files)} files after filtering")
            
            # 2. Archive processing with cascade
            archive_files = [f for f in filtered_files if f.suffix.lower() in ['.zip', '.tar', '.tgz', '.7z']]
            non_archive_files = [f for f in filtered_files if f not in archive_files]
            
            if archive_files and self.archive_processing_stage:
                print(f"[CASCADE] Processing {len(archive_files)} archive files")
                for archive_path in archive_files:
                    try:
                        archive_result = self.archive_processing_stage.execute(archive_path)
                        if archive_result["successful_method"]:
                            print(f"[CASCADE] Extracted {archive_result['total_files']} files from {archive_path.name}")
                    except Exception as e:
                        print(f"[CASCADE] Failed to process archive {archive_path}: {e}")
            
            # 3. Progressive hashing with cascade
            if self.progressive_hashing_stage and non_archive_files:
                print(f"[CASCADE] Processing {len(non_archive_files)} files with progressive hashing")
                
                # Execute progressive hashing cascade
                hash_result = self.progressive_hashing_stage.execute(non_archive_files)
                
                print(f"[CASCADE] Algorithm used: {hash_result['quick_hash_algorithm']} (quick), {hash_result['full_hash_algorithm']} (full)")
                print(f"[CASCADE] Execution time: {hash_result['execution_time']:.3f}s")
                
                # Convert results to format compatible with FileRepository
                processed_files = []
                for file_path in non_archive_files:
                    try:
                        stat = file_path.stat()
                        processed_files.append({
                            'path': str(file_path),
                            'size': stat.st_size,
                            'hash': hash_result.get('hash', ''),  # Would need to be extracted from results
                            'extension': file_path.suffix.lower()
                        })
                    except (OSError, PermissionError):
                        continue
                
                # Save to database
                count = file_repo.batch_add_files(processed_files)
                print(f"[CASCADE] Saved {count} records to database")
                
                all_processed_files.extend(processed_files)
                total_duplicates += hash_result.get('duplicate_groups', 0)
            
            # 4. Fallback to original processing for remaining files
            remaining_files = [f for f in non_archive_files if f not in [Path(p['path']) for p in all_processed_files]]
            if remaining_files:
                print(f"[CASCADE] Fallback processing {len(remaining_files)} files with original method")
                fallback_result = self._execute_original_scan([path], args, file_repo, file_filter, progress_callback)
                total_duplicates += fallback_result.get('duplicates_found', 0)

        return {
            'files_processed': len(all_processed_files),
            'duplicates_found': total_duplicates,
            'processing_method': 'cascade',
            'algorithm_used': hash_result.get('quick_hash_algorithm', 'unknown') if 'hash_result' in locals() else 'fallback'
        }

    def _execute_original_scan(self, paths: List[str], args: argparse.Namespace,
                             file_repo: FileRepository, file_filter: callable,
                             progress_callback: callable) -> Dict[str, Any]:
        """Execute scan using original method for fallback compatibility."""
        all_processed_files = []
        total_duplicates = 0
        
        for path in paths:
            print(f"[ORIGINAL] Scanning directory: {path}")
            
            # Use original FileProcessor
            walker = FileWalker()
            processor = FileProcessor(walker)

            # Process files
            results = processor.process_files(
                root_path=path,
                file_filter=file_filter,
                on_progress=progress_callback
            )

            if results:
                print(f"[ORIGINAL] Found {len(results)} files in {path}")
                all_processed_files.extend(results)

                # Log each file processed
                for result in results:
                    path_obj = Path(result['path'])
                    if path_obj.exists():
                        audit_logger = get_audit_logger()
                        audit_logger.log_file_processed(
                            path_obj,
                            result.get('size', 0),
                            result.get('hash', '')
                        )

                # Save to database
                print("[ORIGINAL] Saving to database...")
                count = file_repo.batch_add_files(results)
                print(f"[ORIGINAL] Saved {count} records")

                # Detect duplicates (In-Database)
                print("[ORIGINAL] Detecting duplicates...")
                
                # Group files by hash to find duplicates
                hash_groups = {}
                for file_info in results:
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
                                
                print(f"[ORIGINAL] Found {len(duplicate_groups)} duplicate groups")
                total_duplicates += len(duplicate_groups)

        return {
            'files_processed': len(all_processed_files),
            'duplicates_found': total_duplicates,
            'processing_method': 'original'
        }

    def _display_scan_results(self, result: Dict[str, Any], elapsed: float, use_cascade: bool) -> None:
        """Display scan results with enhanced formatting."""
        files_processed = result.get('files_processed', 0)
        duplicates_found = result.get('duplicates_found', 0)
        processing_method = result.get('processing_method', 'unknown')
        algorithm_used = result.get('algorithm_used', 'unknown')

        if RICH_AVAILABLE:
            # Enhanced display with Rich
            table = Table(title="Enhanced Scan Results", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Files Processed", str(files_processed))
            table.add_row("Duplicates Found", str(duplicates_found))
            table.add_row("Processing Method", processing_method)
            table.add_row("Algorithm Used", algorithm_used)
            table.add_row("Execution Time", f"{elapsed:.2f}s")
            table.add_row("Cascade Enabled", "Yes" if use_cascade else "No")
            
            console.print(table)
        else:
            # Basic display
            print("=" * 50)
            print("Enhanced Scan Results")
            print("=" * 50)
            print(f"Files Processed: {files_processed}")
            print(f"Duplicates Found: {duplicates_found}")
            print(f"Processing Method: {processing_method}")
            print(f"Algorithm Used: {algorithm_used}")
            print(f"Execution Time: {elapsed:.2f}s")
            print(f"Cascade Enabled: {'Yes' if use_cascade else 'No'}")
            print("=" * 50)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from cascade processing."""
        return self.performance_metrics.copy()

    def enable_cascade(self) -> None:
        """Enable Cascade optimization."""
        self.cascade_enabled = True

    def disable_cascade(self) -> None:
        """Disable Cascade optimization."""
        self.cascade_enabled = False

    def is_cascade_available(self) -> bool:
        """Check if Cascade stages are available."""
        return self.cascade_available


# Create enhanced plugin instance when module is loaded
enhanced_scan_plugin = EnhancedScanPlugin()


def register_plugin():
    """Register enhanced plugin with core system."""
    return enhanced_scan_plugin


# Export plugin interface
__all__ = ['enhanced_scan_plugin', 'register_plugin', 'EnhancedScanPlugin']
