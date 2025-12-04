import tempfile
import pytest
try:
    import numpy as np
except ImportError:
    np = None
# type: ignore # pylint: disable=import-error
from nodupe.similarity import make_index, load_index_from_file, save_index_to_file

pytestmark = pytest.mark.skipif(np is None, reason="numpy not available")


def test_bruteforce_save_load():
    idx = make_index(dim=4)  # should pick bruteforce in test env
    vectors = [[0, 0, 0, 0], [1, 1, 1, 1], [0.9, 0.9, 0.9, 0.9]]
    ids = ['a', 'b', 'c']
    idx.add(vectors, ids)
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/test_index.npz"
        # save
        save_index_to_file(idx, p)
        # load
        idx2 = load_index_from_file(p)
        res = idx2.search([0.95, 0.95, 0.95, 0.95], k=1)
        assert len(res) == 1
        # nearest id should be 'c' or 'b'
        assert isinstance(res[0][0], str)
        assert isinstance(res[0][1], float)


def test_bruteforce_save_load_json():
    idx = make_index(dim=4)
    vectors = [[0, 0, 0, 0], [1, 1, 1, 1], [0.9, 0.9, 0.9, 0.9]]
    ids = ['a', 'b', 'c']
    idx.add(vectors, ids)
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/test_index.json"
        save_index_to_file(idx, p)
        # Ensure JSON file conforms to the format
        import json
        obj = json.loads(open(p, 'r', encoding='utf-8').read())
        assert obj.get('format') == 'nodupe.similarity.index'
        assert obj.get('format_version') == '1.0'
        assert int(obj.get('dim')) == 4
        assert isinstance(obj.get('ids'), list)
        assert isinstance(obj.get('vectors'), list)

        idx2 = load_index_from_file(p)
        res = idx2.search([0.95, 0.95, 0.95, 0.95], k=1)
        assert len(res) == 1


def test_bruteforce_save_load_jsonl():
    idx = make_index(dim=4)
    vectors = [[0, 0, 0, 0], [1, 1, 1, 1], [0.9, 0.9, 0.9, 0.9]]
    ids = ['a', 'b', 'c']
    idx.add(vectors, ids)
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/test_index.jsonl"
        save_index_to_file(idx, p)
        # Validate jsonl has one JSON object per line with correct fields
        with open(p, 'r', encoding='utf-8') as fh:
            lines = [l for l in fh if l.strip()]
        assert len(lines) == 3
        import json
        for line in lines:
            rec = json.loads(line)
            assert 'id' in rec and 'vector' in rec
            assert isinstance(rec['id'], str)
            assert isinstance(rec['vector'], list)

        idx2 = load_index_from_file(p)
        res = idx2.search([0.95, 0.95, 0.95, 0.95], k=1)
        assert len(res) == 1

        # ensure file ends with a newline (JSONL standard / widely compatible)
        with open(p, 'rb') as fh:
            fh.seek(-1, 2)
            assert fh.read(1) == b"\n"
