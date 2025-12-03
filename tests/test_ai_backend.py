from pathlib import Path
from nodupe.ai.backends import choose_backend  # type: ignore # pylint: disable=import-error


def test_choose_backend_returns_backend():
    be = choose_backend()
    # backend must implement available() and predict
    assert hasattr(be, 'available')
    assert hasattr(be, 'predict')

    # predict must return a (int, str) tuple for a missing or text file
    sample = Path(__file__)
    score, reason = be.predict(sample)
    assert isinstance(score, int)
    assert isinstance(reason, str)
