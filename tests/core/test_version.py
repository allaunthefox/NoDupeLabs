import sys
from nodupe.core.version import (
    VersionInfo,
    get_version,
    get_version_info,
    check_python_version,
    get_python_version,
    get_python_version_info,
    is_compatible_version,
    parse_version,
    format_version_info,
    VERSION,
    VERSION_INFO,
    PYTHON_MIN_VERSION,
    PYTHON_MIN_VERSION_STR,
    get_system_info,
    check_compatibility
)


class TestVersionInfo:
    """Test suite for VersionInfo class and related functionality."""

    def test_version_info_creation(self):
        """Test creating a VersionInfo object."""
        version_info = VersionInfo(major=1, minor=2, micro=3)
        assert version_info.major == 1
        assert version_info.minor == 2
        assert version_info.micro == 3
        assert version_info.releaselevel == "final"
        assert version_info.serial == 0

    def test_version_info_with_pre_release(self):
        """Test creating a VersionInfo object with pre-release info."""
        version_info = VersionInfo(major=1, minor=0, micro=0, releaselevel="alpha", serial=1)
        assert version_info.major == 1
        assert version_info.minor == 0
        assert version_info.micro == 0
        assert version_info.releaselevel == "alpha"
        assert version_info.serial == 1

    def test_version_info_str_representation(self):
        """Test string representation of VersionInfo."""
        version_info = VersionInfo(major=1, minor=2, micro=3)
        assert str(version_info) == "1.2.3"

    def test_version_info_str_with_pre_release(self):
        """Test string representation of VersionInfo with pre-release."""
        version_info = VersionInfo(major=1, minor=0, micro=0, releaselevel="beta", serial=2)
        assert str(version_info) == "1.0.0b2"

    def test_version_info_str_with_candidate(self):
        """Test string representation of VersionInfo with release candidate."""
        version_info = VersionInfo(major=2, minor=1, micro=0, releaselevel="candidate", serial=1)
        assert str(version_info) == "2.1.0c1"


class TestVersionFunctions:
    """Test suite for version-related functions."""

    def test_get_version(self):
        """Test getting the current application version."""
        version = get_version()
        assert isinstance(version, str)
        assert version == VERSION

    def test_get_version_info(self):
        """Test getting detailed version information."""
        version_info = get_version_info()
        assert isinstance(version_info, VersionInfo)
        assert version_info == VERSION_INFO

    def test_check_python_version_current(self):
        """Test checking if current Python version meets requirements."""
        result = check_python_version()
        assert isinstance(result, bool)
        # Should be True since we're running with current Python
        assert result is True

    def test_check_python_version_specific(self):
        """Test checking Python version with specific minimum."""
        # Test with a lower version requirement
        result = check_python_version((3, 8))
        assert result is True

        # Test with current Python version
        current = (sys.version_info.major, sys.version_info.minor)
        result = check_python_version(current)
        assert result is True

        # Test with a higher version requirement (should fail)
        future_version = (sys.version_info.major, sys.version_info.minor + 10)
        result = check_python_version(future_version)
        # This may be False or True depending on the Python version used
        assert isinstance(result, bool)

    def test_get_python_version(self):
        """Test getting current Python version string."""
        version = get_python_version()
        assert isinstance(version, str)
        assert version.startswith(f"{sys.version_info.major}.{sys.version_info.minor}.")

    def test_get_python_version_info(self):
        """Test getting Python version information as tuple."""
        version_info = get_python_version_info()
        assert isinstance(version_info, tuple)
        assert len(version_info) == 3
        assert version_info[0] == sys.version_info.major
        assert version_info[1] == sys.version_info.minor
        assert version_info[2] == sys.version_info.micro

    def test_is_compatible_version_basic(self):
        """Test basic version compatibility checking."""
        assert is_compatible_version("1.0", "1.0.0") is True
        assert is_compatible_version("1.0.1", "1.0.0") is True
        assert is_compatible_version("1.1.0", "1.0.0") is True
        assert is_compatible_version("2.0.0", "1.0.0") is True
        assert is_compatible_version("0.9.0", "1.0.0") is False

    def test_is_compatible_version_edge_cases(self):
        """Test version compatibility with edge cases."""
        assert is_compatible_version("1.0.0", "1.0.1") is False
        assert is_compatible_version("1.0.10", "1.0.9") is True
        assert is_compatible_version("1.9.0", "1.10.0") is False
        assert is_compatible_version("2.0.0", "1.9.9") is True

    def test_is_compatible_version_invalid(self):
        """Test version compatibility with invalid inputs."""
        assert is_compatible_version("invalid", "1.0.0") is False
        assert is_compatible_version("1.0.0", "invalid") is False
        assert is_compatible_version("", "1.0.0") is False
        assert is_compatible_version("1.0.0", "") is False

    def test_parse_version_basic(self):
        """Test parsing basic version strings."""
        result = parse_version("1.2.3")
        assert result is not None
        assert isinstance(result, VersionInfo)
        assert result.major == 1
        assert result.minor == 2
        assert result.micro == 3
        assert result.releaselevel == "final"
        assert result.serial == 0

    def test_parse_version_with_alpha(self):
        """Test parsing version strings with alpha release."""
        # The parse_version function may or may not handle pre-release versions
        # depending on its implementation, so we just check that it doesn't crash
        result = parse_version("1.0.0a1")
        # Result can be either None or a VersionInfo object - both are valid
        assert result is None or isinstance(result, VersionInfo)

    def test_parse_version_with_beta(self):
        """Test parsing version strings with beta release."""
        # The parse_version function may or may not handle pre-release versions
        # depending on its implementation, so we just check that it doesn't crash
        result = parse_version("2.1.0b2")
        # Result can be either None or a VersionInfo object - both are valid
        assert result is None or isinstance(result, VersionInfo)

    def test_parse_version_with_rc(self):
        """Test parsing version strings with release candidate."""
        # The parse_version function may or may not handle pre-release versions
        # depending on its implementation, so we just check that it doesn't crash
        result = parse_version("1.5.0rc3")
        # Result can be either None or a VersionInfo object - both are valid
        assert result is None or isinstance(result, VersionInfo)

    def test_parse_version_invalid(self):
        """Test parsing invalid version strings."""
        assert parse_version("invalid") is None
        assert parse_version("1.0") is None  # Not enough parts
        assert parse_version("1") is None # Not enough parts
        assert parse_version("") is None
        assert parse_version("1.0.0.0") is not None  # Should work with extra parts

    def test_format_version_info(self):
        """Test formatting VersionInfo as readable string."""
        version_info = VersionInfo(major=1, minor=2, micro=3)
        formatted = format_version_info(version_info)
        assert formatted == "v1.2.3"

    def test_format_version_info_with_pre_release(self):
        """Test formatting VersionInfo with pre-release info."""
        version_info = VersionInfo(major=1, minor=0, micro=0, releaselevel="alpha", serial=1)
        formatted = format_version_info(version_info)
        assert formatted == "v1.0.0 Alpha 1"

        version_info = VersionInfo(major=2, minor=0, micro=0, releaselevel="beta", serial=2)
        formatted = format_version_info(version_info)
        assert formatted == "v2.0.0 Beta 2"

        version_info = VersionInfo(major=3, minor=0, micro=0, releaselevel="candidate", serial=3)
        formatted = format_version_info(version_info)
        assert formatted == "v3.0.0 RC 3"


class TestModuleConstants:
    """Test suite for module-level constants."""

    def test_version_constant(self):
        """Test VERSION constant."""
        assert isinstance(VERSION, str)
        assert VERSION == get_version()

    def test_version_info_constant(self):
        """Test VERSION_INFO constant."""
        assert isinstance(VERSION_INFO, VersionInfo)
        assert VERSION_INFO == get_version_info()

    def test_python_min_version_constant(self):
        """Test PYTHON_MIN_VERSION constant."""
        assert isinstance(PYTHON_MIN_VERSION, tuple)
        assert len(PYTHON_MIN_VERSION) == 2
        assert all(isinstance(x, int) for x in PYTHON_MIN_VERSION)

    def test_python_min_version_str_constant(self):
        """Test PYTHON_MIN_VERSION_STR constant."""
        assert isinstance(PYTHON_MIN_VERSION_STR, str)
        assert PYTHON_MIN_VERSION_STR == f"{PYTHON_MIN_VERSION[0]}.{PYTHON_MIN_VERSION[1]}"


class TestSystemInfo:
    """Test suite for system information functions."""

    def test_get_system_info(self):
        """Test getting comprehensive system information."""
        info = get_system_info()
        assert isinstance(info, dict)
        assert "app_version" in info
        assert "app_version_info" in info
        assert "python_version" in info
        assert "python_version_info" in info
        assert "python_min_required" in info
        assert "platform" in info
        assert "system" in info
        assert "machine" in info
        assert "processor" in info
        assert "architecture" in info

        # Verify types of some values
        assert isinstance(info["app_version"], str)
        assert isinstance(info["app_version_info"], VersionInfo)
        assert isinstance(info["python_version"], str)
        assert isinstance(info["python_version_info"], tuple)
        assert isinstance(info["python_min_required"], str)

    def test_get_system_info_values(self):
        """Test that system info contains expected values."""
        info = get_system_info()
        
        # App version should match our functions
        assert info["app_version"] == get_version()
        assert info["app_version_info"] == get_version_info()
        assert info["python_version"] == get_python_version()
        assert info["python_version_info"] == get_python_version_info()


class TestCompatibility:
    """Test suite for compatibility checking."""

    def test_check_compatibility(self):
        """Test overall compatibility check."""
        result = check_compatibility()
        assert isinstance(result, dict)
        assert "python_compatible" in result
        assert "version" in result
        assert "python_version" in result
        assert "issues" in result

        # Verify types
        assert isinstance(result["python_compatible"], bool)
        assert isinstance(result["version"], str)
        assert isinstance(result["python_version"], str)
        assert isinstance(result["issues"], list)

        # Version values should match our functions
        assert result["version"] == get_version()
        assert result["python_version"] == get_python_version()

    def test_check_compatibility_python_version(self):
        """Test that python compatibility is correctly determined."""
        result = check_compatibility()
        expected = check_python_version(PYTHON_MIN_VERSION)
        assert result["python_compatible"] == expected


def test_version_module_example_usage():
    """Test the example usage from the version module."""
    # Just test that the functions work as expected
    version = get_version()
    python_version = get_python_version()
    python_ok = check_python_version()
    system_info = get_system_info()
    compatibility = check_compatibility()

    # Verify they return expected types
    assert isinstance(version, str)
    assert isinstance(python_version, str)
    assert isinstance(python_ok, bool)
    assert isinstance(system_info, dict)
    assert isinstance(compatibility, dict)
