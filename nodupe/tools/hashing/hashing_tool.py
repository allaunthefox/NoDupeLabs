# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Standard Hashing Tool for NoDupeLabs.

Provides cryptographic hashing capabilities as a tool.
"""

import os
import sys
from typing import Any, Callable


# Standard High-Assurance Import Pattern for standalone tools
try:
    from nodupe.core.tool_system.base import Tool, ToolMetadata

    from .hasher_logic import FileHasher
except (ImportError, ValueError):
    # Stand-alone mode: resolve parent paths manually
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from nodupe.core.tool_system.base import Tool, ToolMetadata
    from nodupe.tools.hashing.hasher_logic import FileHasher

class StandardHashingTool(Tool):
    """Standard hashing tool using hashlib (ISO/IEC 10118-3 Compliant)."""

    @property
    def name(self) -> str:
        return "hashing_standard"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        """Tool dependencies."""
        return []

    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata (ISO 19770-2 compliant)."""
        return ToolMetadata(
            name=self.name,
            version=self.version,
            software_id=f"org.nodupe.tool.{self.name.lower()}",
            description="Cryptographic hashing aspect compliant with ISO/IEC 10118-3:2018",
            author="NoDupeLabs",
            license="Apache-2.0",
            dependencies=self.dependencies,
            tags=["security", "hashing", "integrity", "ISO-10118-3"]
        )

    @property
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        return {
            'hash_file': self.hasher.hash_file,
            'hash_string': self.hasher.hash_string,
            'hash_bytes': self.hasher.hash_bytes,
            'get_algorithms': self.hasher.get_available_algorithms,
            'check_iso_compliance': self.check_iso_compliance
        }

    def __init__(self):
        """Initialize the tool."""
        self.hasher = FileHasher()

    def check_iso_compliance(self, algorithm: str) -> dict[str, Any]:
        """Verify if an algorithm is standardized under ISO/IEC 10118-3."""
        iso_algorithms = {
            "sha224", "sha256", "sha384", "sha512",
            "sha512_224", "sha512_256",
            "sha3-224", "sha3-256", "sha3-384", "sha3-512",
            "shake128", "shake256",
            "ripemd160", "whirlpool"
        }
        normalized = algorithm.lower().replace("-", "")
        is_compliant = normalized in [a.replace("-", "") for a in iso_algorithms]
        return {
            "algorithm": algorithm,
            "is_iso_compliant": is_compliant,
            "standard": "ISO/IEC 10118-3:2018" if is_compliant else "N/A"
        }

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        container.register_service('hasher_service', self.hasher)

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def run_standalone(self, args: list[str]) -> int:
        """Execute hashing in stand-alone mode."""
        import argparse
        parser = argparse.ArgumentParser(description=self.describe_usage())
        parser.add_argument("file", help="The file you want to verify")
        parser.add_argument("--algo", default="sha256", help="The math rule to use (default: sha256)")

        if not args:
            parser.print_help()
            return 0

        parsed = parser.parse_args(args)
        try:
            self.hasher.set_algorithm(parsed.algo)
            result = self.hasher.hash_file(parsed.file)
            print(f"Digital Fingerprint: {result}")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def describe_usage(self) -> str:
        """Plain language description."""
        return (
            "This component creates a unique 'digital fingerprint' for a file. "
            "If the file changes by even one letter, this fingerprint will change. "
            "It is used to prove that a backup is an exact copy of the original."
        )

    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities."""
        return {
            'algorithms': self.hasher.get_available_algorithms(),
            'features': ['file_hashing', 'string_hashing', 'byte_hashing']
        }

def register_tool():
    """Register the hashing tool."""
    return StandardHashingTool()

if __name__ == "__main__":
    plugin = StandardHashingTool()
    sys.exit(plugin.run_standalone(sys.argv[1:]))
