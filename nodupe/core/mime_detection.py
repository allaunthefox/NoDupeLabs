"""MIME Detection Module.

MIME type detection using standard library only.

Key Features:
    - MIME type detection via mimetypes module
    - File extension mapping
    - Magic number detection for common formats
    - RFC 6838 compliance
    - Standard library only (no external dependencies)

Dependencies:
    - mimetypes (standard library)
    - pathlib (standard library)
"""

import mimetypes
from pathlib import Path
from typing import Optional, Dict


class MIMEDetectionError(Exception):
    """MIME detection error"""


class MIMEDetection:
    """Handle MIME type detection.

    Provides MIME type detection using standard library mimetypes module
    with fallback to magic number detection for common formats.
    """

    # Magic number signatures for common file formats
    # Format: (offset, magic_bytes, mime_type)
    MAGIC_NUMBERS = [
        # Images
        (0, b'\xFF\xD8\xFF', 'image/jpeg'),
        (0, b'\x89PNG\r\n\x1a\n', 'image/png'),
        (0, b'GIF87a', 'image/gif'),
        (0, b'GIF89a', 'image/gif'),
        (0, b'BM', 'image/bmp'),
        (0, b'II*\x00', 'image/tiff'),  # Little-endian TIFF
        (0, b'MM\x00*', 'image/tiff'),  # Big-endian TIFF
        (0, b'RIFF', 'image/webp'),     # Need to check for 'WEBP' at offset 8

        # Documents
        (0, b'%PDF-', 'application/pdf'),
        (0, b'PK\x03\x04', 'application/zip'),  # Also used by docx, xlsx, etc.
        (0, b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', 'application/msword'),  # DOC

        # Audio
        (0, b'ID3', 'audio/mpeg'),      # MP3 with ID3
        (0, b'\xFF\xFB', 'audio/mpeg'),  # MP3
        (0, b'\xFF\xF3', 'audio/mpeg'),  # MP3
        (0, b'\xFF\xF2', 'audio/mpeg'),  # MP3
        (0, b'RIFF', 'audio/wav'),      # Need to check for 'WAVE' at offset 8
        (0, b'fLaC', 'audio/flac'),
        (0, b'OggS', 'audio/ogg'),

        # Video
        (4, b'ftyp', 'video/mp4'),      # MP4, offset 4
        (0, b'\x1A\x45\xDF\xA3', 'video/webm'),  # WebM/MKV
        (0, b'RIFF', 'video/avi'),      # Need to check for 'AVI ' at offset 8

        # Archives
        (0, b'Rar!\x1A\x07', 'application/x-rar-compressed'),
        (0, b'7z\xBC\xAF\x27\x1C', 'application/x-7z-compressed'),
        (257, b'ustar', 'application/x-tar'),  # TAR

        # Executables
        (0, b'MZ', 'application/x-msdownload'),  # Windows EXE
        (0, b'\x7FELF', 'application/x-executable'),  # ELF (Linux)
    ]

    # Extension to MIME type mapping (fallback)
    EXTENSION_MAP: Dict[str, str] = {
        # Images
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',

        # Documents
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.txt': 'text/plain',
        '.rtf': 'application/rtf',
        '.odt': 'application/vnd.oasis.opendocument.text',

        # Audio
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4',
        '.aac': 'audio/aac',
        '.wma': 'audio/x-ms-wma',

        # Video
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',

        # Archives
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',
        '.bz2': 'application/x-bzip2',

        # Code/Text
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.htm': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.py': 'text/x-python',
        '.java': 'text/x-java',
        '.c': 'text/x-c',
        '.cpp': 'text/x-c++',
        '.h': 'text/x-c',
        '.sh': 'application/x-sh',
        '.md': 'text/markdown',
    }

    @staticmethod
    def detect_mime_type(file_path: Optional[str], use_magic: bool = True) -> str:
        """Detect MIME type.

        Args:
            file_path: Path to file
            use_magic: Use magic number detection (slower but more accurate)

        Returns:
            MIME type string

        Raises:
            MIMEDetectionError: If MIME type cannot be detected
        """
        # Handle None as file_path
        if file_path is None:
            raise MIMEDetectionError("File path cannot be None")
        
        # Initialize path outside the try block to avoid unbound variable
        path = Path(file_path)  # Path() handles both str and Path objects
        
        try:
            # Try magic number detection first (if enabled and file exists)
            if use_magic and path.exists() and path.is_file():
                magic_mime = MIMEDetection._detect_by_magic(path)
                if magic_mime:
                    return magic_mime

            # Try standard library mimetypes
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type:
                return mime_type

            # Try extension mapping
            extension = path.suffix.lower()
            if extension in MIMEDetection.EXTENSION_MAP:
                return MIMEDetection.EXTENSION_MAP[extension]

            # Default to octet-stream
            return 'application/octet-stream'

        except Exception as e:
            raise MIMEDetectionError(f"Failed to detect MIME type for {str(path)}: {e}") from e

    @staticmethod
    def _detect_by_magic(file_path: Path, max_read: int = 512) -> Optional[str]:
        """Detect MIME type by magic number.

        Args:
            file_path: Path to file
            max_read: Maximum bytes to read for detection

        Returns:
            MIME type string or None if not detected
        """
        try:
            # Read first bytes of file
            with open(file_path, 'rb') as f:
                header = f.read(max_read)

            # Check magic numbers
            for offset, magic, mime_type in MIMEDetection.MAGIC_NUMBERS:
                if len(header) > offset + len(magic):
                    if header[offset:offset + len(magic)] == magic:
                        # Special cases that need additional verification
                        if magic == b'RIFF' and len(header) > 12:
                            # Check RIFF subtype
                            riff_type = header[8:12]
                            if riff_type == b'WAVE':
                                return 'audio/wav'
                            if riff_type == b'WEBP':
                                return 'image/webp'
                            if riff_type == b'AVI ':
                                return 'video/avi'
                        elif magic == b'PK\x03\x04':
                            # Could be ZIP, DOCX, XLSX, etc.
                            # Default to ZIP, let extension mapping handle office formats
                            return 'application/zip'
                        else:
                            return mime_type

            return None

        except (OSError, IOError):
            return None

    @staticmethod
    def get_extension_for_mime(mime_type: str) -> Optional[str]:
        """Get file extension for MIME type.

        Args:
            mime_type: MIME type string

        Returns:
            File extension (with dot) or None
        """
        # Try standard library first
        extension = mimetypes.guess_extension(mime_type)
        if extension:
            return extension

        # Reverse lookup in extension map
        for ext, mime in MIMEDetection.EXTENSION_MAP.items():
            if mime == mime_type:
                return ext

        return None

    @staticmethod
    def is_text(mime_type: str) -> bool:
        """Check if MIME type is text.

        Args:
            mime_type: MIME type string

        Returns:
            True if MIME type is text
        """
        # Remove any parameters after semicolon
        base_mime_type = mime_type.split(';')[0].strip()
        return base_mime_type.startswith('text/') or base_mime_type in [
            'application/json',
            'application/xml',
            'application/javascript',
            'application/x-sh',
        ]

    @staticmethod
    def is_image(mime_type: str) -> bool:
        """Check if MIME type is image.

        Args:
            mime_type: MIME type string

        Returns:
            True if MIME type is image
        """
        return mime_type.startswith('image/')

    @staticmethod
    def is_audio(mime_type: str) -> bool:
        """Check if MIME type is audio.

        Args:
            mime_type: MIME type string

        Returns:
            True if MIME type is audio
        """
        return mime_type.startswith('audio/')

    @staticmethod
    def is_video(mime_type: str) -> bool:
        """Check if MIME type is video.

        Args:
            mime_type: MIME type string

        Returns:
            True if MIME type is video
        """
        return mime_type.startswith('video/')

    @staticmethod
    def is_archive(mime_type: str) -> bool:
        """Check if MIME type is archive.

        Args:
            mime_type: MIME type string

        Returns:
            True if MIME type is archive
        """
        return mime_type in [
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            'application/x-tar',
            'application/gzip',
            'application/x-bzip2',
            'application/x-xz',
            'application/x-lzma',
        ]


# Initialize mimetypes database
mimetypes.init()
