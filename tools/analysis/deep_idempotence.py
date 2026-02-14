#!/usr/bin/env python3
"""Deep idempotence verification for NoDupeLabs."""
import sys
import subprocess
from pathlib import Path
from typing import Any


class IdempotenceVerifier:
    """Verify operations are idempotent."""
    
    def __init__(self):
        self.results: list[tuple[str, bool, str]] = []
    
    def verify(self, name: str, func: callable) -> bool:
        """Run a verification function."""
        try:
            result = func()
            self.results.append((name, result, ""))
            return result
        except Exception as e:
            self.results.append((name, False, str(e)))
            return False
    
    def print_summary(self) -> None:
        """Print summary of results."""
        print("\n=== Idempotence Summary ===")
        passed = 0
        for name, result, error in self.results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {name}")
            if error:
                print(f"  Error: {error}")
            if result:
                passed += 1
        
        print(f"\nPassed: {passed}/{len(self.results)}")
    
    def run_all(self) -> int:
        """Run all verifications."""
        # Test 1: Import
        def test_import():
            code, _, _ = self._run(['python', '-c', 'import nodupe'])
            return code == 0
        
        # Test 2: Config load
        def test_config():
            code, _, _ = self._run([
                'python', '-c',
                'from nodupe.core.config import Config; c = Config()'
            ])
            return code == 0
        
        # Test 3: Database init twice
        def test_db_init():
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = Path(tmpdir) / "test.db"
                
                # First init
                code1, _, _ = self._run([
                    'python', '-c',
                    f'from nodupe.core.database.database import Database; '
                    f'db = Database("{db_path}"); db.initialize()'
                ])
                
                # Second init (should be idempotent)
                code2, _, _ = self._run([
                    'python', '-c',
                    f'from nodupe.core.database.database import Database; '
                    f'db = Database("{db_path}"); db.initialize()'
                ])
                
                return code1 == 0 and code2 == 0
        
        # Test 4: Plugin loading
        def test_plugins():
            code, _, _ = self._run([
                'python', '-c',
                'from nodupe.core.plugins import PluginRegistry; r = PluginRegistry()'
            ])
            return code == 0
        
        # Test 5: CLI version
        def test_cli():
            code, _, _ = self._run(['python', '-m', 'nodupe', 'version'])
            return code == 0
        
        # Run all tests
        self.verify("Import nodupe", test_import)
        self.verify("Load Config", test_config)
        self.verify("Database Init (idempotent)", test_db_init)
        self.verify("Plugin Registry", test_plugins)
        self.verify("CLI Version", test_cli)
        
        self.print_summary()
        
        return 0 if all(r[1] for r in self.results) else 1
    
    def _run(self, cmd: list[str]) -> tuple[int, str, str]:
        """Run command and return (code, stdout, stderr)."""
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr


def main() -> int:
    """Main entry point."""
    print("=== Deep Idempotence Verification ===")
    verifier = IdempotenceVerifier()
    return verifier.run_all()


if __name__ == '__main__':
    sys.exit(main())
