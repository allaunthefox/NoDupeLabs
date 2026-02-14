# Dangerfile
import os
import sys

# Add local scripts to path
sys.path.append(os.path.join(os.getcwd(), 'scripts'))

from danger_python import Danger, fail, warn, message

# Initialize Danger
danger = Danger()

# PR Size Check
# Warn when PRs are too big
if danger.github.pr.additions + danger.github.pr.deletions > 500:
    warn("Big PR: This PR contains more than 500 lines of code. Consider breaking it down.")

# Title Check
# Ensure PR title follows conventional commits
title = danger.github.pr.title
valid_types = ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert']
has_valid_type = any(title.startswith(t + ':') or title.startswith(t + '(') for t in valid_types)

if not has_valid_type:
    warn("PR title should follow Conventional Commits (e.g., 'feat: add new feature')")

# API Stability Check
# Check for changes in API files
api_files = [f for f in danger.git.modified_files if "nodupe/core/api.py" in f]
if api_files:
    message("This PR modifies the core API definition.")

# TODO Check
# Warn if new TODOs are introduced without an issue reference
for filename in danger.git.modified_files:
    # Skip non-code files
    if not filename.endswith(('.py', '.js', '.ts', '.tsx')):
        continue
        
    diff = danger.git.diff_for_file(filename)
    if diff:
        for line in diff.added.split('\n'):
            if "TODO" in line and not "#" in line: # rudimentary check for issue number
                warn(f"New TODO introduced in {filename} without issue reference: `{line.strip()}`")

# Documentation Check
# If python files are modified, check if docs are updated
py_files_modified = any(f.endswith('.py') for f in danger.git.modified_files)
docs_files_modified = any(f.startswith('docs/') for f in danger.git.modified_files)

if py_files_modified and not docs_files_modified:
    warn("Python files were modified but no documentation changes were detected. Please ensure documentation is up to date.")

# Dependencies Check
# Warn if dependencies are changed
if "pyproject.toml" in danger.git.modified_files or "poetry.lock" in danger.git.modified_files:
    message("Dependencies have been updated. Please verify that the lock file is up to date.")
