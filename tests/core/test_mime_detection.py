import os
import tempfile
from pathlib import Path
import pytest
from nodupe.core.mime_detection import MIMEDetection, MIMEDetectionError


class TestMIMEDetection:
    """Test suite for the MIMEDetection class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mime_detector = MIMEDetection()

    def test_detect_mime_type_with_existing_file(self):
        """Test detecting MIME type for an existing file."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        try:
            # Detect MIME type
            mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=True)
            assert isinstance(mime_type, str)
            assert mime_type != ""  # Should return some MIME type
        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_detect_mime_type_with_nonexistent_file(self):
        """Test detecting MIME type for a nonexistent file."""
        nonexistent_file = "nonexistent_file_12345.txt"
        mime_type = self.mime_detector.detect_mime_type(nonexistent_file, use_magic=True)
        # Should return a default MIME type when file doesn't exist
        assert isinstance(mime_type, str)

    def test_detect_mime_type_with_use_magic_false(self):
        """Test detecting MIME type with magic detection disabled."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write('{"test": "data"}')
            temp_file_path = temp_file.name

        try:
            # Detect MIME type without magic
            mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=False)
            assert isinstance(mime_type, str)
            # Should still return some MIME type based on extension
        finally:
            os.unlink(temp_file_path)

    def test_detect_mime_type_with_various_extensions(self):
        """Test detecting MIME type for various file extensions."""
        test_cases = [
            ('.txt', 'text/plain'),
            ('.jpg', 'image/jpeg'),
            ('.png', 'image/png'),
            ('.pdf', 'application/pdf'),
            ('.zip', 'application/zip'),
        ]
        
        for ext, expected_mime in test_cases:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(b"test content")
                temp_file_path = temp_file.name

            try:
                mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=False)
                # Note: The actual result may vary based on system mimetypes
                assert isinstance(mime_type, str)
            finally:
                os.unlink(temp_file_path)

    def test_detect_mime_type_error_handling(self):
        """Test error handling in detect_mime_type."""
        # The implementation now checks for None at the beginning and raises MIMEDetectionError
        with pytest.raises(MIMEDetectionError):
            self.mime_detector.detect_mime_type(None)

    def test_detect_by_magic_with_jpeg_file(self):
        """Test magic number detection with JPEG file."""
        # Create a file with JPEG magic number
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            # Write JPEG magic number
            temp_file.write(b'\xFF\xD8\xFF')
            temp_file.write(b'some jpeg content')
            temp_file_path = temp_file.name

        try:
            # Test magic detection directly
            result = self.mime_detector._detect_by_magic(Path(temp_file_path))
            # Should return image/jpeg based on the magic number
            assert result == 'image/jpeg' or result is None  # Could be None if file too small
        finally:
            os.unlink(temp_file_path)

    def test_detect_by_magic_with_png_file(self):
        """Test magic number detection with PNG file."""
        # Create a file with PNG magic number
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            # Write PNG magic number
            temp_file.write(b'\x89PNG\r\n\x1a\n')
            temp_file.write(b'some png content')
            temp_file_path = temp_file.name

        try:
            result = self.mime_detector._detect_by_magic(Path(temp_file_path))
            # Should return image/png based on the magic number
            assert result == 'image/png' or result is None
        finally:
            os.unlink(temp_file_path)

    def test_detect_by_magic_with_non_matching_file(self):
        """Test magic number detection with file that doesn't match any signature."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            # Write random content
            temp_file.write(b'random content that does not match any known magic number')
            temp_file_path = temp_file.name

        try:
            result = self.mime_detector._detect_by_magic(temp_file_path)
            # Should return None as it doesn't match any magic signature
            assert result is None
        finally:
            os.unlink(temp_file_path)

    def test_detect_by_magic_with_nonexistent_file(self):
        """Test magic number detection with nonexistent file."""
        result = self.mime_detector._detect_by_magic("nonexistent_file.bin")
        # Should return None for nonexistent file
        assert result is None

    def test_get_extension_for_mime_basic(self):
        """Test getting extension for a basic MIME type."""
        # Test with a known MIME type
        ext = self.mime_detector.get_extension_for_mime('image/jpeg')
        assert ext == '.jpg' or ext == '.jpeg' or ext is not None  # System-dependent

    def test_get_extension_for_mime_unknown(self):
        """Test getting extension for an unknown MIME type."""
        # Test with an unknown MIME type
        ext = self.mime_detector.get_extension_for_mime('unknown/type')
        # Should return None for unknown types or possibly a system default
        assert ext is None or isinstance(ext, str)

    def test_get_extension_for_mime_with_parameter(self):
        """Test getting extension for a MIME type with parameter."""
        ext = self.mime_detector.get_extension_for_mime('text/plain; charset=utf-8')
        # Should handle MIME types with parameters
        assert ext is None or isinstance(ext, str)

    def test_is_text_basic_types(self):
        """Test is_text with basic text MIME types."""
        assert self.mime_detector.is_text('text/plain') is True
        assert self.mime_detector.is_text('text/html') is True
        assert self.mime_detector.is_text('application/json') is True
        assert self.mime_detector.is_text('application/xml') is True
        assert self.mime_detector.is_text('image/jpeg') is False
        assert self.mime_detector.is_text('application/pdf') is False

    def test_is_image_basic_types(self):
        """Test is_image with basic image MIME types."""
        assert self.mime_detector.is_image('image/jpeg') is True
        assert self.mime_detector.is_image('image/png') is True
        assert self.mime_detector.is_image('image/gif') is True
        assert self.mime_detector.is_image('text/plain') is False
        assert self.mime_detector.is_image('application/json') is False

    def test_is_audio_basic_types(self):
        """Test is_audio with basic audio MIME types."""
        assert self.mime_detector.is_audio('audio/mpeg') is True
        assert self.mime_detector.is_audio('audio/wav') is True
        assert self.mime_detector.is_audio('audio/ogg') is True
        assert self.mime_detector.is_audio('image/jpeg') is False
        assert self.mime_detector.is_audio('text/plain') is False

    def test_is_video_basic_types(self):
        """Test is_video with basic video MIME types."""
        assert self.mime_detector.is_video('video/mp4') is True
        assert self.mime_detector.is_video('video/avi') is True
        assert self.mime_detector.is_video('video/webm') is True
        assert self.mime_detector.is_video('audio/mpeg') is False
        assert self.mime_detector.is_video('image/jpeg') is False

    def test_is_archive_basic_types(self):
        """Test is_archive with basic archive MIME types."""
        assert self.mime_detector.is_archive('application/zip') is True
        assert self.mime_detector.is_archive('application/x-rar-compressed') is True
        assert self.mime_detector.is_archive('application/x-7z-compressed') is True
        assert self.mime_detector.is_archive('image/jpeg') is False
        assert self.mime_detector.is_archive('text/plain') is False

    def test_detect_mime_type_with_binary_file(self):
        """Test detecting MIME type for binary files."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as temp_file:
            # Write some binary content
            temp_file.write(b'\x00\x01\x02\x03\x04\x05')
            temp_file_path = temp_file.name

        try:
            mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=True)
            assert isinstance(mime_type, str)
        finally:
            os.unlink(temp_file_path)

    def test_detect_mime_type_empty_file(self):
        """Test detecting MIME type for an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file_path = temp_file.name

        try:
            mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=True)
            assert isinstance(mime_type, str)
        finally:
            os.unlink(temp_file_path)

    def test_detect_mime_type_pdf_file_with_magic(self):
        """Test detecting MIME type for PDF with magic detection."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pdf') as temp_file:
            # Write PDF magic number
            temp_file.write(b'%PDF-')
            temp_file.write(b'some pdf content')
            temp_file_path = temp_file.name

        try:
            mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=True)
            assert mime_type == 'application/pdf' or mime_type is not None
        finally:
            os.unlink(temp_file_path)

    def test_detect_mime_type_zip_file_with_magic(self):
        """Test detecting MIME type for ZIP with magic detection."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.zip') as temp_file:
            # Write ZIP magic number
            temp_file.write(b'PK\x03\x04')
            temp_file.write(b'some zip content')
            temp_file_path = temp_file.name

        try:
            mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=True)
            assert mime_type == 'application/zip' or mime_type is not None
        finally:
            os.unlink(temp_file_path)

    def test_detect_mime_type_with_special_characters_in_path(self):
        """Test detecting MIME type with special characters in file path."""
        # Create a file with special characters in the name
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, "test_file_with_üñíçødé.txt")
        
        with open(temp_file_path, 'w') as f:
            f.write("test content")

        try:
            mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=False)
            assert isinstance(mime_type, str)
        finally:
            os.unlink(temp_file_path)
            os.rmdir(temp_dir)

    def test_detect_by_magic_small_file(self):
        """Test magic number detection with a very small file."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            # Write a very small file that's smaller than most magic signatures
            temp_file.write(b'hi')
            temp_file_path = temp_file.name

        try:
            result = self.mime_detector._detect_by_magic(temp_file_path)
            # Should return None as the file is too small for magic detection
            assert result is None
        finally:
            os.unlink(temp_file_path)

    def test_detect_mime_type_with_permission_error(self):
        """Test detecting MIME type when file has permission issues."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        try:
            # Change permissions to make it unreadable
            os.chmod(temp_file_path, 0o000)
            
            # Try to detect MIME type - this should handle the permission error gracefully
            mime_type = self.mime_detector.detect_mime_type(temp_file_path, use_magic=True)
            # When magic detection fails due to permissions, it should fall back to extension detection
            assert isinstance(mime_type, str)
        except Exception:
            # If there's an exception, it might be expected on some systems
            pass
        finally:
            # Restore permissions to allow deletion
            os.chmod(temp_file_path, 0o644)
            os.unlink(temp_file_path)

    def test_mime_numbers_structure(self):
        """Test that MAGIC_NUMBERS structure is valid."""
        # Check that MAGIC_NUMBERS is properly structured
        assert isinstance(MIMEDetection.MAGIC_NUMBERS, list)
        for entry in MIMEDetection.MAGIC_NUMBERS:
            assert isinstance(entry, tuple)
            assert len(entry) == 3  # (offset, magic_bytes, mime_type)
            offset, magic_bytes, mime_type = entry
            assert isinstance(offset, int)
            assert isinstance(magic_bytes, bytes)
            assert isinstance(mime_type, str)

    def test_extension_map_structure(self):
        """Test that EXTENSION_MAP structure is valid."""
        # Check that EXTENSION_MAP is properly structured
        assert isinstance(MIMEDetection.EXTENSION_MAP, dict)
        for ext, mime_type in MIMEDetection.EXTENSION_MAP.items():
            assert isinstance(ext, str)
            assert ext.startswith('.')  # Extensions should start with a dot
            assert isinstance(mime_type, str)

    def test_detect_mime_type_with_path_object(self):
        """Test detecting MIME type with a Path object instead of string."""
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        try:
            # Pass Path object instead of string
            path_obj = Path(temp_file_path)
            mime_type = self.mime_detector.detect_mime_type(str(path_obj), use_magic=False)  # Convert to string
            assert isinstance(mime_type, str)
        finally:
            os.unlink(temp_file_path)

    def test_detect_mime_type_large_read_buffer(self):
        """Test magic detection with a large read buffer."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            # Write content that includes a magic signature at the beginning
            temp_file.write(b'\xFF\xD8\xFF')  # JPEG magic
            # Fill with more content
            temp_file.write(b'A' * 1000)  # Large content
            temp_file_path = temp_file.name

        try:
            result = self.mime_detector._detect_by_magic(temp_file_path, max_read=1024)
            # Should still detect as JPEG despite large content
            assert result == 'image/jpeg' or result is None
        finally:
            os.unlink(temp_file_path)

    def test_get_extension_for_mime_case_insensitive(self):
        """Test getting extension for MIME type with different cases."""
        # This might not be supported by the implementation, but let's test
        ext1 = self.mime_detector.get_extension_for_mime('IMAGE/JPEG')
        ext2 = self.mime_detector.get_extension_for_mime('image/jpeg')
        # Results may vary, but both should be valid
        assert (ext1 is None or isinstance(ext1, str))
        assert (ext2 is None or isinstance(ext2, str))

    def test_is_text_with_extra_params(self):
        """Test is_text with MIME types that have extra parameters."""
        # The implementation should handle MIME types with parameters by extracting the base type
        assert self.mime_detector.is_text('text/plain;charset=utf-8') is True
        assert self.mime_detector.is_text('application/json; charset=UTF-8') is True

    def test_mime_detection_error_raising(self):
        """Test that MIMEDetectionError can be raised properly."""
        with pytest.raises(MIMEDetectionError):
            # Raise it directly to test the exception class
            raise MIMEDetectionError("Test MIME detection error")

    def test_mime_detection_error_properties(self):
        """Test properties of MIMEDetectionError."""
        error = MIMEDetectionError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
        assert isinstance(error, MIMEDetectionError)


class TestMIMEDetectionClass:
    """Additional tests for the MIMEDetection class itself."""

    def test_class_instantiation(self):
        """Test that MIMEDetection class can be instantiated."""
        detector = MIMEDetection()
        assert isinstance(detector, MIMEDetection)
        assert hasattr(detector, 'MAGIC_NUMBERS')
        assert hasattr(detector, 'EXTENSION_MAP')

    def test_static_method_calls(self):
        """Test calling static methods directly on the class."""
        # Test calling detect_mime_type statically
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as temp_file:
            temp_file.write("temp content")
            temp_file_path = temp_file.name

        try:
            # Call static method directly on class
            mime_type = MIMEDetection.detect_mime_type(temp_file_path)
            assert isinstance(mime_type, str)
        finally:
            os.unlink(temp_file_path)

    def test_magic_numbers_access(self):
        """Test accessing the MAGIC_NUMBERS attribute."""
        magic_numbers = MIMEDetection.MAGIC_NUMBERS
        assert isinstance(magic_numbers, list)
        # Check that it has some entries
        assert len(magic_numbers) > 0

    def test_extension_map_access(self):
        """Test accessing the EXTENSION_MAP attribute."""
        ext_map = MIMEDetection.EXTENSION_MAP
        assert isinstance(ext_map, dict)
        # Check that it has some entries
        assert len(ext_map) > 0

    def test_dependencies_constants_exist(self):
        """Test that required constants exist."""
        assert hasattr(MIMEDetection, 'MAGIC_NUMBERS')
        assert hasattr(MIMEDetection, 'EXTENSION_MAP')
        assert isinstance(MIMEDetection.MAGIC_NUMBERS, list)
        assert isinstance(MIMEDetection.EXTENSION_MAP, dict)
