"""Tests for MIME detection module."""

import pytest
from pathlib import Path
from nodupe.core.mime_detection import MIMEDetection, MIMEDetectionError


class TestMIMEDetection:
    """Test MIMEDetection class."""

    def test_detect_mime_type_by_extension(self, tmp_path):
        """Test MIME detection by file extension."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        mime = MIMEDetection.detect_mime_type(str(test_file), use_magic=False)
        assert mime == "text/plain"

    def test_detect_mime_type_pdf(self, tmp_path):
        """Test PDF MIME detection."""
        test_file = tmp_path / "test.pdf"
        # PDF magic number
        test_file.write_bytes(b"%PDF-1.4\n")

        mime = MIMEDetection.detect_mime_type(str(test_file), use_magic=True)
        assert mime == "application/pdf"

    def test_detect_mime_type_jpeg(self, tmp_path):
        """Test JPEG MIME detection."""
        test_file = tmp_path / "test.jpg"
        # JPEG magic number
        test_file.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)

        mime = MIMEDetection.detect_mime_type(str(test_file), use_magic=True)
        assert mime == "image/jpeg"

    def test_detect_mime_type_png(self, tmp_path):
        """Test PNG MIME detection."""
        test_file = tmp_path / "test.png"
        # PNG magic number
        test_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        mime = MIMEDetection.detect_mime_type(str(test_file), use_magic=True)
        assert mime == "image/png"

    def test_detect_mime_type_unknown(self, tmp_path):
        """Test unknown MIME type defaults to octet-stream."""
        test_file = tmp_path / "test.unknown"
        test_file.write_bytes(b"random data")

        mime = MIMEDetection.detect_mime_type(str(test_file))
        assert mime == "application/octet-stream"

    def test_get_extension_for_mime(self):
        """Test getting file extension for MIME type."""
        ext = MIMEDetection.get_extension_for_mime("image/jpeg")
        assert ext in [".jpg", ".jpeg", ".jpe"]

        ext = MIMEDetection.get_extension_for_mime("text/plain")
        assert ext == ".txt"

    def test_is_text(self):
        """Test text MIME type detection."""
        assert MIMEDetection.is_text("text/plain")
        assert MIMEDetection.is_text("text/html")
        assert MIMEDetection.is_text("application/json")
        assert MIMEDetection.is_text("application/xml")
        assert not MIMEDetection.is_text("image/jpeg")

    def test_is_image(self):
        """Test image MIME type detection."""
        assert MIMEDetection.is_image("image/jpeg")
        assert MIMEDetection.is_image("image/png")
        assert not MIMEDetection.is_image("text/plain")

    def test_is_audio(self):
        """Test audio MIME type detection."""
        assert MIMEDetection.is_audio("audio/mpeg")
        assert MIMEDetection.is_audio("audio/wav")
        assert not MIMEDetection.is_audio("video/mp4")

    def test_is_video(self):
        """Test video MIME type detection."""
        assert MIMEDetection.is_video("video/mp4")
        assert MIMEDetection.is_video("video/avi")
        assert not MIMEDetection.is_video("audio/mpeg")

    def test_is_archive(self):
        """Test archive MIME type detection."""
        assert MIMEDetection.is_archive("application/zip")
        assert MIMEDetection.is_archive("application/x-tar")
        assert not MIMEDetection.is_archive("text/plain")

    def test_extension_map_coverage(self):
        """Test that extension map contains common formats."""
        assert ".jpg" in MIMEDetection.EXTENSION_MAP
        assert ".png" in MIMEDetection.EXTENSION_MAP
        assert ".pdf" in MIMEDetection.EXTENSION_MAP
        assert ".mp3" in MIMEDetection.EXTENSION_MAP
        assert ".mp4" in MIMEDetection.EXTENSION_MAP
        assert ".zip" in MIMEDetection.EXTENSION_MAP
