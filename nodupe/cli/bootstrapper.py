# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""CLI bootstrapper.

Handles dependency initialization and code linting on startup/shutdown.
"""
import atexit
import sys
from pathlib import Path
from typing import Optional


class CLIBootstrapper:
    """Handles CLI startup and shutdown tasks.

    Responsibilities:
    - Dependency auto-installation
    - Startup code linting
    - Shutdown linting registration
    """

    def __init__(self, module_dir: Optional[Path] = None):
        """Initialize bootstrapper.

        Args:
            module_dir: Directory to lint (default: nodupe package)
        """
        if module_dir is None:
            module_dir = Path(__file__).parent.parent
        self.module_dir = module_dir

    def bootstrap(self) -> int:
        """Run startup bootstrap tasks.

        Returns:
            0 on success, non-zero exit code on failure
        """
        # Initialize dependency auto-installer
        from ..deps import init_deps
        init_deps(auto_install=True, silent=False)

        # Startup linting
        from ..bootstrap import lint_tree
        try:
            lint_tree(self.module_dir)
        except SyntaxError as e:
            print(f"[fatal] Startup linting failed: {e}", file=sys.stderr)
            return 10

        # Register shutdown linting
        self._register_shutdown_lint()

        return 0

    def _register_shutdown_lint(self):
        """Register shutdown linting atexit handler."""
        from ..bootstrap import lint_tree
        module_dir = self.module_dir

        def shutdown_lint():
            try:
                lint_tree(module_dir)
            except Exception as e:  # pylint: disable=broad-except
                print(f"[warn] Shutdown linting failed: {e}", file=sys.stderr)

        atexit.register(shutdown_lint)
