import os


def pytest_addoption(parser):
    parser.addoption(
        "--no-dupe-progress",
        action="store",
        default=None,
        choices=("auto", "quiet", "interactive"),
        help="Set NO_DUPE_PROGRESS for tests (auto|quiet|interactive)",
    )


def pytest_configure(config):
    mode = config.getoption("--no-dupe-progress")
    if mode:
        os.environ["NO_DUPE_PROGRESS"] = mode
