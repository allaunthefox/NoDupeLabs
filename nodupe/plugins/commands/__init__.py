"""NoDupeLabs Commands Plugins - CLI Command Implementations

This module provides command implementations for the NoDupeLabs CLI
with proper argument validation, error handling, and result formatting.
"""

from typing import List, Optional, Dict, Any, Tuple
import argparse
import logging
import json
import csv
import os
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[Exception] = None

class Command(ABC):
    """Abstract base class for commands"""

    @abstractmethod
    def get_name(self) -> str:
        """Get command name"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get command description"""
        pass

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command arguments to parser"""
        pass

    @abstractmethod
    def validate_args(self, args: argparse.Namespace) -> CommandResult:
        """Validate command arguments"""
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> CommandResult:
        """Execute command"""
        pass

class ScanCommand(Command):
    """Scan directories for duplicates"""

    def get_name(self) -> str:
        return "scan"

    def get_description(self) -> str:
        return "Scan directories for duplicate files"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add scan command arguments"""
        parser.add_argument('paths', nargs='+', help='Directories to scan')
        parser.add_argument('--min-size', type=int, default=1024,
                          help='Minimum file size in bytes')
        parser.add_argument('--max-size', type=int, default=100*1024*1024,
                          help='Maximum file size in bytes')
        parser.add_argument('--extensions', nargs='+',
                          help='File extensions to include')
        parser.add_argument('--exclude', nargs='+',
                          help='Directories to exclude')
        parser.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose output')
        parser.add_argument('--output', choices=['text', 'json', 'csv'],
                          default='text', help='Output format')

    def validate_args(self, args: argparse.Namespace) -> CommandResult:
        """Validate scan command arguments"""
        try:
            # Check that paths exist
            for path in args.paths:
                if not os.path.exists(path):
                    return CommandResult(
                        success=False,
                        message=f"Path does not exist: {path}"
                    )

            # Check size constraints
            if args.min_size < 0:
                return CommandResult(
                    success=False,
                    message="Minimum size cannot be negative"
                )

            if args.max_size < args.min_size:
                return CommandResult(
                    success=False,
                    message="Maximum size cannot be less than minimum size"
                )

            return CommandResult(
                success=True,
                message="Arguments are valid"
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message="Argument validation failed",
                error=e
            )

    def execute(self, args: argparse.Namespace) -> CommandResult:
        """Execute scan command"""
        try:
            from nodupe.scan.walker import FileWalker
            from nodupe.scan.processor import FileProcessor
            from nodupe.scan.hasher import FileHasher

            # Initialize scanner components
            walker = FileWalker()
            processor = FileProcessor()
            hasher = FileHasher()

            # Configure scanner
            scan_config = {
                'min_size': args.min_size,
                'max_size': args.max_size,
                'extensions': args.extensions or ['jpg', 'png', 'pdf', 'docx', 'txt'],
                'exclude_dirs': args.exclude or ['.git', '.venv', 'node_modules'],
                'verbose': args.verbose
            }

            # Scan files
            all_files = []
            for path in args.paths:
                files = walker.walk_directory(path, **scan_config)
                all_files.extend(files)

            if args.verbose:
                logger.info(f"Found {len(all_files)} files to process")

            # Process files and find duplicates
            duplicates = processor.find_duplicates(all_files)

            # Format output
            if args.output == 'json':
                output = json.dumps(duplicates, indent=2)
            elif args.output == 'csv':
                if duplicates:
                    fieldnames = duplicates[0].keys()
                    output = self._duplicates_to_csv(duplicates, fieldnames)
                else:
                    output = "No duplicates found"
            else:  # text
                output = self._format_text_output(duplicates)

            return CommandResult(
                success=True,
                message=f"Scan completed. Found {len(duplicates)} duplicate groups.",
                data=output
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message="Scan failed",
                error=e
            )

    def _duplicates_to_csv(self, duplicates: List[Dict], fieldnames: List[str]) -> str:
        """Convert duplicates to CSV format"""
        output = []
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(duplicates)
        return ''.join(output)

    def _format_text_output(self, duplicates: List[Dict]) -> str:
        """Format duplicates as text output"""
        if not duplicates:
            return "No duplicates found"

        output = []
        for i, dup_group in enumerate(duplicates, 1):
            output.append(f"Duplicate Group {i}:")
            for file_info in dup_group.get('files', []):
                output.append(f"  {file_info.get('path', 'Unknown')}")
                output.append(f"    Size: {file_info.get('size', 0)} bytes")
                output.append(f"    Hash: {file_info.get('hash', 'Unknown')}")
            output.append("")  # Blank line between groups

        return '\n'.join(output)

class ApplyCommand(Command):
    """Apply actions to duplicates"""

    def get_name(self) -> str:
        return "apply"

    def get_description(self) -> str:
        return "Apply actions to duplicate files"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add apply command arguments"""
        parser.add_argument('action', choices=['delete', 'move', 'copy', 'symlink', 'list'],
                          help='Action to apply')
        parser.add_argument('--input', required=True,
                          help='Input file (JSON or CSV from scan command)')
        parser.add_argument('--target-dir',
                          help='Target directory for move/copy/symlink actions')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be done without actually doing it')
        parser.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose output')

    def validate_args(self, args: argparse.Namespace) -> CommandResult:
        """Validate apply command arguments"""
        try:
            # Check input file exists
            if not os.path.exists(args.input):
                return CommandResult(
                    success=False,
                    message=f"Input file not found: {args.input}"
                )

            # Check target directory for relevant actions
            if args.action in ['move', 'copy', 'symlink'] and not args.target_dir:
                return CommandResult(
                    success=False,
                    message=f"Target directory required for {args.action} action"
                )

            if args.target_dir and not os.path.exists(args.target_dir):
                return CommandResult(
                    success=False,
                    message=f"Target directory does not exist: {args.target_dir}"
                )

            return CommandResult(
                success=True,
                message="Arguments are valid"
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message="Argument validation failed",
                error=e
            )

    def execute(self, args: argparse.Namespace) -> CommandResult:
        """Execute apply command"""
        try:
            # Load duplicates from input file
            duplicates = self._load_duplicates(args.input)
            if not duplicates:
                return CommandResult(
                    success=False,
                    message="No duplicates found in input file"
                )

            # Apply action
            results = []
            for dup_group in duplicates:
                group_results = self._apply_action_to_group(dup_group, args)
                results.extend(group_results)

            # Format output
            output = self._format_apply_results(results, args)

            return CommandResult(
                success=True,
                message=f"Applied {args.action} to {len(results)} files",
                data=output
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message="Apply failed",
                error=e
            )

    def _load_duplicates(self, input_file: str) -> List[Dict]:
        """Load duplicates from input file"""
        try:
            if input_file.endswith('.json'):
                with open(input_file, 'r') as f:
                    return json.load(f)
            elif input_file.endswith('.csv'):
                with open(input_file, 'r') as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            else:
                logger.warning(f"Unknown file format: {input_file}")
                return []
        except Exception as e:
            logger.error(f"Error loading duplicates: {e}")
            return []

    def _apply_action_to_group(self, dup_group: Dict, args: argparse.Namespace) -> List[Dict]:
        """Apply action to a duplicate group"""
        results = []
        files = dup_group.get('files', [])

        # Keep the first file, apply action to others
        for file_info in files[1:]:  # Skip first file (keep it)
            result = {
                'original_path': file_info.get('path'),
                'action': args.action,
                'success': False,
                'message': ''
            }

            if args.dry_run:
                result['message'] = f"Would {args.action} {file_info.get('path')}"
                result['success'] = True
                results.append(result)
                continue

            try:
                if args.action == 'delete':
                    os.remove(file_info.get('path'))
                    result['message'] = f"Deleted {file_info.get('path')}"
                    result['success'] = True

                elif args.action == 'move':
                    target_path = os.path.join(args.target_dir, os.path.basename(file_info.get('path')))
                    os.rename(file_info.get('path'), target_path)
                    result['message'] = f"Moved {file_info.get('path')} to {target_path}"
                    result['success'] = True

                elif args.action == 'copy':
                    target_path = os.path.join(args.target_dir, os.path.basename(file_info.get('path')))
                    import shutil
                    shutil.copy2(file_info.get('path'), target_path)
                    result['message'] = f"Copied {file_info.get('path')} to {target_path}"
                    result['success'] = True

                elif args.action == 'symlink':
                    target_path = os.path.join(args.target_dir, os.path.basename(file_info.get('path')))
                    os.symlink(file_info.get('path'), target_path)
                    result['message'] = f"Created symlink from {file_info.get('path')} to {target_path}"
                    result['success'] = True

                elif args.action == 'list':
                    result['message'] = f"Would {args.action} {file_info.get('path')}"
                    result['success'] = True

            except Exception as e:
                result['message'] = f"Failed to {args.action} {file_info.get('path')}: {e}"
                result['success'] = False

            results.append(result)

        return results

    def _format_apply_results(self, results: List[Dict], args: argparse.Namespace) -> str:
        """Format apply results"""
        output = []
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)

        output.append(f"Action: {args.action}")
        output.append(f"Files processed: {total_count}")
        output.append(f"Successful: {success_count}")
        output.append(f"Failed: {total_count - success_count}")
        output.append("")

        if args.verbose:
            for result in results:
                status = "✓" if result['success'] else "✗"
                output.append(f"{status} {result['message']}")

        return '\n'.join(output)

class SimilarityCommand(Command):
    """Find similar files using similarity search"""

    def get_name(self) -> str:
        return "similarity"

    def get_description(self) -> str:
        return "Find similar files using vector similarity search"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add similarity command arguments"""
        parser.add_argument('query_file', help='Query file to find similar files for')
        parser.add_argument('--database', help='Database file containing file vectors')
        parser.add_argument('--k', type=int, default=5,
                          help='Number of similar files to return')
        parser.add_argument('--threshold', type=float, default=0.8,
                          help='Similarity threshold (0-1)')
        parser.add_argument('--backend', choices=['brute_force', 'faiss', 'annoy'],
                          default='brute_force', help='Similarity backend')
        parser.add_argument('--output', choices=['text', 'json', 'csv'],
                          default='text', help='Output format')
        parser.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose output')

    def validate_args(self, args: argparse.Namespace) -> CommandResult:
        """Validate similarity command arguments"""
        try:
            # Check query file exists
            if not os.path.exists(args.query_file):
                return CommandResult(
                    success=False,
                    message=f"Query file not found: {args.query_file}"
                )

            # Check threshold is valid
            if not (0 <= args.threshold <= 1):
                return CommandResult(
                    success=False,
                    message="Threshold must be between 0 and 1"
                )

            # Check k is positive
            if args.k <= 0:
                return CommandResult(
                    success=False,
                    message="k must be positive"
                )

            return CommandResult(
                success=True,
                message="Arguments are valid"
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message="Argument validation failed",
                error=e
            )

    def execute(self, args: argparse.Namespace) -> CommandResult:
        """Execute similarity command"""
        try:
            from nodupe.similarity import create_brute_force_backend, create_similarity_manager

            # Initialize similarity backend
            if args.backend == 'brute_force':
                backend = create_brute_force_backend(dimensions=128)
            else:
                # For other backends, we'd need to implement them
                logger.warning(f"Backend {args.backend} not implemented, using brute_force")
                backend = create_brute_force_backend(dimensions=128)

            manager = create_similarity_manager()
            manager.add_backend('default', backend)
            manager.set_backend('default')

            # Load or create database
            if args.database and os.path.exists(args.database):
                # Load existing database
                backend.load_index(args.database)
                logger.info(f"Loaded similarity database from {args.database}")
            else:
                logger.warning("No existing database found, similarity search may not work well")
                # In a real implementation, we'd scan files and build the database

            # Generate query vector (placeholder - real implementation would use ML)
            query_vector = self._generate_query_vector(args.query_file)

            # Perform similarity search
            results = backend.search(query_vector, k=args.k, threshold=args.threshold)

            # Format output
            output = self._format_similarity_results(results, args)

            return CommandResult(
                success=True,
                message=f"Found {len(results)} similar files",
                data=output
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message="Similarity search failed",
                error=e
            )

    def _generate_query_vector(self, file_path: str) -> List[float]:
        """Generate a query vector for the given file (placeholder)"""
        # In a real implementation, this would use ML to generate embeddings
        # For now, we'll generate a random vector based on file properties
        import hashlib

        # Get file properties
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        # Create a simple hash-based vector
        combined = f"{file_name}:{file_size}"
        hash_obj = hashlib.md5(combined.encode())
        hash_hex = hash_obj.hexdigest()

        # Convert hash to numerical vector
        vector = []
        for i in range(0, len(hash_hex), 2):
            byte_val = int(hash_hex[i:i+2], 16) / 255.0
            vector.append(byte_val)

        # Pad or truncate to 128 dimensions
        return vector[:128] + [0.0] * max(0, 128 - len(vector))

    def _format_similarity_results(self, results: List[Tuple[Dict, float]], args: argparse.Namespace) -> str:
        """Format similarity results"""
        if args.output == 'json':
            formatted = []
            for metadata, score in results:
                formatted.append({
                    'path': metadata.get('path', 'Unknown'),
                    'score': score,
                    'size': metadata.get('size', 0),
                    'type': metadata.get('type', 'Unknown')
                })
            return json.dumps(formatted, indent=2)

        elif args.output == 'csv':
            output = []
            writer = csv.writer(output)
            writer.writerow(['Path', 'Score', 'Size', 'Type'])
            for metadata, score in results:
                writer.writerow([
                    metadata.get('path', 'Unknown'),
                    score,
                    metadata.get('size', 0),
                    metadata.get('type', 'Unknown')
                ])
            return ''.join(output)

        else:  # text
            output = []
            output.append(f"Similar files to {args.query_file}:")
            output.append("")

            for i, (metadata, score) in enumerate(results, 1):
                output.append(f"{i}. {metadata.get('path', 'Unknown')} (Score: {score:.3f})")
                output.append(f"   Size: {metadata.get('size', 0)} bytes")
                output.append(f"   Type: {metadata.get('type', 'Unknown')}")
                output.append("")

            return '\n'.join(output)

class CommandManager:
    """Manage available commands"""

    def __init__(self):
        self.commands = {}
        self._register_commands()

    def _register_commands(self):
        """Register all available commands"""
        commands = [
            ScanCommand(),
            ApplyCommand(),
            SimilarityCommand()
        ]

        for cmd in commands:
            self.commands[cmd.get_name()] = cmd
            logger.info(f"Registered command: {cmd.get_name()}")

    def get_command(self, name: str) -> Optional[Command]:
        """Get command by name"""
        return self.commands.get(name)

    def list_commands(self) -> List[str]:
        """List all available commands"""
        return list(self.commands.keys())

    def execute_command(self, name: str, args: argparse.Namespace) -> CommandResult:
        """Execute command by name"""
        cmd = self.get_command(name)
        if not cmd:
            return CommandResult(
                success=False,
                message=f"Command not found: {name}"
            )

        # Validate arguments
        validation_result = cmd.validate_args(args)
        if not validation_result.success:
            return validation_result

        # Execute command
        return cmd.execute(args)

# Module-level command manager
COMMAND_MANAGER: Optional[CommandManager] = None

def get_command_manager() -> CommandManager:
    """Get the global command manager"""
    global COMMAND_MANAGER
    if COMMAND_MANAGER is None:
        COMMAND_MANAGER = CommandManager()
    return COMMAND_MANAGER

# Initialize manager on import
get_command_manager()

__all__ = [
    'Command', 'CommandResult', 'ScanCommand', 'ApplyCommand',
    'SimilarityCommand', 'CommandManager', 'get_command_manager'
]
