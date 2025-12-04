from pathlib import Path
# type: ignore # pylint: disable=import-error
from nodupe.nsfw_classifier import NSFWClassifier


def test_nsfw_classify_basic():
    c = NSFWClassifier(threshold=2)
    p = Path(__file__)
    res = c.classify(p, 'text/plain')
    assert isinstance(res, dict)
    assert set(['score', 'flagged', 'method', 'reason',
               'threshold']).issubset(res.keys())
    assert isinstance(res['score'], int)
    assert isinstance(res['flagged'], bool)
    assert isinstance(res['threshold'], int)
