#!/usr/bin/env python3
"""
Documentation build script for NoDupeLabs.

This script builds documentation using both Sphinx and MkDocs.
It can build both systems or just one of them based on command line arguments.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        sys.exit(1)
    
    return result


def build_sphinx(output_dir="docs/_build"):
    """Build documentation using Sphinx."""
    print("Building Sphinx documentation...")
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Run Sphinx build
    cmd = [
        "python", "-m", "sphinx",
        "-b", "html",
        "docs/source",
        output_dir
    ]
    
    result = run_command(cmd)
    print("Sphinx build completed successfully!")
    return result


def build_mkdocs(output_dir="site"):
    """Build documentation using MkDocs."""
    print("Building MkDocs documentation...")
    
    # Check if mkdocs is installed
    try:
        run_command(["python", "-m", "mkdocs", "--version"], check=False)
    except FileNotFoundError:
        print("MkDocs is not installed. Please install it with: pip install mkdocs mkdocs-material")
        sys.exit(1)
    
    # Run MkDocs build
    cmd = ["python", "-m", "mkdocs", "build", "--site-dir", output_dir]
    
    result = run_command(cmd)
    print("MkDocs build completed successfully!")
    return result


def build_markify(output_dir="output/markify"):
    """Build documentation using Markify."""
    print("Building Markify documentation...")
    
    # Check if markify is installed
    try:
        run_command(["python", "-m", "markify", "--version"], check=False)
    except FileNotFoundError:
        print("Markify is not installed. Please install it with: pip install markify")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Run Markify build
    cmd = ["python", "-m", "markify", "build", "--config", "markify.yml"]
    
    result = run_command(cmd)
    print("Markify build completed successfully!")
    return result


def clean_docs(output_dirs=None):
    """Clean documentation build directories."""
    if output_dirs is None:
        output_dirs = ["docs/_build", "site"]
    
    for output_dir in output_dirs:
        path = Path(output_dir)
        if path.exists():
            print(f"Cleaning {output_dir}...")
            import shutil
            shutil.rmtree(path)
            print(f"Cleaned {output_dir}")
        else:
            print(f"{output_dir} does not exist, skipping...")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build NoDupeLabs documentation")
    parser.add_argument(
        "--builder",
        choices=["sphinx", "mkdocs", "both"],
        default="both",
        help="Which documentation system to build (default: both)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before building"
    )
    parser.add_argument(
        "--sphinx-output",
        default="docs/_build",
        help="Sphinx output directory (default: docs/_build)"
    )
    parser.add_argument(
        "--mkdocs-output",
        default="site",
        help="MkDocs output directory (default: site)"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Clean if requested
    if args.clean:
        clean_docs([args.sphinx_output, args.mkdocs_output])
    
    # Build documentation
    if args.builder == "sphinx" or args.builder == "both":
        build_sphinx(args.sphinx_output)
    
    if args.builder == "mkdocs" or args.builder == "both":
        build_mkdocs(args.mkdocs_output)
    
    print("\nDocumentation build completed!")
    print(f"Sphinx output: {args.sphinx_output}")
    print(f"MkDocs output: {args.mkdocs_output}")


if __name__ == "__main__":
    main()
