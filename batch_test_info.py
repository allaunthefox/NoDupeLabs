#!/usr/bin/env python3
"""
Batch test information script for NoDupeLabs project.

This script collects and displays comprehensive information about the project's
test suite, plugin system, and compatibility checking functionality.
"""

import sys
import os
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_command(cmd: List[str], cwd: Optional[str] = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr.
    
    Args:
        cmd: Command to run as a list of strings
        cwd: Working directory for the command
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
            check=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr
    except Exception as e:
        return -1, "", str(e)

def check_plugin_system_imports():
    """Check if plugin system imports work correctly."""
    print("=" * 60)
    print("PLUGIN SYSTEM IMPORTS")
    print("=" * 60)
    
    try:
        from nodupe.core.plugin_system.base import Plugin
        from nodupe.core.plugin_system.compatibility import PluginCompatibility
        print("✓ Successfully imported Plugin and PluginCompatibility")
        
        # Test creating a simple plugin
        class TestPlugin(Plugin):
            """Test plugin for compatibility checking.
            
            A simple test plugin used to verify the plugin system and compatibility
            checking functionality works correctly.
            """
            
            @property
            def name(self) -> str:
                return 'test_plugin'
            
            @property
            def version(self) -> str:
                return '1.0.0'
            
            @property
            def dependencies(self) -> list[str]:
                return []
            
            def __init__(self):
                pass
            
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}
        
        plugin = TestPlugin()
        compatibility = PluginCompatibility()
        report = compatibility.check_compatibility(plugin)
        
        print(f"✓ Successfully created and checked plugin compatibility")
        print(f"  Report: {report}")
        
        return True
        
    except Exception as e:
        print(f"✗ Plugin system import failed: {e}")
        traceback.print_exc()
        return False

def run_pytest_tests():
    """Run pytest tests and collect results."""
    print("\n" + "=" * 60)
    print("PYTEST TEST RESULTS")
    print("=" * 60)
    
    # Run pytest with verbose output
    returncode, stdout, stderr = run_command([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v",
        "--tb=short",
        "--no-header"
    ], cwd=str(project_root))
    
    print(f"Exit code: {returncode}")
    if stdout:
        print("STDOUT:")
        print(stdout)
    if stderr:
        print("STDERR:")
        print(stderr)
    
    return returncode == 0

def run_specific_test_file(test_file: str):
    """Run a specific test file."""
    print(f"\n" + "=" * 60)
    print(f"RUNNING: {test_file}")
    print("=" * 60)
    
    returncode, stdout, stderr = run_command([
        sys.executable, "-m", "pytest", 
        test_file, 
        "-v",
        "--tb=short"
    ], cwd=str(project_root))
    
    print(f"Exit code: {returncode}")
    if stdout:
        print("STDOUT:")
        print(stdout)
    if stderr:
        print("STDERR:")
        print(stderr)
    
    return returncode == 0

def check_test_files():
    """Check which test files exist and their status."""
    print("\n" + "=" * 60)
    print("TEST FILES STATUS")
    print("=" * 60)
    
    test_files = [
        "tests/core/test_plugin_compatibility.py",
        "tests/plugins/test_plugin_compatibility.py",
        "tests/core/test_plugins.py",
        "tests/plugins/test_plugin_loader.py",
        "tests/plugins/test_plugin_discovery.py",
        "tests/plugins/test_plugin_lifecycle.py",
        "tests/plugins/test_plugin_hot_reload.py",
        "tests/plugins/test_plugin_registry.py"
    ]
    
    for test_file in test_files:
        path = project_root / test_file
        if path.exists():
            print(f"✓ {test_file}")
        else:
            print(f"✗ {test_file} (not found)")

def check_python_environment():
    """Check Python environment and dependencies."""
    print("\n" + "=" * 60)
    print("PYTHON ENVIRONMENT")
    print("=" * 60)
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    
    # Check if nodupe can be imported
    try:
        import nodupe
        print(f"✓ nodupe module found at: {nodupe.__file__}")
    except ImportError as e:
        print(f"✗ nodupe module not found: {e}")
    
    # Check key dependencies
    dependencies = ['pytest', 'wired', 'attrs', 'typing_extensions']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} available")
        except ImportError:
            print(f"✗ {dep} not available")

def check_git_status():
    """Check git status and recent commits."""
    print("\n" + "=" * 60)
    print("GIT STATUS")
    print("=" * 60)
    
    # Check current branch and status
    returncode, stdout, stderr = run_command(["git", "status", "--short"], cwd=str(project_root))
    if returncode == 0:
        if stdout.strip():
            print("Untracked changes:")
            print(stdout)
        else:
            print("No untracked changes")
    else:
        print(f"Git status failed: {stderr}")
    
    # Check recent commits
    returncode, stdout, stderr = run_command([
        "git", "log", "--oneline", "-5"
    ], cwd=str(project_root))
    if returncode == 0:
        print("Recent commits:")
        print(stdout)
    else:
        print(f"Git log failed: {stderr}")

def main():
    """Main function to run all checks."""
    print("NoDupeLabs Batch Test Information")
    print("=" * 60)
    
    # Check Python environment
    check_python_environment()
    
    # Check git status
    check_git_status()
    
    # Check test files
    check_test_files()
    
    # Check plugin system imports
    plugin_ok = check_plugin_system_imports()
    
    # Run specific test files that are most relevant
    test_files_to_run = [
        "tests/core/test_plugin_compatibility.py",
        "tests/plugins/test_plugin_compatibility.py"
    ]
    
    test_results = {}
    for test_file in test_files_to_run:
        test_path = project_root / test_file
        if test_path.exists():
            test_results[test_file] = run_specific_test_file(test_file)
        else:
            print(f"\nSkipping {test_file} (not found)")
            test_results[test_file] = None
    
    # Try running all tests if plugin system is working
    if plugin_ok:
        print("\n" + "=" * 60)
        print("RUNNING ALL TESTS")
        print("=" * 60)
        all_tests_ok = run_pytest_tests()
    else:
        print("\nSkipping full test run due to plugin system issues")
        all_tests_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Plugin system imports: {'✓' if plugin_ok else '✗'}")
    for test_file, result in test_results.items():
        status = "✓" if result is True else ("✗" if result is False else "~")
        print(f"{test_file}: {status}")
    print(f"All tests: {'✓' if all_tests_ok else '✗'}")
    
    # Determine exit code
    EXIT_CODE = 0
    if not plugin_ok:
        EXIT_CODE = 1
    if not all_tests_ok:
        EXIT_CODE = 1
    
    return EXIT_CODE

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
