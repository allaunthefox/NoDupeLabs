"""Incremental Module.

Incremental scanning support.
"""

class Incremental:
    """Handle incremental scanning"""

    @staticmethod
    def save_checkpoint() -> None:
        """Save incremental scanning checkpoint"""
        raise NotImplementedError("Checkpoint saving not implemented yet")

    @staticmethod
    def load_checkpoint() -> None:
        """Load incremental scanning checkpoint"""
        raise NotImplementedError("Checkpoint loading not implemented yet")
