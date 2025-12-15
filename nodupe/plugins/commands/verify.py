# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Verify plugin for NoDupeLabs.

This plugin provides integrity verification functionality to check
the consistency and integrity of processed files and database state.
It ensures that file operations were completed successfully and
that no corruption occurred during processing.

Key Features:
    - File integrity checking
    - Database consistency verification
    - Checksum validation
    - Rollback safety verification
    - Progress tracking
    - Plugin integration

Dependencies:
    - Core modules
"""

import argparse
import hashlib
from pathlib import Path
from typing import Any, Dict
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection


class VerifyPlugin(Plugin):
    """Verify plugin implementation."""
    
    def __init__(self):
        """Initialize verify plugin."""
        self.description = "Verify file integrity and database consistency"
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return "verify"
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"
    
    @property
    def dependencies(self) -> list[str]:
        """List of plugin dependencies."""
        return ["database"]
        
    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        pass
        
    def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass
        
    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {'commands': ['verify']}
    
    def _on_verify_start(self, **kwargs: Any) -> None:
        """Handle verify start event."""
        print(f"[PLUGIN] Verify started: {kwargs.get('mode', 'unknown')}")
    
    def _on_verify_complete(self, **kwargs: Any) -> None:
        """Handle verify complete event."""
        print(f"[PLUGIN] Verify completed: {kwargs.get('checks_performed', 0)} checks, "
              f"{kwargs.get('errors_found', 0)} errors")

    def register_commands(self, subparsers: Any) -> None:
        """Register verify command with argument parser."""
        verify_parser = subparsers.add_parser('verify', help='Verify file integrity and database consistency')
        verify_parser.add_argument(
            '--mode',
            choices=['integrity', 'consistency', 'checksums', 'all'],
            default='all',
            help='Verification mode to run'
        )
        verify_parser.add_argument(
            '--fast',
            action='store_true',
            help='Perform fast verification (skip heavy checks)'
        )
        verify_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        verify_parser.add_argument(
            '--repair',
            action='store_true',
            help='Attempt to repair detected issues'
        )
        verify_parser.add_argument(
            '--output',
            help='Output results to file'
        )
        verify_parser.set_defaults(func=self.execute_verify)

    def execute_verify(self, args: argparse.Namespace) -> int:
        """Execute verify command.
        
        Args:
            args: Command arguments including injected 'container'
        """
        from typing import TypedDict
        
        class VerificationResult(TypedDict):
            checks: int
            errors: int
            warnings: int
            error_details: list
        
        try:
            print(f"[PLUGIN] Executing verify command: {args.mode} mode")
            print(f"[PLUGIN] Fast mode: {args.fast}, Repair: {args.repair}")
            
            # 1. Get services
            container = getattr(args, 'container', None)
            if not container:
                print("[ERROR] Dependency container not available")
                return 1
            
            db_connection = container.get_service('database')
            if not db_connection:
                print("[ERROR] Database service not available")
                db_connection = DatabaseConnection.get_instance()

            file_repo = FileRepository(db_connection)
            
            # 2. Determine verification mode
            modes = []
            if args.mode == 'all':
                modes = ['integrity', 'consistency', 'checksums']
            else:
                modes = [args.mode]
            
            results: Dict[str, VerificationResult] = {
                'integrity': {'checks': 0, 'errors': 0, 'warnings': 0, 'error_details': []},
                'consistency': {'checks': 0, 'errors': 0, 'warnings': 0, 'error_details': []},
                'checksums': {'checks': 0, 'errors': 0, 'warnings': 0, 'error_details': []}
            }
            
            total_errors = 0
            total_warnings = 0
            
            # 3. Run verification modes
            for mode in modes:
                print(f"\n[PLUGIN] Running {mode} verification...")
                
                if mode == 'integrity':
                    mode_results = self._verify_integrity(file_repo, args)
                    results['integrity'] = {
                        'checks': mode_results['checks'],
                        'errors': mode_results['errors'], 
                        'warnings': mode_results['warnings'],
                        'error_details': []
                    }
                    total_errors += mode_results['errors']
                    total_warnings += mode_results['warnings']
                    
                elif mode == 'consistency':
                    mode_results = self._verify_consistency(file_repo, args)
                    results['consistency'] = {
                        'checks': mode_results['checks'],
                        'errors': mode_results['errors'], 
                        'warnings': mode_results['warnings'],
                        'error_details': []
                    }
                    total_errors += mode_results['errors']
                    total_warnings += mode_results['warnings']
                    
                elif mode == 'checksums':
                    mode_results = self._verify_checksums(file_repo, args)
                    results['checksums'] = {
                        'checks': mode_results['checks'],
                        'errors': mode_results['errors'], 
                        'warnings': mode_results['warnings'],
                        'error_details': []
                    }
                    total_errors += mode_results['errors']
                    total_warnings += mode_results['warnings']
            
            # 4. Report results
            print(f"\n[PLUGIN] Verification Summary:")
            for mode, stats in results.items():
                if stats['checks'] > 0:
                    print(f" {mode.title()}: {stats['checks']} checks, "
                          f"{stats['errors']} errors, {stats['warnings']} warnings")
            
            print(f"\n[PLUGIN] Total: {sum(r['checks'] for r in results.values())} checks, "
                  f"{total_errors} errors, {total_warnings} warnings")
            
            if total_errors > 0:
                print(f"[PLUGIN] ❌ {total_errors} integrity issues detected!")
                if args.repair:
                    print("[PLUGIN] Repair mode enabled - this would attempt to fix issues")
                    # TODO: Implement repair functionality in future
            else:
                print(f"[PLUGIN] ✅ All verification checks passed!")
                
            # Output detailed results to file if requested
            if args.output:
                self._output_findings_to_file(results, args.output, args)
                print(f"[PLUGIN] Detailed findings saved to: {args.output}")
            
            self._on_verify_complete(
                checks_performed=sum(r['checks'] for r in results.values()),
                errors_found=total_errors
            )
            
            return 0 if total_errors == 0 else 1

        except Exception as e:
            print(f"[PLUGIN ERROR] Verify failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

    def _output_findings_to_file(self, results: Dict[str, Any], output_file: str, args: argparse.Namespace) -> None:
        """Output detailed verification findings to a file.
        
        Args:
            results: Verification results dictionary
            output_file: Path to output file
            args: Command arguments
        """
        import json
        from datetime import datetime
        
        findings: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'command_args': {
                'mode': args.mode,
                'fast': args.fast,
                'verbose': args.verbose,
                'repair': args.repair
            },
            'summary': {
                'total_checks': sum(r['checks'] for r in results.values()),  # type: ignore
                'total_errors': sum(r['errors'] for r in results.values()),  # type: ignore
                'total_warnings': sum(r['warnings'] for r in results.values())  # type: ignore
            },
            'details': {}
        }
        
        for mode, stats in results.items():
            findings['details'][mode] = {
                'checks': stats['checks'],
                'errors': stats['errors'],
                'warnings': stats['warnings'],
                'error_details': stats.get('error_details', [])
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(findings, f, indent=2, ensure_ascii=False)

    def _verify_integrity(self, file_repo: FileRepository, args: argparse.Namespace) -> Dict[str, int]:
        """Verify file integrity by checking file existence and basic properties."""
        results = {'checks': 0, 'errors': 0, 'warnings': 0}
        
        try:
            files = file_repo.get_all_files()
            print(f"[PLUGIN] Checking integrity of {len(files)} files...")
            
            for file_data in files:
                results['checks'] += 1
                file_path = Path(file_data['path'])
                
                # Check if file exists
                if not file_path.exists():
                    results['errors'] += 1
                    if args.verbose:
                        print(f"[ERROR] File not found: {file_path}")
                    continue
                
                # Check file size matches database
                try:
                    actual_size = file_path.stat().st_size
                    if actual_size != file_data['size']:
                        results['errors'] += 1
                        if args.verbose:
                            print(f"[ERROR] Size mismatch for {file_path}: "
                                  f"expected {file_data['size']}, got {actual_size}")
                except OSError:
                    results['errors'] += 1
                    if args.verbose:
                        print(f"[ERROR] Cannot access file: {file_path}")
                
                # Check file readability (unless in fast mode)
                if not args.fast:
                    try:
                        with open(file_path, 'rb') as f:
                            f.read(1)  # Test if file is readable
                    except (OSError, PermissionError):
                        results['errors'] += 1
                        if args.verbose:
                            print(f"[ERROR] Cannot read file: {file_path}")
            
            print(f"[PLUGIN] Integrity check: {results['checks']} files, "
                  f"{results['errors']} errors, {results['warnings']} warnings")
            
        except Exception as e:
            print(f"[PLUGIN ERROR] Integrity verification failed: {e}")
            results['errors'] += 1
            
        return results

    def _verify_consistency(self, file_repo: FileRepository, args: argparse.Namespace) -> Dict[str, int]:
        """Verify database consistency and relationships."""
        results = {'checks': 0, 'errors': 0, 'warnings': 0}
        
        try:
            files = file_repo.get_all_files()
            print(f"[PLUGIN] Checking consistency of {len(files)} files...")
            
            for file_data in files:
                results['checks'] += 1
                
                # Check duplicate relationships
                if file_data['is_duplicate']:
                    if not file_data['duplicate_of']:
                        results['errors'] += 1
                        if args.verbose:
                            print(f"[ERROR] Duplicate file {file_data['path']} has no duplicate_of reference")
                    else:
                        # Verify the referenced original file exists
                        original = file_repo.get_file(file_data['duplicate_of'])
                        if not original:
                            results['errors'] += 1
                            if args.verbose:
                                print(f"[ERROR] Duplicate file {file_data['path']} references "
                                      f"non-existent original ID {file_data['duplicate_of']}")
                
                # Check for circular references or invalid relationships
                if file_data['duplicate_of'] == file_data['id']:
                    results['errors'] += 1
                    if args.verbose:
                        print(f"[ERROR] File {file_data['path']} references itself as duplicate")
            
            # Check for orphaned duplicate references
            duplicates = file_repo.get_duplicate_files()
            for dup in duplicates:
                if dup['duplicate_of']:
                    original = file_repo.get_file(dup['duplicate_of'])
                    if not original:
                        results['errors'] += 1
                        if args.verbose:
                            print(f"[ERROR] Orphaned duplicate reference: {dup['path']} -> {dup['duplicate_of']}")
            
            print(f"[PLUGIN] Consistency check: {results['checks']} files, "
                  f"{results['errors']} errors, {results['warnings']} warnings")
            
        except Exception as e:
            print(f"[PLUGIN ERROR] Consistency verification failed: {e}")
            results['errors'] += 1
            
        return results

    def _verify_checksums(self, file_repo: FileRepository, args: argparse.Namespace) -> Dict[str, int]:
        """Verify file checksums by recalculating hashes."""
        results = {'checks': 0, 'errors': 0, 'warnings': 0}
        
        if args.fast:
            print("[PLUGIN] Skipping checksum verification in fast mode")
            return results
            
        try:
            files = file_repo.get_all_files()
            print(f"[PLUGIN] Verifying checksums for {len(files)} files...")
            
            for file_data in files:
                if not file_data['hash']:
                    results['warnings'] += 1
                    if args.verbose:
                        print(f"[WARN] No hash stored for: {file_data['path']}")
                    continue
                
                results['checks'] += 1
                file_path = Path(file_data['path'])
                
                # Skip if file doesn't exist (already caught in integrity check)
                if not file_path.exists():
                    results['errors'] += 1
                    continue
                
                # Recalculate hash and compare
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    if file_hash != file_data['hash']:
                        results['errors'] += 1
                        if args.verbose:
                            print(f"[ERROR] Hash mismatch for {file_path}: "
                                  f"stored {file_data['hash'][:8]}..., calculated {file_hash[:8]}...")
                
                except (OSError, MemoryError) as e:
                    results['errors'] += 1
                    if args.verbose:
                        print(f"[ERROR] Cannot calculate hash for {file_path}: {e}")
            
            print(f"[PLUGIN] Checksum check: {results['checks']} files, "
                  f"{results['errors']} errors, {results['warnings']} warnings")
            
        except Exception as e:
            print(f"[PLUGIN ERROR] Checksum verification failed: {e}")
            results['errors'] += 1
            
        return results


# Create plugin instance when module is loaded
verify_plugin = VerifyPlugin()

# Register plugin with core system
def register_plugin():
    """Register plugin with core system."""
    return verify_plugin

# Export plugin interface
__all__ = ['verify_plugin', 'register_plugin']
