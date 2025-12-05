# Running tests locally

This repository's CI installs and runs the test-suite with specific tooling. To get the same
experience locally, create a Python virtual environment and install the development
dependencies below.

Quick setup (Unix / Linux / macOS):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r dev-requirements.txt
```

Running tests
-------------

- Fast tests (short):

```bash
pytest -q -m "not slow and not integration"
```

- Slow / stress tests (longer; marked `slow`):

```bash
pytest -q tests/test_concurrency_stress.py -m slow
```

Notes
-----
- The `tests/test_concurrency_stress.py` file uses heavy concurrency and is marked `slow`.
  Run it only when you are ready to validate large-scale concurrency behavior.
- CI has a `slow-tests` job which runs these slow tests with a longer timeout; you can run
  them locally with the command above.
