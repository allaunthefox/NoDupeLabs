# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Standard Archive Tool for NoDupeLabs.

Provides archive detection and extraction capabilities as a tool.
"""

from typing import Any

from nodupe.core.tool_system.base import Tool

from .archive_logic import ArchiveHandler


class StandardArchiveTool(Tool):
    """Standard archive handling tool."""

    @property
    def name(self) -> str:
        return "standard_archive"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    @property
    def api_methods(self) -> dict[str, Callable[..., Any]]:
        return {
            "extract_archive": self.handler.extract_archive,
            "create_archive": self.handler.create_archive,
            "is_archive": self.handler.is_archive_file,
            "detect_format": self.handler.detect_archive_format,
        }

    def __init__(self):
        """Initialize the tool."""
        self.handler = ArchiveHandler()

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        container.register_service("archive_handler_service", self.handler)

    def shutdown(self) -> None:
        """Shutdown the tool and cleanup."""
        self.handler.cleanup()

    def run_standalone(self, args: list[str]) -> int:
        """Execute archive operations in stand-alone mode."""
        import argparse

        parser = argparse.ArgumentParser(description=self.describe_usage())
        parser.add_argument(
            "archive", help="The compressed collection (zip/tar)"
        )
        parser.add_argument(
            "--extract", help="The folder where you want the files to go"
        )

        if not args:
            parser.print_help()
            return 0

        parsed = parser.parse_args(args)
        try:
            if parsed.extract:
                res = self.handler.extract_archive(
                    parsed.archive, parsed.extract
                )
                print(f"Success: Put {len(res)} files into {parsed.extract}")
            else:
                fmt = self.handler.detect_archive_format(parsed.archive)
                print(
                    f"Type: {fmt or 'Unknown Collection Type'} for {parsed.archive}"
                )
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def describe_usage(self) -> str:
        """Plain language description."""
        return (
            "This component handles 'collections' of files that have been combined or shrunk. "
            "It can tell you what kind of collection a file is, and it can unpack "
            "those collections so you can see the individual files inside."
        )

    def get_capabilities(self) -> dict[str, Any]:
        """Get tool capabilities."""
        return {
            "formats": [
                "zip",
                "tar",
                "tar.gz",
                "tar.bz2",
                "tar.xz",
                "tar.lzma",
            ],
            "features": ["extraction", "detection", "PASSWORD_REMOVED_support"],
        }


def register_tool():
    """Register the archive tool."""
    return StandardArchiveTool()


if __name__ == "__main__":
    import sys

    tool = StandardArchiveTool()
    sys.exit(tool.run_standalone(sys.argv[1:]))
