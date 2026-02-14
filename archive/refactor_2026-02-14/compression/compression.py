"""Compression Module.

File compression utilities using standard library only.

Key Features:
    - Multiple compression formats (gzip, bz2, lzma)
    - Compression level control
    - Stream compression for large files
    - Archive creation and extraction
    - Standard library only (no external dependencies)

Dependencies:
    - gzip (standard library)
    - bz2 (standard library)
    - lzma (standard library)
    - tarfile (standard library)
    - zipfile (standard library)
"""

import gzip
import bz2
import lzma
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, List, Literal


class CompressionError(Exception):
    """Compression operation error"""


CompressionFormat = Literal['gzip', 'bz2', 'lzma', 'zip', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz']


class Compression:
    """Handle file compression operations.

    Provides compression and decompression using standard library
    compression algorithms with support for multiple formats.
    """

    @staticmethod
    def compress_data(
        data: bytes,
        format: CompressionFormat = 'gzip',
        level: int = 6
    ) -> bytes:
        """Compress data using specified format.

        Args:
            data: Data to compress
            format: Compression format (gzip, bz2, lzma)
            level: Compression level (1-9, 9=best compression)

        Returns:
            Compressed data

        Raises:
            CompressionError: If compression fails
        """
        try:
            if format == 'gzip':
                return gzip.compress(data, compresslevel=level)
            elif format == 'bz2':
                return bz2.compress(data, compresslevel=level)
            elif format == 'lzma':
                # LZMA doesn't use standard level parameter
                return lzma.compress(data, preset=level)
            else:
                raise CompressionError(
                    f"Unsupported compression format: {format}. "
                    "Use 'gzip', 'bz2', or 'lzma' for data compression."
                )

        except Exception as e:
            if isinstance(e, CompressionError):
                raise
            raise CompressionError(f"Compression failed: {e}") from e

    @staticmethod
    def decompress_data(
        data: bytes,
        format: CompressionFormat = 'gzip'
    ) -> bytes:
        """Decompress data using specified format.

        Args:
            data: Compressed data
            format: Compression format (gzip, bz2, lzma)

        Returns:
            Decompressed data

        Raises:
            CompressionError: If decompression fails
        """
        try:
            if format == 'gzip':
                return gzip.decompress(data)
            elif format == 'bz2':
                return bz2.decompress(data)
            elif format == 'lzma':
                return lzma.decompress(data)
            else:
                raise CompressionError(
                    f"Unsupported compression format: {format}. "
                    "Use 'gzip', 'bz2', or 'lzma' for data decompression."
                )

        except Exception as e:
            if isinstance(e, CompressionError):
                raise
            raise CompressionError(f"Decompression failed: {e}") from e

    @staticmethod
    def compress_file(
        input_path: Path,
        output_path: Optional[Path] = None,
        format: CompressionFormat = 'gzip',
        level: int = 6,
        remove_original: bool = False
    ) -> Path:
        """Compress a file.

        Args:
            input_path: Path to file to compress
            output_path: Output path (None = auto-generate)
            format: Compression format
            level: Compression level (1-9)
            remove_original: Remove original file after compression

        Returns:
            Path to compressed file

        Raises:
            CompressionError: If compression fails
        """
        try:
            # Convert to Path objects
            if isinstance(input_path, str):
                input_path = Path(input_path)

            # Check input exists
            if not input_path.exists():
                raise CompressionError(f"Input file does not exist: {input_path}")

            # Generate output path if not provided
            if output_path is None:
                extensions = {
                    'gzip': '.gz',
                    'bz2': '.bz2',
                    'lzma': '.xz',
                    'zip': '.zip',
                }
                ext = extensions.get(format, f'.{format}')
                output_path = input_path.with_suffix(input_path.suffix + ext)
            elif isinstance(output_path, str):
                output_path = Path(output_path)

            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Read input file
            with open(input_path, 'rb') as f:
                data = f.read()

            # Compress based on format
            if format in ('gzip', 'bz2', 'lzma'):
                compressed = Compression.compress_data(data, format, level)
                with open(output_path, 'wb') as f:
                    f.write(compressed)
            elif format == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(input_path, arcname=input_path.name)
            else:
                raise CompressionError(f"Unsupported format for file compression: {format}")

            # Remove original if requested
            if remove_original:
                input_path.unlink()

            return output_path

        except Exception as e:
            if isinstance(e, CompressionError):
                raise
            raise CompressionError(f"File compression failed: {e}") from e

    @staticmethod
    def decompress_file(
        input_path: Path,
        output_path: Optional[Path] = None,
        format: Optional[CompressionFormat] = None,
        remove_compressed: bool = False
    ) -> Path:
        """Decompress a file.

        Args:
            input_path: Path to compressed file
            output_path: Output path (None = auto-generate)
            format: Compression format (None = auto-detect from extension)
            remove_compressed: Remove compressed file after decompression

        Returns:
            Path to decompressed file

        Raises:
            CompressionError: If decompression fails
        """
        try:
            # Convert to Path objects
            if isinstance(input_path, str):
                input_path = Path(input_path)

            # Check input exists
            if not input_path.exists():
                raise CompressionError(f"Input file does not exist: {input_path}")

            # Auto-detect format if not provided
            if format is None:
                suffix = input_path.suffix.lower()
                format_map = {
                    '.gz': 'gzip',
                    '.bz2': 'bz2',
                    '.xz': 'lzma',
                    '.zip': 'zip',
                }
                format = format_map.get(suffix)
                if format is None:
                    raise CompressionError(f"Cannot auto-detect format for: {suffix}")

            # Generate output path if not provided
            if output_path is None:
                # Remove compression extension
                if input_path.suffix in ('.gz', '.bz2', '.xz'):
                    output_path = input_path.with_suffix('')
                else:
                    output_path = input_path.with_suffix('.decompressed')
            elif isinstance(output_path, str):
                output_path = Path(output_path)

            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Decompress based on format
            if format in ('gzip', 'bz2', 'lzma'):
                with open(input_path, 'rb') as f:
                    compressed = f.read()

                decompressed = Compression.decompress_data(compressed, format)

                with open(output_path, 'wb') as f:
                    f.write(decompressed)
            elif format == 'zip':
                with zipfile.ZipFile(input_path, 'r') as zf:
                    # Extract all files
                    zf.extractall(output_path.parent)
                    # Return path to first extracted file
                    names = zf.namelist()
                    if names:
                        output_path = output_path.parent / names[0]
            else:
                raise CompressionError(f"Unsupported format for decompression: {format}")

            # Remove compressed file if requested
            if remove_compressed:
                input_path.unlink()

            return output_path

        except Exception as e:
            if isinstance(e, CompressionError):
                raise
            raise CompressionError(f"File decompression failed: {e}") from e

    @staticmethod
    def create_archive(
        files: List[Path],
        output_path: Path,
        format: CompressionFormat = 'tar.gz',
        base_dir: Optional[Path] = None
    ) -> Path:
        """Create an archive from multiple files.

        Args:
            files: List of files to archive
            output_path: Path to output archive
            format: Archive format (zip, tar, tar.gz, tar.bz2, tar.xz)
            base_dir: Base directory for relative paths (None = use absolute)

        Returns:
            Path to created archive

        Raises:
            CompressionError: If archive creation fails
        """
        try:
            # Convert to Path objects
            files = [Path(f) if isinstance(f, str) else f for f in files]
            if isinstance(output_path, str):
                output_path = Path(output_path)

            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create archive based on format
            if format == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path in files:
                        if not file_path.exists():
                            raise CompressionError(f"File not found: {file_path}")

                        # Calculate archive name
                        if base_dir:
                            arcname = file_path.relative_to(base_dir)
                        else:
                            arcname = file_path.name

                        zf.write(file_path, arcname=arcname)

            elif format in ('tar', 'tar.gz', 'tar.bz2', 'tar.xz'):
                # Determine compression mode
                mode_map = {
                    'tar': 'w',
                    'tar.gz': 'w:gz',
                    'tar.bz2': 'w:bz2',
                    'tar.xz': 'w:xz',
                }
                mode = mode_map[format]

                with tarfile.open(output_path, mode) as tf:
                    for file_path in files:
                        if not file_path.exists():
                            raise CompressionError(f"File not found: {file_path}")

                        # Calculate archive name
                        if base_dir:
                            arcname = str(file_path.relative_to(base_dir))
                        else:
                            arcname = file_path.name

                        tf.add(file_path, arcname=arcname)

            else:
                raise CompressionError(f"Unsupported archive format: {format}")

            return output_path

        except Exception as e:
            if isinstance(e, CompressionError):
                raise
            raise CompressionError(f"Archive creation failed: {e}") from e

    @staticmethod
    def extract_archive(
        archive_path: Path,
        output_dir: Path,
        format: Optional[CompressionFormat] = None
    ) -> List[Path]:
        """Extract an archive.

        Args:
            archive_path: Path to archive file
            output_dir: Directory to extract to
            format: Archive format (None = auto-detect)

        Returns:
            List of extracted file paths

        Raises:
            CompressionError: If extraction fails
        """
        try:
            # Convert to Path objects
            if isinstance(archive_path, str):
                archive_path = Path(archive_path)
            if isinstance(output_dir, str):
                output_dir = Path(output_dir)

            # Check archive exists
            if not archive_path.exists():
                raise CompressionError(f"Archive not found: {archive_path}")

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Auto-detect format if not provided
            if format is None:
                suffix = archive_path.suffix.lower()
                if suffix == '.zip':
                    format = 'zip'
                elif archive_path.name.endswith('.tar.gz'):
                    format = 'tar.gz'
                elif archive_path.name.endswith('.tar.bz2'):
                    format = 'tar.bz2'
                elif archive_path.name.endswith('.tar.xz'):
                    format = 'tar.xz'
                elif suffix == '.tar':
                    format = 'tar'
                else:
                    raise CompressionError(f"Cannot auto-detect archive format: {suffix}")

            extracted_files = []

            # Extract based on format
            if format == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(output_dir)
                    extracted_files = [output_dir / name for name in zf.namelist()]

            elif format in ('tar', 'tar.gz', 'tar.bz2', 'tar.xz'):
                with tarfile.open(archive_path, 'r:*') as tf:
                    tf.extractall(output_dir)
                    extracted_files = [output_dir / member.name for member in tf.getmembers()]

            else:
                raise CompressionError(f"Unsupported archive format: {format}")

            return extracted_files

        except Exception as e:
            if isinstance(e, CompressionError):
                raise
            raise CompressionError(f"Archive extraction failed: {e}") from e

    @staticmethod
    def get_compression_ratio(
        original_size: int,
        compressed_size: int
    ) -> float:
        """Calculate compression ratio.

        Args:
            original_size: Original data size in bytes
            compressed_size: Compressed data size in bytes

        Returns:
            Compression ratio (1.0 = no compression, <1.0 = expansion, >1.0 = compression)
        """
        if compressed_size == 0:
            return 0.0
        return original_size / compressed_size

    @staticmethod
    def estimate_compressed_size(
        data_size: int,
        format: CompressionFormat = 'gzip',
        data_type: str = 'text'
    ) -> int:
        """Estimate compressed size.

        Args:
            data_size: Original data size in bytes
            format: Compression format
            data_type: Type of data ('text', 'binary', 'image', 'video')

        Returns:
            Estimated compressed size in bytes
        """
        # Rough compression ratio estimates
        ratios = {
            'gzip': {'text': 0.3, 'binary': 0.6, 'image': 0.9, 'video': 0.95},
            'bz2': {'text': 0.25, 'binary': 0.55, 'image': 0.9, 'video': 0.95},
            'lzma': {'text': 0.2, 'binary': 0.5, 'image': 0.9, 'video': 0.95},
        }

        format_key = format.replace('tar.', '')
        if format_key in ratios and data_type in ratios[format_key]:
            ratio = ratios[format_key][data_type]
        else:
            # Default: assume 50% compression
            ratio = 0.5

        return int(data_size * ratio)
