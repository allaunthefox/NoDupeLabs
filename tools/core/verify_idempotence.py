#!/usr/bin/env python3
"""Idempotence verification for NoDupeLabs operations."""
import sys
import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def verify_import() -> bool:
    """Verify all imports work (idempotent)."""
    print("=== Idempotence: Import Check ===")
    code, out, err = run_command(['python', '-c', 'import nodupe'])
    if code == 0:
        print("PASS: All imports successful")
        return True
    print(f"FAIL: Import error: {err}")
    return False


def verify_config_load() -> bool:
    """Verify config loads (idempotent)."""
    print("\n=== Idempotence: Config Load ===")
    code, out, err = run_command(['python', '-c', 
        'from nodupe.core.config import Config; c = Config(); print("OK")'])
    if code == 0:
        print("PASS: Config loads")
        return True
    print(f"FAIL: Config error: {err}")
    return False


def verify_database_init() -> bool:
    """Verify database initializes (idempotent)."""
    print("\n=== Idempotence: Database Init ===")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        code, out, err = run_command([
            'python', '-c',
            f'from nodupe.core.database.database import Database; '
            f'db = Database("{db_path}"); db.initialize()'
        ])
        if code == 0:
            # Run again to verify idempotence
            code2, out2, err2 = run_command([
                'python', '-c',
                f'from nodupe.core.database.database import Database; '
                f'db = Database("{db_path}"); db.initialize()'
            ])
            if code2 == 0:
                print("PASS: Database init is idempotent")
                return True
        print(f"FAIL: Database error: {err or err2}")
    return False


def main() -> int:
    """Run idempotence checks."""
    print("=== Idempotence Verification ===\n")
    
    checks = [
        ("Import", verify_import),
        ("Config Load", verify_config_load),
        ("Database Init", verify_database_init),
    ]
    
    results = []
    for name, check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"ERROR in {name}: {e}")
            results.append(False)
    
    print("\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
