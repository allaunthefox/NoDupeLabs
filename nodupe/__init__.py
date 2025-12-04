"""Top-level package init. Ensure vendored libs are available on sys.path.

We add `nodupe/vendor/libs` to sys.path so the CLI and library imports can
use bundled fallbacks without requiring global installation.

Public API:
    Core Operations:
        - scanner: File scanning and hashing
        - planner: Deduplication planning
        - applier: Plan execution
        - rollback: Operation reversal

    Database:
        - db.DB: Database class

    Utilities:
        - config: Configuration management
        - categorizer: File categorization
        - nsfw_classifier: NSFW content detection

    Subsystems:
        - similarity: Similarity search
        - ai.backends: AI backend selection
        - plugins: Plugin system
        - commands: CLI command implementations
"""
import sys
from pathlib import Path

_VENDOR_LIBS = Path(__file__).parent / "vendor" / "libs"
if _VENDOR_LIBS.exists():
    sp = str(_VENDOR_LIBS)
    if sp not in sys.path:
        sys.path.insert(0, sp)

# Version
__version__ = "0.1.0"

# Public API - Core modules
__all__ = [
    # Version
    "__version__",
    # Core operation modules
    "scanner",
    "planner",
    "applier",
    "rollback",
    # Database
    "db",
    # Configuration & utilities
    "config",
    "categorizer",
    "nsfw_classifier",
    "exporter",
    # Subsystems (packages)
    "similarity",
    "ai",
    "plugins",
    "commands",
    "utils",
]
