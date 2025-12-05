# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Command router.

Handles command dispatch and error handling.
"""
import sys
from typing import Any, Dict


class CommandRouter:
    """Routes parsed arguments to command handlers.

    Handles:
    - Command dispatch
    - Error handling
    - Plugin lifecycle events
    """

    def __init__(self, plugin_manager: Any = None):
        """Initialize router.

        Args:
            plugin_manager: Optional plugin manager for events
        """
        self.pm = plugin_manager

    def dispatch(self, args: Any, cfg: Dict) -> int:
        """Dispatch to command handler.

        Args:
            args: Parsed CLI arguments
            cfg: Configuration dict

        Returns:
            Exit code (0 = success)
        """
        try:
            # Get handler from args (set by argparse set_defaults)
            handler = getattr(args, '_run', None)
            if handler is None:
                print("[fatal] No command handler found", file=sys.stderr)
                return 1

            rc = handler(args, cfg)

        except KeyboardInterrupt:
            print("\n[fatal] Interrupted by user", file=sys.stderr)
            self._emit("shutdown", reason="interrupt")
            return 130

        except Exception as e:  # pylint: disable=broad-except
            print(f"[fatal] {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            self._emit("shutdown", reason="error", error=e)
            return 10

        self._emit("shutdown", reason="success")
        return rc

    def _emit(self, event: str, **kwargs):
        """Emit plugin event if manager available."""
        if self.pm is not None:
            self.pm.emit(event, **kwargs)
