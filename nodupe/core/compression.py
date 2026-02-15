# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from __future__ import annotations
import gzip
import bz2
import lzma
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, List, Union


PathLike = Union[str, Path]


class CompressionError(Exception):
    pass


class Compression:
    DATA_FORMATS = ['gzip', 'bz2', 'lzma']
    EXTENSION_MAP = {
        '.gz': 'gzip',
        '.bz2': 'bz2',
        '.xz': 'lzma',
        '.zip': 'zip'
    }

    FORMAT_EXTENSION = {
        'gzip': '.gz',
        'bz2': '.bz2',
        'lzma': '.xz',
        'zip': '.zip'
    }

    TAR_MODE_MAP = {
        'tar': 'w',
        'tar.gz': 'w:gz',
        'tar.bz2': 'w:bz2',
        'tar.xz': 'w:xz'
    }

    COMPRESSION_RATIOS = {
        'gzip': {'text': 0.3, 'binary': 0.6},
        'gz': {'text': 0.3, 'binary': 0.6},
        'bz2': {'text': 0.25, 'binary': 0.55},
        'lzma': {'text': 0.2, 'binary': 0.5},
    }

    @staticmethod
    def _ensure_path(path: PathLike) -> Path:
        return Path(path)

    @staticmethod
    def _validate_extraction_path(output_dir: Path, member_name: str) -> None:
        member_path = (output_dir / member_name).resolve()
        output_dir_resolved = output_dir.resolve()
        try:
            member_path.relative_to(output_dir_resolved)
        except ValueError:
            raise CompressionError(
                f"Unsafe extraction path: {member_name}"
            )

    @staticmethod
    def _validate_format(format: str) -> None:
        if format not in Compression.DATA_FORMATS and \
           format not in Compression.FORMAT_EXTENSION and \
           format not in Compression.TAR_MODE_MAP:
            raise CompressionError(f"Unsupported format: {format}")

    @staticmethod
    def compress_data(data: bytes, format: str = 'gzip', level: int = 6) -> bytes:
        Compression._validate_format(format)

        try:
            if format == 'gzip':
                return gzip.compress(data, compresslevel=level)
            if format == 'bz2':
                return bz2.compress(data, compresslevel=level)
            if format == 'lzma':
                return lzma.compress(data, preset=level)
        except Exception as e:
            raise CompressionError(f"Compression failed: {e}") from e

        raise CompressionError(f"Unsupported format: {format}")

    @staticmethod
    def decompress_data(data: bytes, format: str = 'gzip') -> bytes:
        Compression._validate_format(format)

        try:
            if format == 'gzip':
                return gzip.decompress(data)
            if format == 'bz2':
                return bz2.decompress(data)
            if format == 'lzma':
                return lzma.decompress(data)
        except Exception as e:
            raise CompressionError(f"Decompression failed: {e}") from e

        raise CompressionError(f"Unsupported format: {format}")

    @staticmethod
    def compress_file(
        input_path: PathLike,
        output_path: Optional[PathLike] = None,
        format: str = 'gzip',
        remove_original: bool = False
    ) -> Path:

        input_path = Compression._ensure_path(input_path)
        if not input_path.exists():
            raise CompressionError("Input file does not exist")

        Compression._validate_format(format)

        if output_path is None:
            ext = Compression.FORMAT_EXTENSION.get(format, f'.{format}')
            output_path = input_path.with_suffix(input_path.suffix + ext)
        else:
            output_path = Compression._ensure_path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format in Compression.DATA_FORMATS:
                with open(input_path, 'rb') as src:
                    data = src.read()
                compressed = Compression.compress_data(data, format)
                with open(output_path, 'wb') as dst:
                    dst.write(compressed)

            elif format == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(input_path, arcname=input_path.name)

            else:
                raise CompressionError(f"Unsupported format: {format}")

        except Exception as e:
            raise CompressionError(f"File compression failed: {e}") from e

        if remove_original:
            try:
                input_path.unlink()
            except Exception as e:
                raise CompressionError(f"Failed to remove original: {e}") from e

        return output_path

    @staticmethod
    def decompress_file(
        input_path: PathLike,
        format: Optional[str] = None,
        remove_compressed: bool = False
    ) -> Path:

        input_path = Compression._ensure_path(input_path)
        if not input_path.exists():
            raise CompressionError("Input file does not exist")

        if format is None:
            format = Compression.EXTENSION_MAP.get(input_path.suffix.lower())
            if not format:
                raise CompressionError("Cannot auto-detect format")

        Compression._validate_format(format)

        output_path = input_path.with_suffix('')

        try:
            if format in Compression.DATA_FORMATS:
                with open(input_path, 'rb') as src:
                    data = src.read()
                decompressed = Compression.decompress_data(data, format)
                with open(output_path, 'wb') as dst:
                    dst.write(decompressed)

            elif format == 'zip':
                with zipfile.ZipFile(input_path, 'r') as zf:
                    for name in zf.namelist():
                        Compression._validate_extraction_path(output_path.parent, name)
                    zf.extractall(output_path.parent)

            else:
                raise CompressionError(f"Unsupported format: {format}")

        except Exception as e:
            raise CompressionError(f"File decompression failed: {e}") from e

        if remove_compressed:
            input_path.unlink()

        return output_path

    @staticmethod
    def extract_archive(
        archive_path: PathLike,
        output_dir: PathLike,
        format: Optional[str] = None
    ) -> List[Path]:
        """Extract archive (zip, tar, tar.gz, tar.bz2, tar.xz) to output directory.

        Args:
            archive_path: Path to the archive file
            output_dir: Directory to extract to
            format: Optional format hint ('zip', 'tar', 'tar.gz', etc.)

        Returns:
            List of extracted file paths

        Raises:
            CompressionError: If archive cannot be extracted
        """
        archive_path = Compression._ensure_path(archive_path)
        output_dir = Compression._ensure_path(output_dir)

        if not archive_path.exists():
            raise CompressionError("Archive not found")

        # Auto-detect format if not provided
        detected = format
        if detected is None:
            suffix = archive_path.suffix.lower()
            if suffix == '.zip':
                detected = 'zip'
            elif archive_path.name.endswith('.tar.gz'):
                detected = 'tar.gz'
            elif archive_path.name.endswith('.tar.bz2'):
                detected = 'tar.bz2'
            elif archive_path.name.endswith('.tar.xz'):
                detected = 'tar.xz'
            elif suffix == '.tar':
                detected = 'tar'
            else:
                raise CompressionError(f"Cannot auto-detect format for: {archive_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        extracted_files: List[Path] = []

        if detected == 'zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                # Validate all paths before extracting
                for name in zf.namelist():
                    Compression._validate_extraction_path(output_dir, name)
                zf.extractall(output_dir)
                extracted_files = [output_dir / name for name in zf.namelist()]

        elif detected in Compression.TAR_MODE_MAP:
            with tarfile.open(archive_path, 'r:*') as tf:
                # Validate all paths before extracting
                for member in tf.getmembers():
                    Compression._validate_extraction_path(output_dir, member.name)
                tf.extractall(output_dir)
                extracted_files = [output_dir / member.name for member in tf.getmembers()]
        else:
            raise CompressionError(f"Unsupported format: {detected}")

        return extracted_files

    @staticmethod
    def get_compression_ratio(original: int, compressed: int) -> float:
        return original / compressed if compressed else 0.0

    @staticmethod
    def estimate_compressed_size(
        size: int,
        format: str = 'gzip',
        data_type: str = 'text'
    ) -> int:

        format_key = format.replace('tar.', '')
        ratios = Compression.COMPRESSION_RATIOS.get(format_key)
        if ratios:
            ratio = ratios.get(data_type, 0.5)
        else:
            ratio = 0.5

        return int(size * ratio)
