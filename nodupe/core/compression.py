# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
"""Compression module for file compression utilities."""

from __future__ import annotations
import gzip
import bz2
import lzma
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, List, Union

PathLike = Union[str, Path]
CompressionFormat = str


class CompressionError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class Compression:
    DATA_FORMATS = ['gzip', 'bz2', 'lzma']
    EXTENSION_MAP = {'.gz': 'gzip', '.bz2': 'bz2', '.xz': 'lzma', '.zip': 'zip'}
    TAR_MODE_MAP = {'tar': 'w', 'tar.gz': 'w:gz', 'tar.bz2': 'w:bz2', 'tar.xz': 'w:xz'}
    COMPRESSION_RATIOS = {
        'gzip': {'text': 0.3, 'binary': 0.6, 'image': 0.9, 'video': 0.95},
        'bz2': {'text': 0.25, 'binary': 0.55, 'image': 0.9, 'video': 0.95},
        'lzma': {'text': 0.2, 'binary': 0.5, 'image': 0.9, 'video': 0.95},
    }

    @staticmethod
    def _ensure_path(path: PathLike) -> Path:
        return Path(path) if isinstance(path, str) else path

    @staticmethod
    def _validate_extraction_path(output_dir: Path, member_name: str) -> None:
        """Validate that extraction path does not escape the target directory.
        
        Raises CompressionError if the path would escape the target directory
        via path traversal attacks (e.g., ../../evil.py, absolute paths).
        """
        member_path = (output_dir / member_name).resolve()
        output_dir_resolved = output_dir.resolve()
        
        try:
            member_path.relative_to(output_dir_resolved)
        except ValueError:  # pragma: no cover - only unsafe paths trigger this
            raise CompressionError(
                f"Unsafe extraction path detected: '{member_name}' would escape target directory"
            )

    @staticmethod
    def compress_data(data: bytes, format: CompressionFormat = 'gzip', level: int = 6) -> bytes:
        try:
            if format == 'gzip':
                return gzip.compress(data, compresslevel=level)
            if format == 'bz2':
                return bz2.compress(data, compresslevel=level)
            if format == 'lzma':
                return lzma.compress(data, preset=level)
            raise CompressionError(f"Unsupported format: {format}")
        except Exception as e:
            raise CompressionError(f"Compression failed: {e}") from e

    @staticmethod
    def decompress_data(data: bytes, format: CompressionFormat = 'gzip') -> bytes:
        try:
            if format == 'gzip':
                return gzip.decompress(data)
            if format == 'bz2':
                return bz2.decompress(data)
            if format == 'lzma':
                return lzma.decompress(data)
            raise CompressionError(f"Unsupported format: {format}")
        except Exception as e:
            raise CompressionError(f"Decompression failed: {e}") from e

    @staticmethod
    def compress_file(
        input_path: PathLike,
        output_path: Optional[PathLike] = None,
        format: CompressionFormat = 'gzip',
        level: int = 6,
        remove_original: bool = False
    ) -> Path:
        input_path_obj = Compression._ensure_path(input_path)
        if not input_path_obj.exists():
            raise CompressionError(f"Input file does not exist: {input_path}")

        try:
            if output_path is None:
                ext = {'.gz': '.gz', '.bz2': '.bz2', '.xz': '.xz', '.zip': '.zip'}.get(format, f'.{format}')
                output_path_obj = input_path_obj.with_suffix(input_path_obj.suffix + ext)
            else:
                output_path_obj = Compression._ensure_path(output_path)

            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise CompressionError(f"File compression failed: {e}") from e

        try:
            with open(input_path_obj, 'rb') as f:
                file_data = f.read()

            if format in Compression.DATA_FORMATS:
                compressed = Compression.compress_data(file_data, format, level)
                with open(output_path_obj, 'wb') as f:
                    f.write(compressed)
            elif format == 'zip':
                with zipfile.ZipFile(output_path_obj, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(input_path_obj, arcname=input_path_obj.name)
            else:  # pragma: no cover - not tested with invalid format
                raise CompressionError(f"Unsupported format: {format}")
        except CompressionError:
            raise
        except Exception as e:
            raise CompressionError(f"File compression failed: {e}") from e

        if remove_original:
            try:
                input_path_obj.unlink()
            except Exception as e:  # pragma: no cover - unreachable
                raise CompressionError(f"Failed to remove original: {e}") from e

        return output_path_obj

    @staticmethod
    def decompress_file(
        input_path: PathLike,
        output_path: Optional[PathLike] = None,
        format: Optional[CompressionFormat] = None,
        remove_compressed: bool = False
    ) -> Path:
        input_path_obj = Compression._ensure_path(input_path)
        if not input_path_obj.exists():
            raise CompressionError(f"Input file does not exist: {input_path}")

        try:
            detected = format
            if detected is None:
                suffix = input_path_obj.suffix.lower()
                detected = Compression.EXTENSION_MAP.get(suffix)
                if detected is None:
                    raise CompressionError(f"Cannot auto-detect format for: {suffix}")

            if output_path is None:
                if input_path_obj.suffix in ('.gz', '.bz2', '.xz'):
                    output_path_obj = input_path_obj.with_suffix('')
                else:
                    output_path_obj = input_path_obj.with_suffix('.decompressed')
            else:
                output_path_obj = Compression._ensure_path(output_path)

            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        except CompressionError:
            raise
        except Exception as e:
            raise CompressionError(f"File decompression failed: {e}") from e

        try:
            if detected in Compression.DATA_FORMATS:
                with open(input_path_obj, 'rb') as f:
                    compressed_data = f.read()
                decompressed = Compression.decompress_data(compressed_data, detected)
                with open(output_path_obj, 'wb') as f:
                    f.write(decompressed)
            elif detected == 'zip':
                with zipfile.ZipFile(input_path_obj, 'r') as zf:
                    zf.extractall(output_path_obj.parent)
                    names = zf.namelist()
                    if names:
                        output_path_obj = output_path_obj.parent / names[0]
            else:  # pragma: no cover - not tested with invalid format
                raise CompressionError(f"Unsupported format: {detected}")
        except CompressionError:
            raise
        except Exception as e:
            raise CompressionError(f"File decompression failed: {e}") from e

        if remove_compressed:
            try:
                input_path_obj.unlink()
            except Exception as e:
                raise CompressionError(f"Failed to remove compressed: {e}") from e

        return output_path_obj

    @staticmethod
    def create_archive(
        files: List[PathLike],
        output_path: PathLike,
        format: CompressionFormat = 'tar.gz',
        base_dir: Optional[PathLike] = None
    ) -> Path:
        try:
            file_paths = [Compression._ensure_path(f) for f in files]
            output_path_obj = Compression._ensure_path(output_path)
            base_dir_obj = Compression._ensure_path(base_dir) if base_dir else None

            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            if format == 'zip':
                with zipfile.ZipFile(output_path_obj, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path in file_paths:
                        if not file_path.exists():
                            raise CompressionError(f"File not found: {file_path}")
                        arcname = str(file_path.relative_to(base_dir_obj)) if base_dir_obj else file_path.name
                        zf.write(file_path, arcname=arcname)
            elif format in Compression.TAR_MODE_MAP:
                mode = Compression.TAR_MODE_MAP[format]
                with tarfile.open(str(output_path_obj), mode) as tf:
                    for file_path in file_paths:
                        if not file_path.exists():
                            raise CompressionError(f"File not found: {file_path}")
                        arcname = str(file_path.relative_to(base_dir_obj)) if base_dir_obj else file_path.name
                        tf.add(file_path, arcname=arcname)
            else:  # pragma: no cover - not tested with invalid format
                raise CompressionError(f"Unsupported format: {format}")

            return output_path_obj
        except CompressionError:
            raise
        except Exception as e:
            raise CompressionError(f"Archive creation failed: {e}") from e

    @staticmethod
    def extract_archive(
        archive_path: PathLike,
        output_dir: PathLike,
        format: Optional[CompressionFormat] = None
    ) -> List[Path]:
        archive_path_obj = Compression._ensure_path(archive_path)
        output_dir_obj = Compression._ensure_path(output_dir)

        if not archive_path_obj.exists():
            raise CompressionError(f"Archive not found: {archive_path}")

        try:
            output_dir_obj.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise CompressionError(f"Archive extraction failed: {e}") from e

        detected = format
        if detected is None:
            suffix = archive_path_obj.suffix.lower()
            if suffix == '.zip':
                detected = 'zip'
            elif archive_path_obj.name.endswith('.tar.gz'):
                detected = 'tar.gz'
            elif archive_path_obj.name.endswith('.tar.bz2'):
                detected = 'tar.bz2'
            elif archive_path_obj.name.endswith('.tar.xz'):
                detected = 'tar.xz'
            elif suffix == '.tar':
                detected = 'tar'
            else:
                raise CompressionError(f"Cannot auto-detect format: {suffix}")

        extracted_files = []

        if detected == 'zip':
            try:
                with zipfile.ZipFile(archive_path_obj, 'r') as zf:
                    for name in zf.namelist():
                        Compression._validate_extraction_path(output_dir_obj, name)
                    zf.extractall(output_dir_obj)
                    extracted_files = [output_dir_obj / name for name in zf.namelist()]
            except CompressionError:
                raise
            except Exception as e:
                raise CompressionError(f"Archive extraction failed: {e}") from e
                
        elif detected in Compression.TAR_MODE_MAP:
            try:
                with tarfile.open(archive_path_obj, 'r:*') as tf:
                    for member in tf.getmembers():
                        Compression._validate_extraction_path(output_dir_obj, member.name)
                    tf.extractall(output_dir_obj)
                    extracted_files = [output_dir_obj / member.name for member in tf.getmembers()]
            except CompressionError:
                raise
            except Exception as e:
                raise CompressionError(f"Archive extraction failed: {e}") from e
        else:  # pragma: no cover - not tested with invalid format
            raise CompressionError(f"Unsupported format: {detected}")

        return extracted_files

    @staticmethod
    def get_compression_ratio(original_size: int, compressed_size: int) -> float:
        return original_size / compressed_size if compressed_size else 0.0

    @staticmethod
    def estimate_compressed_size(data_size: int, format: CompressionFormat = 'gzip', data_type: str = 'text') -> int:
        format_key = format.replace('tar.', '')
        ratio = 0.5
        if format_key in Compression.COMPRESSION_RATIOS:
            ratios = Compression.COMPRESSION_RATIOS[format_key]
            if data_type in ratios:
                ratio = ratios[data_type]
        return int(data_size * ratio)
