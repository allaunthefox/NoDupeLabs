"""Version Management Module.

Handles application version information and compatibility checking.
"""

import sys
from typing import NamedTuple, Optional, Union


class VersionInfo(NamedTuple):
    """Version information tuple."""

    major: int
    minor: int
    micro: int
    releaselevel: str = "final"
    serial: int = 0

    def __str__(self) -> str:
        """Return version string representation."""
        version = f"{self.major}.{self.minor}.{self.micro}"
        if self.releaselevel != "final":
            version += f"{self.releaselevel[0]}{self.serial}"
        return version


# Application version information
__version_info__ = VersionInfo(
    major=1, minor=0, micro=0, releaselevel="final", serial=0
)
__version__ = str(__version_info__)


def get_version() -> str:
    """Get the current application version.

    Returns:
        Current version string (e.g., "1.0.0")
    """
    return __version__


def get_version_info() -> VersionInfo:
    """Get detailed version information.

    Returns:
        VersionInfo tuple containing major, minor, micro, releaselevel, and serial
    """
    return __version_info__


def check_python_version(min_version: tuple = (3, 9)) -> bool:
    """Check if current Python version meets minimum requirements.

    Args:
        min_version: Minimum required Python version as (major, minor) tuple

    Returns:
        True if current Python version meets requirements, False otherwise
    """
    current = sys.version_info[:2]
    return current >= min_version


def get_python_version() -> str:
    """Get current Python version string.

    Returns:
        Python version string (e.g., "3.9.7")
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_python_version_info() -> tuple[int, int, int]:
    """Get current Python version information.

    Returns:
        Tuple containing (major, minor, micro) version numbers
    """
    return (
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )


def is_compatible_version(version_str: str, min_version: str) -> bool:
    """Check if a version string is compatible with minimum version.

    Args:
        version_str: Version string to check (e.g., "1.2.3")
        min_version: Minimum required version string (e.g., "1.0.0")

    Returns:
        True if version_str is >= min_version, False otherwise
    """
    try:
        version_parts = [int(x) for x in version_str.split(".")]
        min_parts = [int(x) for x in min_version.split(".")]

        # Pad with zeros if needed
        while len(version_parts) < 3:
            version_parts.append(0)
        while len(min_parts) < 3:
            min_parts.append(0)

        return tuple(version_parts) >= tuple(min_parts)
    except (ValueError, AttributeError):
        return False


def parse_version(version_str: str) -> Optional[VersionInfo]:
    """Parse a version string into VersionInfo object.

    Args:
        version_str: Version string to parse (e.g., "1.2.3")

    Returns:
        VersionInfo object or None if parsing fails
    """
    try:
        parts = version_str.split(".")
        if len(parts) < 3:
            return None

        major = int(parts[0])
        minor = int(parts[1])
        micro = int(parts[2])

        # Handle pre-release versions like "1.0.0a1" or "1.0.0b2"
        releaselevel = "final"
        serial = 0

        if len(parts) > 3:
            # Handle version with pre-release info
            extra = "".join(parts[3:])
            if "a" in extra:
                releaselevel = "alpha"
                serial = int(extra.replace("a", ""))
            elif "b" in extra:
                releaselevel = "beta"
                serial = int(extra.replace("b", ""))
            elif "rc" in extra:
                releaselevel = "candidate"
                serial = int(extra.replace("rc", ""))
        elif len(parts[2]) > 1 and not parts[2].isdigit():
            # Handle cases like "1.0.0a1" in single part
            micro_part = parts[2]
            if "a" in micro_part:
                micro = int(micro_part.split("a")[0])
                releaselevel = "alpha"
                serial = int(micro_part.split("a")[1])
            elif "b" in micro_part:
                micro = int(micro_part.split("b")[0])
                releaselevel = "beta"
                serial = int(micro_part.split("b")[1])
            elif "rc" in micro_part:
                micro = int(micro_part.split("rc")[0])
                releaselevel = "candidate"
                serial = int(micro_part.split("rc")[1])

        return VersionInfo(major, minor, micro, releaselevel, serial)
    except (ValueError, IndexError):
        return None


def format_version_info(version_info: VersionInfo) -> str:
    """Format VersionInfo object as a readable string.

    Args:
        version_info: VersionInfo object to format

    Returns:
        Formatted version string
    """
    if version_info.releaselevel == "final":
        return (
            f"v{version_info.major}.{version_info.minor}.{version_info.micro}"
        )
    else:
        level_map = {"alpha": "Alpha", "beta": "Beta", "candidate": "RC"}
        level_name = level_map.get(
            version_info.releaselevel, version_info.releaselevel
        )
        return f"v{version_info.major}.{version_info.minor}.{version_info.micro} {level_name} {version_info.serial}"


# Module-level constants
VERSION = __version__
VERSION_INFO = __version_info__
PYTHON_MIN_VERSION = (3, 9)
PYTHON_MIN_VERSION_STR = f"{PYTHON_MIN_VERSION[0]}.{PYTHON_MIN_VERSION[1]}"


def get_system_info() -> (
    dict[str, Union[str, VersionInfo, tuple[int, int], tuple[int, int, int]]]
):
    """Get comprehensive system and version information.

    Returns:
        Dictionary containing version and system information
    """
    import platform

    return {
        "app_version": get_version(),
        "app_version_info": get_version_info(),
        "python_version": get_python_version(),
        "python_version_info": get_python_version_info(),
        "python_min_required": PYTHON_MIN_VERSION_STR,
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
    }


def check_compatibility() -> dict[str, Union[bool, str, list[str]]]:
    """Check overall compatibility status.

    Returns:
        Dictionary with compatibility status information
    """
    python_ok = check_python_version(PYTHON_MIN_VERSION)

    return {
        "python_compatible": python_ok,
        "version": get_version(),
        "python_version": get_python_version(),
        "issues": [] if python_ok else ["Python version requirement not met"],
    }


if __name__ == "__main__":
    # Example usage and testing
    print(f"Application Version: {get_version()}")
    print(f"Python Version: {get_python_version()}")
    print(f"Python Compatible: {check_python_version()}")
    print(f"System Info: {get_system_info()}")
    print(f"Compatibility Check: {check_compatibility()}")
