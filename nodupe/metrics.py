# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import json
from pathlib import Path
from datetime import datetime, timezone

class Metrics:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "files_scanned": 0,
            "bytes_scanned": 0,
            "durations": {},
            "meta_exported": 0,
            "meta_errors": 0,
            "duplicates_found": 0,
            "planned_ops": 0,
            "apply": {}
        }

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
