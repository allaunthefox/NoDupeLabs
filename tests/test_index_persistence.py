import tempfile
import numpy as np
from nodupe.similarity import make_index, load_index_from_file


def test_bruteforce_save_load():
    idx = make_index(dim=4)  # should pick bruteforce in test env
    vectors = [[0,0,0,0], [1,1,1,1], [0.9,0.9,0.9,0.9]]
    ids = ['a','b','c']
    idx.add(vectors, ids)
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/test_index.npz"
        # save
        from nodupe.similarity.index import save_index_to_file, load_index_from_file
        save_index_to_file(idx, p)
        # load
        idx2 = load_index_from_file(p)
        res = idx2.search([0.95,0.95,0.95,0.95], k=1)
        assert len(res) == 1
        # nearest id should be 'c' or 'b'
        assert isinstance(res[0][0], str)
        assert isinstance(res[0][1], float)
