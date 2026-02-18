import sqlite3
from unittest.mock import Mock

import pytest

from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.indexing import (
    DatabaseIndexing,
    IndexingError,
    create_covering_index,
)
from nodupe.tools.databases.schema import DatabaseSchema


@pytest.fixture(autouse=True)
def clear_db_instances():
    DatabaseConnection._instances.clear()
    yield
    DatabaseConnection._instances.clear()


def _make_conn(tmp_path):
    db_path = str(tmp_path / "idx.db")
    db_conn = DatabaseConnection.get_instance(db_path)
    # ensure full schema
    DatabaseSchema(db_conn.get_connection()).create_schema()
    return db_conn.get_connection()


def test_create_and_drop_index_and_get_indexes(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    # Create a custom index
    idx.create_index("idx_test_path", "files", ["path"], unique=False)
    indexes = idx.get_indexes(table_name="files")
    names = [i["name"] for i in indexes]
    assert any("idx_test_path" in n for n in names)

    # Drop index
    idx.drop_index("idx_test_path")
    indexes_after = idx.get_indexes(table_name="files")
    names_after = [i["name"] for i in indexes_after]
    assert all("idx_test_path" not in n for n in names_after)


def test_get_index_info_and_create_covering_index(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    # Create covering index using helper
    create_covering_index(
        conn, "cov_idx", "files", ["status"], ["path", "hash"]
    )

    indexes = idx.get_indexes(table_name="files")
    names = [i["name"] for i in indexes]
    assert any("cov_idx" in n for n in names)

    info = idx.get_index_info("cov_idx")
    assert isinstance(info, list)
    assert any(col["name"] in ("status", "path", "hash") for col in info)


def test_find_missing_indexes_and_stats(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    # create a lightweight table with a 'status' column and no indexes
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS temp_table (id INTEGER PRIMARY KEY, status TEXT)"
    )
    conn.commit()

    suggestions = idx.find_missing_indexes()
    # suggestions may include temp_table if status is detected
    assert isinstance(suggestions, list)

    stats = idx.get_index_stats()
    assert "total_tables" in stats and "total_indexes" in stats

    # create_indexes should succeed (idempotent)
    idx.create_indexes()
    # optimize should run without error
    idx.optimize_indexes()

    # reindex should run without error
    idx.reindex()


def test_analyze_query_and_is_index_used(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    # create an index and insert a row
    idx.create_index("idx_test_path", "files", ["path"], unique=False)

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("/tmp/x", 10, 1, 1, 1, 1),
    )
    conn.commit()

    query = "SELECT * FROM files INDEXED BY idx_test_path WHERE path = '/tmp/x'"
    plan = idx.analyze_query(query)
    assert isinstance(plan, list)
    # forced INDEXED BY should include the index name in the plan
    assert any("idx_test_path" in (step.get("detail") or "") for step in plan)

    assert idx.is_index_used(query, "idx_test_path") is True


def test_get_table_stats_uses_dbstat_when_available(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    # insert some rows
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("/tmp/a", 10, 1, 1, 1, 1),
    )
    conn.commit()

    # create a fake dbstat table to simulate page-size reporting
    cur.execute("CREATE TABLE IF NOT EXISTS dbstat (name TEXT, pgsize INTEGER)")
    cur.execute(
        "INSERT INTO dbstat (name, pgsize) VALUES (?, ?)", ("files", 12345)
    )
    conn.commit()

    stats = idx.get_table_stats("files")
    assert stats["table_name"] == "files"
    assert stats["row_count"] >= 1
    assert stats["table_size_bytes"] == 12345
    assert "index_count" in stats


def test_get_index_info_nonexistent_index_returns_empty(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    info = idx.get_index_info("no_such_index")
    assert isinstance(info, list)
    assert info == []


def test_create_unique_index_enforces_uniqueness(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    # create a small table without uniqueness and enforce a unique index
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS tmp_unique (id INTEGER PRIMARY KEY, val TEXT)"
    )
    conn.commit()

    idx.create_index("tmp_val_unique", "tmp_unique", ["val"], unique=True)

    # inserting duplicate values should raise due to unique index
    cur.execute("INSERT INTO tmp_unique (val) VALUES (?)", ("dup",))
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO tmp_unique (val) VALUES (?)", ("dup",))
        conn.commit()


def test_drop_index_if_not_exists_false_raises(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    with pytest.raises(IndexingError):
        idx.drop_index("does_not_exist", if_exists=False)


def test_reindex_invalid_index_raises(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    with pytest.raises(IndexingError):
        idx.reindex("nonexistent_index")


def test_get_table_stats_without_dbstat_raises(tmp_path):
    # wrap the real connection in a lightweight proxy so we can simulate a failing dbstat access
    real_conn = _make_conn(tmp_path)

    class _WrapperCursor:
        def __init__(self, base):
            self._base = base

        def execute(self, sql, params=None):
            if isinstance(sql, str) and "FROM dbstat" in sql:
                # simulate missing/readonly dbstat access
                raise sqlite3.OperationalError("no such table: dbstat")
            return (
                self._base.execute(sql, params)
                if params is not None
                else self._base.execute(sql)
            )

        def fetchone(self):
            return self._base.fetchone()

        def fetchall(self):
            return self._base.fetchall()

        def __getattr__(self, name):
            return getattr(self._base, name)

    class _ProxyConn:
        def __init__(self, real):
            self._real = real

        def cursor(self):
            return _WrapperCursor(self._real.cursor())

        def execute(self, *a, **kw):
            return self._real.execute(*a, **kw)

        def commit(self):
            return self._real.commit()

        def __getattr__(self, name):
            return getattr(self._real, name)

    proxy = _ProxyConn(real_conn)
    idx = DatabaseIndexing(proxy)

    with pytest.raises(IndexingError):
        idx.get_table_stats("files")

    real_conn.close()


def test_is_index_used_returns_false_when_not_used(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    idx.create_index("idx_test_path", "files", ["path"], unique=False)

    # query does not reference the path/index
    query = "SELECT * FROM files WHERE size = 10"
    assert idx.is_index_used(query, "idx_test_path") is False


def test_analyze_query_invalid_sql_raises(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    with pytest.raises(IndexingError):
        idx.analyze_query("SELEKT * FROM missing_table")


def test_get_indexes_all_and_filtered(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    idx.create_index("idx_test_path", "files", ["path"], unique=False)
    all_indexes = idx.get_indexes()
    assert any("idx_test_path" in i["name"] for i in all_indexes)

    file_indexes = idx.get_indexes(table_name="files")
    assert any("idx_test_path" in i["name"] for i in file_indexes)


def test_find_missing_indexes_suggests_common_columns(tmp_path):
    conn = _make_conn(tmp_path)
    idx = DatabaseIndexing(conn)

    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS missing_idx (id INTEGER PRIMARY KEY, created_at INTEGER, other TEXT)"
    )
    conn.commit()

    suggestions = idx.find_missing_indexes()
    assert any(
        s.get("table") == "missing_idx" and s.get("column") == "created_at"
        for s in suggestions
    )


def test_get_index_stats_handles_empty_catalog():
    # use a fresh in-memory connection with no tables
    conn = sqlite3.connect(":memory:")
    idx = DatabaseIndexing(conn)

    stats = idx.get_index_stats()
    assert stats["total_tables"] == 0
    assert stats["avg_indexes_per_table"] == 0

    conn.close()
