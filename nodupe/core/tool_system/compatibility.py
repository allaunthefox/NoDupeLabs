"""Tool Compatibility Module.

Tool compatibility checking using standard library only.

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation

Key Features:
    - Python version compatibility checking
    - Dependency version validation
    - Tool API compatibility verification
    - Forward and backward compatibility management
    - Standard library only (no external dependencies)

Dependencies:
    - sys (standard library)
    - typing (standard library)
    - packaging (if available, otherwise manual version parsing)
"""

import re
import sys
from typing import Any, Optional

from nodupe.core.tool_system.base import Tool


class CompatibilityError(Exception):
    """Tool compatibility error"""


class CompatibilityChecker:
    """Handle tool compatibility checking.

    Checks Python version compatibility, dependency versions,
    and API compatibility between tools.
    """

    def __init__(self):
        """Initialize compatibility checker."""
        self._python_version = sys.version_info
        self._supported_versions = [
            (3, 9),
            (3, 10),
            (3, 11),
            (3, 12),
            (3, 13),
            (3, 14),
        ]
        self._api_versions: dict[str, str] = {}
        self._dependency_constraints: dict[str, str] = {}

    def check_python_compatibility(
        self,
        required_version: Optional[tuple[int, ...]] = None,
        min_version: Optional[tuple[int, ...]] = None,
        max_version: Optional[tuple[int, ...]] = None,
    ) -> tuple[bool, str]:
        """Check Python version compatibility.

        Args:
            required_version: Exact Python version required (major, minor)
            min_version: Minimum Python version required (major, minor)
            max_version: Maximum Python version allowed (major, minor)

        Returns:
            Tuple of (is_compatible, reason_message)
        """
        current = self._python_version

        # Check exact version requirement
        if (
            required_version
            and (current.major, current.minor) != required_version
        ):
            return False, (
                f"Requires Python {required_version[0]}.{required_version[1]}, "
                f"running {current.major}.{current.minor}"
            )

        # Check minimum version
        if min_version and (current.major, current.minor) < min_version:
            return False, (
                f"Requires Python {min_version[0]}.{min_version[1]}+, "
                f"running {current.major}.{current.minor}"
            )

        # Check maximum version
        if max_version and (current.major, current.minor) > max_version:
            return False, (
                f"Maximum Python {max_version[0]}.{max_version[1]} supported, "
                f"running {current.major}.{current.minor}"
            )

        return True, f"Compatible with Python {current.major}.{current.minor}"

    def check_dependency_compatibility(
        self,
        dependency_name: str,
        required_version: Optional[str] = None,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Check dependency version compatibility.

        Args:
            dependency_name: Name of dependency to check
            required_version: Exact version required
            min_version: Minimum version required
            max_version: Maximum version allowed

        Returns:
            Tuple of (is_compatible, reason_message)
        """
        try:
            # Import the dependency to check its version
            module = __import__(dependency_name)
            if hasattr(module, "__version__"):
                installed_version = module.__version__
            elif hasattr(module, "VERSION"):
                installed_version = str(module.VERSION)
            else:
                return (
                    True,
                    f"Cannot determine version for {dependency_name}, assuming compatible",
                )

            # Parse versions
            if required_version and not self._version_matches(
                installed_version, required_version
            ):
                return (
                    False,
                    f"{dependency_name} {installed_version} does not match required {required_version}",
                )

            if min_version and not self._version_satisfies_min(
                installed_version, min_version
            ):
                return (
                    False,
                    f"{dependency_name} {installed_version} below minimum {min_version}",
                )

            if max_version and not self._version_satisfies_max(
                installed_version, max_version
            ):
                return (
                    False,
                    f"{dependency_name} {installed_version} exceeds maximum {max_version}",
                )

            return (
                True,
                f"Compatible with {dependency_name} {installed_version}",
            )

        except ImportError:
            if required_version or min_version:
                return (
                    False,
                    f"Required dependency {dependency_name} not installed",
                )
            return True, f"Optional dependency {dependency_name} not installed"

        except Exception as e:
            return True, f"Could not check {dependency_name} version: {e}"

    def check_api_compatibility(
        self,
        tool_name: str,
        required_api_version: str,
        current_api_version: str,
    ) -> tuple[bool, str]:
        """Check API compatibility between tool and host.

        Args:
            tool_name: Name of tool
            required_api_version: API version tool requires
            current_api_version: Current API version of host

        Returns:
            Tuple of (is_compatible, reason_message)
        """
        if not self._api_version_compatible(
            required_api_version, current_api_version
        ):
            return (
                False,
                f"{tool_name} requires API {required_api_version}, host provides {current_api_version}",
            )

        return True, (
            f"API compatible with {tool_name} "
            f"(host: {current_api_version}, required: {required_api_version})"
        )

    def check_tool_compatibility(
        self, tool_info: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Check overall tool compatibility.

        Args:
            tool_info: Dictionary containing tool compatibility info
                        Expected keys: 'name', 'python_version', 'dependencies', 'api_version'

        Returns:
            Tuple of (is_compatible, list_of_issues)
        """
        issues: list[str] = []

        # Check Python version compatibility
        if "python_version" in tool_info:
            req_version = tool_info["python_version"]
            if isinstance(req_version, str):
                try:
                    major, minor = map(int, req_version.split(".")[:2])
                    req_tuple = (major, minor)
                    is_compat, msg = self.check_python_compatibility(
                        required_version=req_tuple
                    )
                    if not is_compat:
                        issues.append(msg)
                except ValueError:
                    issues.append(
                        f"Invalid Python version format: {req_version}"
                    )
            elif isinstance(req_version, tuple):
                is_compat, msg = self.check_python_compatibility(
                    required_version=req_version
                )  # type: ignore
                if not is_compat:
                    issues.append(msg)

        # Check dependencies
        if "dependencies" in tool_info:
            deps = tool_info["dependencies"]
            if isinstance(deps, dict):
                # Cast to proper dict type for type checking
                typed_deps = deps
                deps_dict: dict[str, str] = {}
                for item_key, item_value in typed_deps.items():
                    try:
                        key_str: str = (
                            str(item_key) if item_key is not None else ""
                        )
                        value_str: str = (
                            str(item_value) if item_value is not None else ""
                        )
                        deps_dict[key_str] = value_str
                    except (TypeError, ValueError):
                        # Skip items that can't be converted to strings
                        continue
                for dep_name, version_constraint in deps_dict.items():
                    if version_constraint.startswith(">="):
                        min_ver = version_constraint[2:]
                        is_compat, msg = self.check_dependency_compatibility(
                            dep_name, min_version=min_ver
                        )
                        if not is_compat:
                            issues.append(msg)
                    elif version_constraint.startswith("<="):
                        max_ver = version_constraint[2:]
                        is_compat, msg = self.check_dependency_compatibility(
                            dep_name, max_version=max_ver
                        )
                        if not is_compat:
                            issues.append(msg)
                    elif version_constraint.startswith("=="):
                        exact_ver = version_constraint[2:]
                        is_compat, msg = self.check_dependency_compatibility(
                            dep_name, required_version=exact_ver
                        )
                        if not is_compat:
                            issues.append(msg)
                    else:
                        # Assume it's a version constraint
                        is_compat, msg = self.check_dependency_compatibility(
                            dep_name, min_version=version_constraint
                        )
                        if not is_compat:
                            issues.append(msg)

        # Check API compatibility
        if "api_version" in tool_info and "current_api_version" in tool_info:
            tool_name = tool_info.get("name", "unknown")
            is_compat, msg = self.check_api_compatibility(
                tool_name,
                tool_info["api_version"],
                tool_info["current_api_version"],
            )
            if not is_compat:
                issues.append(msg)

        return len(issues) == 0, issues

    def register_api_version(self, tool_name: str, api_version: str) -> None:
        """Register an API version for a tool.

        Args:
            tool_name: Name of tool
            api_version: API version string
        """
        self._api_versions[tool_name] = api_version

    def register_dependency_constraint(
        self, dependency_name: str, constraint: str
    ) -> None:
        """Register a dependency version constraint.

        Args:
            dependency_name: Name of dependency
            constraint: Version constraint string
        """
        self._dependency_constraints[dependency_name] = constraint

    def get_supported_python_versions(self) -> list[tuple[int, int]]:
        """Get list of supported Python versions.

        Returns:
            List of supported (major, minor) version tuples
        """
        return self._supported_versions.copy()

    def is_version_compatible(
        self, version1: str, version2: str, tolerance: str = "patch"
    ) -> bool:
        """Check if two versions are compatible within tolerance.

        Args:
            version1: First version string
            version2: Second version string
            tolerance: Level of tolerance ('major', 'minor', 'patch')

        Returns:
            True if versions are compatible within tolerance
        """
        try:
            v1_parts = self._parse_version(version1)
            v2_parts = self._parse_version(version2)

            if tolerance == "major":
                return v1_parts[0] == v2_parts[0]
            elif tolerance == "minor":
                return v1_parts[:2] == v2_parts[:2]
            elif tolerance == "patch":
                return v1_parts[:3] == v2_parts[:3]
            else:
                return False

        except Exception:
            return False

    def _version_matches(self, installed: str, required: str) -> bool:
        """Check if installed version matches required version.

        Args:
            installed: Installed version string
            required: Required version string

        Returns:
            True if versions match
        """
        if required.startswith("=="):
            required = required[2:]

        installed_parts = self._parse_version(installed)
        required_parts = self._parse_version(required)

        # Compare up to the length of required version
        return installed_parts[: len(required_parts)] == required_parts

    def _version_satisfies_min(self, installed: str, minimum: str) -> bool:
        """Check if installed version satisfies minimum version.

        Args:
            installed: Installed version string
            minimum: Minimum version string

        Returns:
            True if installed >= minimum
        """
        if minimum.startswith(">="):
            minimum = minimum[2:]

        installed_parts = self._parse_version(installed)
        min_parts = self._parse_version(minimum)

        for i in range(min(len(installed_parts), len(min_parts))):
            if installed_parts[i] > min_parts[i]:
                return True
            elif installed_parts[i] < min_parts[i]:
                return False

        # If all compared parts are equal, installed version should be at least as long
        return len(installed_parts) >= len(min_parts)

    def _version_satisfies_max(self, installed: str, maximum: str) -> bool:
        """Check if installed version satisfies maximum version.

        Args:
            installed: Installed version string
            maximum: Maximum version string

        Returns:
            True if installed <= maximum
        """
        if maximum.startswith("<="):
            maximum = maximum[2:]

        installed_parts = self._parse_version(installed)
        max_parts = self._parse_version(maximum)

        for i in range(min(len(installed_parts), len(max_parts))):
            if installed_parts[i] < max_parts[i]:
                return True
            elif installed_parts[i] > max_parts[i]:
                return False

        # If all compared parts are equal, installed version should not be longer
        return len(installed_parts) <= len(max_parts)

    def _api_version_compatible(self, required: str, current: str) -> bool:
        """Check if API versions are compatible.

        Args:
            required: Required API version
            current: Current API version

        Returns:
            True if API versions are compatible
        """
        # For API compatibility, we typically want same major version
        req_parts = self._parse_version(required)
        cur_parts = self._parse_version(current)

        # Same major version is typically required for API compatibility
        return (
            req_parts[0] == cur_parts[0] if req_parts and cur_parts else False
        )

    def _parse_version(self, version_str: str) -> list[int]:
        """Parse version string into integer parts.

        Args:
            version_str: Version string to parse

        Returns:
            List of integer version parts
        """
        # Remove any pre-release or build metadata
        clean_version = re.split(r"[-+]", version_str)[0]
        # Split on dots and convert to integers
        parts: list[int] = []
        for part in clean_version.split("."):
            try:
                parts.append(int(part))
            except ValueError:
                # Stop at first non-numeric part
                break
        return parts


def create_compatibility_checker() -> CompatibilityChecker:
    """Create a compatibility checker instance.

    Returns:
        CompatibilityChecker instance
    """
    return CompatibilityChecker()


class ToolCompatibilityError(Exception):
    """Tool compatibility error exception."""

    pass


class ToolCompatibility:
    """Tool compatibility checker with tool-specific functionality.

    Provides compatibility checking for tools, including interface validation,
    dependency checking, and lifecycle management.
    """

    def __init__(self):
        """Initialize tool compatibility checker."""
        self.container = None
        self._checker = CompatibilityChecker()

    def check_compatibility(self, tool):
        """Check tool compatibility.

        Args:
            tool: Tool instance to check

        Returns:
            Dictionary with compatibility information
        """
        if not isinstance(tool, Tool):
            raise ToolCompatibilityError(
                "Tool must inherit from Tool base class"
            )

        if not hasattr(tool, "name") or not tool.name:
            raise ToolCompatibilityError("Tool must have a valid name")

        if not hasattr(tool, "version"):
            raise ToolCompatibilityError("Tool must have a version")

        if not hasattr(tool, "dependencies"):
            raise ToolCompatibilityError("Tool must have dependencies")

        # Check required methods
        required_methods = ["initialize", "shutdown", "get_capabilities"]
        for method in required_methods:
            if not hasattr(tool, method):
                raise ToolCompatibilityError(
                    f"Tool must implement {method} method"
                )

        # Create compatibility report
        report = {"compatible": True, "issues": [], "warnings": []}

        # Check tool attributes
        if not tool.name.strip():
            report["compatible"] = False
            report["issues"].append("Tool name cannot be empty")

        # Check version format
        try:
            self._parse_version(tool.version)
        except Exception:
            report["compatible"] = False
            report["issues"].append(f"Invalid version format: {tool.version}")

        # Check dependencies
        if not isinstance(tool.dependencies, list):
            report["compatible"] = False
            report["issues"].append("Dependencies must be a list")

        return report

    def get_compatibility_report(self, tool):
        """Get detailed compatibility report for a tool.

        Args:
            tool: Tool instance to analyze

        Returns:
            Dictionary with detailed compatibility report
        """
        if not isinstance(tool, Tool):
            raise ToolCompatibilityError(
                "Tool must inherit from Tool base class"
            )

        report = {
            "tool_name": getattr(tool, "name", "unknown"),
            "tool_version": getattr(tool, "version", "unknown"),
            "compatibility_status": "unknown",
            "compatibility_issues": [],
            "compatibility_warnings": [],
        }

        # Basic validation
        if not hasattr(tool, "name") or not tool.name:
            report["compatibility_status"] = "incompatible"
            report["compatibility_issues"].append("Tool must have a valid name")
            return report

        if not hasattr(tool, "version"):
            report["compatibility_status"] = "incompatible"
            report["compatibility_issues"].append("Tool must have a version")
            return report

        if not hasattr(tool, "dependencies"):
            report["compatibility_status"] = "incompatible"
            report["compatibility_issues"].append("Tool must have dependencies")
            return report

        # Check required methods
        required_methods = ["initialize", "shutdown", "get_capabilities"]
        for method in required_methods:
            if not hasattr(tool, method):
                report["compatibility_status"] = "incompatible"
                report["compatibility_issues"].append(
                    f"Tool must implement {method} method"
                )

        # If we got here, basic checks passed
        if not report["compatibility_issues"]:
            report["compatibility_status"] = "compatible"

        return report

    def initialize(self, container):
        """Initialize compatibility checker with container.

        Args:
            container: Service container instance
        """
        self.container = container

    def shutdown(self):
        """Shutdown compatibility checker."""
        self.container = None

    def _parse_version(self, version_str):
        """Parse version string into components.

        Args:
            version_str: Version string to parse

        Returns:
            List of version components
        """
        if not version_str:
            raise ValueError("Version string cannot be empty")

        parts = []
        for part in version_str.split("."):
            try:
                parts.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid version part: {part}")

        if len(parts) < 2:
            raise ValueError("Version must have at least major.minor format")

        return parts
