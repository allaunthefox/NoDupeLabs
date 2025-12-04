# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

from pathlib import Path
from ..rollback import rollback_from_checkpoint

def cmd_rollback(args, _cfg):
    res = rollback_from_checkpoint(Path(args.checkpoint))
    print(f"[rollback] {res}")
    return 0 if res["errors"] == 0 else 1
