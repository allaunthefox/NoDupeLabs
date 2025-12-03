# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import json
from pathlib import Path
from datetime import datetime

class JsonlLogger:
    def __init__(self, log_dir: Path, rotate_mb: int = 10, keep: int = 7):
        self.log_dir = Path(log_dir)
        self.rotate_mb = rotate_mb
        self.keep = keep
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log = self.log_dir / "nodupe.log.jsonl"
        self._rotate_if_needed()

    def _rotate_if_needed(self):
        if not self.current_log.exists():
            return
        if self.current_log.stat().st_size > self.rotate_mb * 1024 * 1024:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_log.rename(self.log_dir / f"nodupe.log.{ts}.jsonl")
            self._cleanup()

    def _cleanup(self):
        logs = sorted(self.log_dir.glob("nodupe.log.*.jsonl"))
        while len(logs) > self.keep:
            logs.pop(0).unlink()

    def log(self, level: str, event: str, **kwargs):
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            "data": kwargs
        }
        with self.current_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
