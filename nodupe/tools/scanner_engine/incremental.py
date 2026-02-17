"""Incremental Module.

Incremental scanning support.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class Incremental:
    """Handle incremental scanning"""

    CHECKPOINT_FILE = ".nodupe_checkpoint.json"

    @staticmethod
    def save_checkpoint(
        scan_path: str,
        processed_files: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """Save incremental scanning checkpoint

        Args:
            scan_path: Path that was scanned
            processed_files: Dictionary of processed files with their metadata
            metadata: Additional checkpoint metadata
        """
        checkpoint_data: dict[str, Any] = {
            "scan_path": scan_path,
            "processed_files": processed_files,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        checkpoint_file = Path(scan_path) / Incremental.CHECKPOINT_FILE
        with open(checkpoint_file, 'w') as f:
            json.dump(
                checkpoint_data,
                f,
                indent=2
            )

    @staticmethod
    def load_checkpoint(scan_path: str) -> Optional[dict[str, Any]]:
        """Load incremental scanning checkpoint

        Args:
            scan_path: Path to look for checkpoint

        Returns:
            Checkpoint data dictionary or None if no checkpoint exists
        """
        checkpoint_file = Path(scan_path) / Incremental.CHECKPOINT_FILE

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file) as f:
                data = json.load(f)
                return dict(data) if isinstance(data, dict) else None
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            # Invalid JSON or corrupted file
            return None

    @staticmethod
    def get_remaining_files(scan_path: str, all_files: list[str]) -> list[str]:
        """Get files that haven't been processed yet

        Args:
            scan_path: Path that was scanned
            all_files: List of all files to process

        Returns:
            List of remaining files to process
        """
        checkpoint = Incremental.load_checkpoint(scan_path)

        if not checkpoint:
            return all_files

        processed_files = set(checkpoint.get("processed_files", {}).keys())
        remaining_files = [f for f in all_files if f not in processed_files]

        return remaining_files

    @staticmethod
    def update_checkpoint(scan_path: str, new_processed_files: dict[str, Any]) -> None:
        """Update existing checkpoint with new processed files

        Args:
            scan_path: Path of the scan
            new_processed_files: New files to add to checkpoint
        """
        existing_checkpoint: Optional[dict[str, Any]] = Incremental.load_checkpoint(scan_path)

        if existing_checkpoint:
            existing_checkpoint["processed_files"].update(new_processed_files)
            existing_checkpoint["timestamp"] = datetime.now().isoformat()
        else:
            existing_checkpoint = {
                "scan_path": scan_path,
                "processed_files": new_processed_files,
                "timestamp": datetime.now().isoformat(),
                "metadata": {}
            }

        checkpoint_file = Path(scan_path) / Incremental.CHECKPOINT_FILE
        with open(checkpoint_file, 'w') as f:
            json.dump(existing_checkpoint, f, indent=2)

    @staticmethod
    def cleanup_checkpoint(scan_path: str) -> bool:
        """Remove checkpoint file

        Args:
            scan_path: Path where checkpoint should be removed

        Returns:
            True if checkpoint was removed, False if no checkpoint existed
        """
        checkpoint_file = Path(scan_path) / Incremental.CHECKPOINT_FILE

        if checkpoint_file.exists():
            checkpoint_file.unlink()
            return True

        return False
