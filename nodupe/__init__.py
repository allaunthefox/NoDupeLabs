"""Top-level package init. Ensure vendored libs are available on sys.path.

We add `nodupe/vendor/libs` to sys.path so the CLI and library imports can
use bundled fallbacks without requiring global installation.
"""
import sys
from pathlib import Path

_VENDOR_LIBS = Path(__file__).parent / "vendor" / "libs"
if _VENDOR_LIBS.exists():
    sp = str(_VENDOR_LIBS)
    if sp not in sys.path:
        sys.path.insert(0, sp)
