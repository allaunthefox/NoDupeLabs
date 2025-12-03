from nodupe.similarity import make_index  # type: ignore # pylint: disable=import-error


def test_make_index_default():
    idx = make_index(dim=8)
    # index should have add and search methods
    assert hasattr(idx, 'add')
    assert hasattr(idx, 'search')

def test_index_add_search():
    idx = make_index(dim=4)
    vectors = [[0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]]
    ids = ['a', 'b']
    idx.add(vectors, ids=ids)
    res = idx.search([0.9, 0.9, 0.9, 0.9], k=2)
    assert isinstance(res, list)
    assert len(res) >= 1
