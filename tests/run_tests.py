#!/usr/bin/env python3
"""
Test runner for NoDupeLabs.
"""
import subprocess
import sys
from pathlib import Path


def run_tests(test_pattern=None, verbose=True, coverage=True):
    """
    Run tests with optional pattern matching.

    Args:
        test_pattern (str): Pattern to match test files/names
        verbose (bool): Whether to show verbose output
        coverage (bool): Whether to generate coverage report
    """
    cmd = ["python", "-m", "pytest"]

    if test_pattern:
        cmd.append(test_pattern)

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=nodupe", "--cov-report=term-missing"])

    cmd.extend(["--tb=short", "--color=yes"])

    print(f"Running tests with command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with return code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("Error: pytest not found. Please install pytest first.")
        return False


def run_unit_tests():
    """Run only unit tests."""
    return run_tests("-m unit", verbose=True)


def run_integration_tests():
    """Run only integration tests."""
    return run_tests("-m integration", verbose=True)


def run_slow_tests():
    """Run slow tests."""
    return run_tests("-m slow", verbose=True)


def run_all_tests():
    """Run all tests with full coverage."""
    return run_tests(verbose=True, coverage=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run NoDupeLabs tests")
    parser.add_argument("pattern", nargs="?", help="Test pattern to run")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--unit", action="store_true", help="Run only unit tests"
    )
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument("--slow", action="store_true", help="Run slow tests")
    parser.add_argument(
        "--all", action="store_true", help="Run all tests (default)"
    )

    args = parser.parse_args()

    if args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.slow:
        success = run_slow_tests()
    else:
        success = run_tests(args.pattern, verbose=args.verbose or True)

    sys.exit(0 if success else 1)
