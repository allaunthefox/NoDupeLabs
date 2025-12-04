# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import sys
from ..archiver import ArchiveHandler

def cmd_archive_list(args, _cfg):
    try:
        h = ArchiveHandler(args.file)
        print(f"Archive Type: {h.type}")
        for item in h.list_contents():
            print(f"{item['size']:>12} {item['path']}")
        return 0
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def cmd_archive_extract(args, _cfg):
    try:
        h = ArchiveHandler(args.file)
        h.extract(args.dest)
        print("Extraction complete.")
        return 0
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
