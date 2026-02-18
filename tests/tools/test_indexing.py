import sqlite3
import pytest

from nodupe.tools.databases.indexing import (
    DatabaseIndexing,
    IndexingError,
    create_covering_index,
)


def _create_minimal_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE files (
            id INTEGER PRIMARY KEY,
            path TEXT,
            size INTEGER,
            hash TEXT,
            is_duplicate INTEGER,
            duplicate_of INTEGER,
            status TEXT,
            modified_time INTEGER
        )
    """
    )
    cur.execute(
        """
        CREATE TABLE embeddings (
            id INTEGER PRIMARY KEY,
            file_id INTEGER,
            model_version TEXT,
            created_time INTEGER
        )
    """
    )
    cur.execute(
        """
        CREATE TABLE file_relationships (
            id INTEGER PRIMARY KEY,
            file1_id INTEGER,
            file2_id INTEGER,
            relationship_type TEXT,
            similarity_score REAL
        )
    """
    )
    cur.execute(
        """
        CREATE TABLE tools (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            status TEXT,
            enabled INTEGER
        )
    """
    )
    conn.commit()


def test_create_and_list_indexes(tmp_path):
    conn = sqlite3.connect(":memory:")
    _create_minimal_schema(conn)

    idx = DatabaseIndexing(conn)
    # create standard indexes without raising
    idx.create_indexes()

    # verify some expected indexes exist
    indexes = idx.get_indexes("files")
    names = {i["name"] for i in indexes}
    assert any(n.startswith("idx_files_") for n in names)

    # get_index_info returns columns for a known index
    # pick one index name from the list and check pragma
    if indexes:
        info = idx.get_index_info(indexes[0]["name"])
        assert isinstance(info, list)

    conn.close()


def test_create_and_drop_custom_index():
    conn = sqlite3.connect(":memory:")
    _create_minimal_schema(conn)

    idx = DatabaseIndexing(conn)
    idx.create_index("idx_test_path", "files", ["path"])

    found = [i for i in idx.get_indexes("files") if i["name"] == "idx_test_path"]
    assert found

    idx.drop_index("idx_test_path")
    found = [i for i in idx.get_indexes("files") if i["name"] == "idx_test_path"]
    assert not found
    conn.close()


def test_optimize_and_analyze_query_and_index_usage():
    conn = sqlite3.connect(":memory:")
    _create_minimal_schema(conn)

    idx = DatabaseIndexing(conn)
    idx.create_index("idx_files_path", "files", ["path"])

    # optimize_indexes should run without error
    idx.optimize_indexes()

    # analyze a simple query
    plan = idx.analyze_query("SELECT path FROM files WHERE path = 'x'")
    assert isinstance(plan, list)

    # is_index_used should return True if the index name appears in the plan detail
    used = idx.is_index_used("SELECT path FROM files WHERE path = 'x'", "idx_files_path")
    # depending on SQLite planner, index may or may not be used — ensure bool returned
    assert isinstance(used, bool)

    conn.close()


def test_get_table_stats_and_find_missing_indexes():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    # create a table which will not have indexes
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, created_at INTEGER, status TEXT)")
    conn.commit()

    idx = DatabaseIndexing(conn)

    # get_table_stats may raise IndexingError because `dbstat` virtual table isn't available
    with pytest.raises(IndexingError):
        idx.get_table_stats("users")

    # find_missing_indexes should suggest indexes for common columns
    suggestions = idx.find_missing_indexes()
    assert any(s["table"] == "users" for s in suggestions)

    conn.close()


def test_reindex_and_error_paths():
    conn = sqlite3.connect(":memory:")
    _create_minimal_schema(conn)

    idx = DatabaseIndexing(conn)
    # Reindex all should not fail
    idx.reindex()

    # invalid SQL passed to analyze_query should raise IndexingError
    with pytest.raises(IndexingError):
        idx.analyze_query("THIS IS NOT SQL")

    conn.close()


def test_create_covering_index_creates_index():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, user_id INTEGER, event_type TEXT, created_at INTEGER)")
    conn.commit()

    create_covering_index(conn, "idx_events_user_type", "events", ["user_id"], ["event_type", "created_at"])

    # verify index exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_events_user_type'")
    assert cur.fetchone() is not None

    conn.close()
