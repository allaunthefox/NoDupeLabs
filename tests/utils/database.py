# Database Test Utilities
# Helper functions for database operations testing

import sqlite3
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from unittest.mock import MagicMock, patch
import contextlib
import time

def create_test_database(
    schema: Optional[str] = None,
    data: Optional[List[Dict[str, Any]]] = None,
    db_name: str = "test_db",
    use_memory: bool = True
) -> Union[str, Path]:
    """
    Create a test database with optional schema and data.

    Args:
        schema: SQL schema definition
        data: List of data dictionaries to insert
        db_name: Database name
        use_memory: Use in-memory database if True

    Returns:
        Database path or connection string
    """
    if use_memory:
        conn = sqlite3.connect(":memory:")
        return conn
    else:
        db_path = Path(tempfile.gettempdir()) / f"{db_name}.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()
        return str(db_path)

def setup_test_database_schema(
    conn: sqlite3.Connection,
    schema: str
) -> None:
    """
    Set up database schema for testing.

    Args:
        conn: Database connection
        schema: SQL schema definition
    """
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()

def insert_test_data(
    conn: sqlite3.Connection,
    table: str,
    data: List[Dict[str, Any]]
) -> None:
    """
    Insert test data into a database table.

    Args:
        conn: Database connection
        table: Table name
        data: List of data dictionaries
    """
    if not data:
        return

    cursor = conn.cursor()

    # Get column names from first data item
    columns = list(data[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    columns_str = ", ".join(columns)

    # Prepare and execute insert statements
    for item in data:
        values = [item[col] for col in columns]
        cursor.execute(
            f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
            values
        )

    conn.commit()

def verify_database_state(
    conn: sqlite3.Connection,
    expected_state: Dict[str, Any],
    tolerance: float = 0.0
) -> bool:
    """
    Verify database state matches expected state.

    Args:
        conn: Database connection
        expected_state: Expected database state
        tolerance: Numeric tolerance for floating point comparisons

    Returns:
        True if state matches, False otherwise
    """
    cursor = conn.cursor()

    for table, expected_data in expected_state.items():
        # Query all data from table
        cursor.execute(f"SELECT * FROM {table}")
        actual_data = cursor.fetchall()

        # Get column names
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]

        # Convert to list of dictionaries for comparison
        actual_records = []
        for row in actual_data:
            record = dict(zip(columns, row))
            actual_records.append(record)

        # Compare with expected data
        if len(actual_records) != len(expected_data):
            return False

        for actual, expected in zip(actual_records, expected_data):
            for key, expected_value in expected.items():
                actual_value = actual[key]

                if isinstance(expected_value, (int, str, bool)):
                    if actual_value != expected_value:
                        return False
                elif isinstance(expected_value, float):
                    if abs(actual_value - expected_value) > tolerance:
                        return False
                else:
                    if actual_value != expected_value:
                        return False

    return True

def create_database_mock() -> MagicMock:
    """
    Create a mock database connection for testing.

    Returns:
        Mock database connection object
    """
    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_cursor = MagicMock()

    # Set up mock behavior
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)
    mock_cursor.fetchall.return_value = [(1, "test"), (2, "data")]
    mock_cursor.description = [("id",), ("name",)]

    return mock_conn

def create_database_fixture(
    schema: str,
    initial_data: Optional[List[Dict[str, Any]]] = None
) -> Callable:
    """
    Create a pytest fixture for database testing.

    Args:
        schema: Database schema
        initial_data: Initial data to populate

    Returns:
        Fixture function
    """
    def database_fixture():
        # Create in-memory database
        conn = sqlite3.connect(":memory:")

        # Set up schema
        setup_test_database_schema(conn, schema)

        # Insert initial data if provided
        if initial_data:
            for table_data in initial_data:
                table_name = list(table_data.keys())[0]
                insert_test_data(conn, table_name, table_data[table_name])

        yield conn

        # Cleanup
        conn.close()

    return database_fixture

def simulate_database_errors(
    error_type: str = "connection",
    operation: str = "execute"
) -> Callable:
    """
    Create a context manager to simulate database errors.

    Args:
        error_type: Type of error to simulate
        operation: Database operation to fail

    Returns:
        Context manager for error simulation
    """
    @contextlib.contextmanager
    def error_context():
        error_map = {
            "connection": sqlite3.OperationalError("Unable to connect"),
            "integrity": sqlite3.IntegrityError("Constraint violation"),
            "programming": sqlite3.ProgrammingError("SQL syntax error"),
            "timeout": sqlite3.OperationalError("Database locked")
        }

        error = error_map.get(error_type, sqlite3.Error("Database error"))

        with patch('sqlite3.Connection') as mock_conn_class:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            if operation == "execute":
                mock_cursor.execute.side_effect = error
            elif operation == "commit":
                mock_conn.commit.side_effect = error
            elif operation == "fetch":
                mock_cursor.fetchall.side_effect = error

            mock_conn.cursor.return_value = mock_cursor
            mock_conn_class.return_value = mock_conn

            yield mock_conn

    return error_context

def benchmark_database_operations(
    conn: sqlite3.Connection,
    operations: List[Callable],
    iterations: int = 100
) -> Dict[str, float]:
    """
    Benchmark database operations performance.

    Args:
        conn: Database connection
        operations: List of operation functions
        iterations: Number of iterations per operation

    Returns:
        Dictionary of operation timings
    """
    results = {}

    for i, operation in enumerate(operations):
        start_time = time.time()

        for _ in range(iterations):
            operation(conn)

        end_time = time.time()
        avg_time = (end_time - start_time) / iterations

        results[f"operation_{i}"] = avg_time

    return results

def create_transaction_test_scenarios() -> List[Dict[str, Any]]:
    """
    Create test scenarios for transaction testing.

    Returns:
        List of transaction test scenarios
    """
    return [
        {
            "name": "successful_transaction",
            "operations": [
                "BEGIN",
                "INSERT INTO test VALUES (1, 'data')",
                "COMMIT"
            ],
            "expected_result": "success"
        },
        {
            "name": "failed_transaction",
            "operations": [
                "BEGIN",
                "INSERT INTO test VALUES (1, 'data')",
                "ROLLBACK"
            ],
            "expected_result": "rollback"
        },
        {
            "name": "nested_transaction",
            "operations": [
                "BEGIN",
                "SAVEPOINT sp1",
                "INSERT INTO test VALUES (1, 'data')",
                "RELEASE SAVEPOINT sp1",
                "COMMIT"
            ],
            "expected_result": "success"
        }
    ]

def verify_database_performance(
    conn: sqlite3.Connection,
    query: str,
    max_execution_time: float = 1.0,
    iterations: int = 10
) -> bool:
    """
    Verify database query performance meets requirements.

    Args:
        conn: Database connection
        query: SQL query to test
        max_execution_time: Maximum allowed execution time
        iterations: Number of test iterations

    Returns:
        True if performance is acceptable, False otherwise
    """
    cursor = conn.cursor()
    total_time = 0.0

    for _ in range(iterations):
        start_time = time.time()
        cursor.execute(query)
        cursor.fetchall()
        end_time = time.time()

        total_time += (end_time - start_time)

    avg_time = total_time / iterations
    return avg_time <= max_execution_time

def create_database_snapshot(
    conn: sqlite3.Connection
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create a snapshot of current database state.

    Args:
        conn: Database connection

    Returns:
        Dictionary representing database state
    """
    cursor = conn.cursor()
    snapshot = {}

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]

    for table in tables:
        # Get table data
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        # Get column names
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]

        # Convert to list of dictionaries
        table_data = []
        for row in rows:
            record = dict(zip(columns, row))
            table_data.append(record)

        snapshot[table] = table_data

    return snapshot

def restore_database_snapshot(
    conn: sqlite3.Connection,
    snapshot: Dict[str, List[Dict[str, Any]]]
) -> None:
    """
    Restore database to a previous snapshot state.

    Args:
        conn: Database connection
        snapshot: Database snapshot to restore
    """
    cursor = conn.cursor()

    for table, data in snapshot.items():
        # Clear existing data
        cursor.execute(f"DELETE FROM {table}")

        # Re-insert data
        if data:
            columns = list(data[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            columns_str = ", ".join(columns)

            for item in data:
                values = [item[col] for col in columns]
                cursor.execute(
                    f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                    values
                )

    conn.commit()
