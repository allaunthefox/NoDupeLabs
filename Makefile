.PHONY: help venv install-dev test test-slow docs lint clean

HELP = \
\tsetup-venv   Create and activate a local virtualenv at .venv\n\tinstall-dev  Install development dependencies into the venv\n\ttest         Run the fast test-suite (non-slow)\n\ttest-slow    Run slow / stress tests (slow)

help:
\t@echo "Usage:" && echo "" && echo "$(HELP)"

venv:
\tpython -m venv .venv
\t@echo "To activate: source .venv/bin/activate"

install-dev: venv
\t. .venv/bin/activate && python -m pip install --upgrade pip && pip install -r dev-requirements.txt

test: install-dev
\t. .venv/bin/activate && pytest -q -m "not slow and not integration"

test-slow: install-dev
\t. .venv/bin/activate && pytest -q -m slow

docs: install-dev
\t. .venv/bin/activate && sphinx-build -b html docs/sphinx docs/sphinx/_build

lint: install-dev
\t. .venv/bin/activate && flake8 nodupe/ tests/

clean:
\t-rm -rf .venv
\t-rm -rf docs/sphinx/_build
