# Transaction API

## TransactionLog

Logs operations for rollback capability.

### Constructor

```python
TransactionLog(log_dir: str = ".nodupe/backups")
```

### Methods

#### begin_transaction

```python
def begin_transaction(self) -> str
```

Start a new transaction.

**Returns:** Transaction ID

#### log_operation

```python
def log_operation(self, operation: Operation) -> None
```

Log an operation in the current transaction.

**Parameters:**
- `operation`: Operation to log

#### commit_transaction

```python
def commit_transaction(self) -> str
```

Commit the transaction.

**Returns:** Final status

#### rollback_transaction

```python
def rollback_transaction(self, transaction_id: str) -> bool
```

Rollback all operations in a transaction.

**Parameters:**
- `transaction_id`: ID of transaction to rollback

**Returns:** `True` if successful

#### list_transactions

```python
def list_transactions(self) -> list[dict]
```

List all transactions.

**Returns:** List of transaction summaries

## Operation

Represents a single operation in a transaction.

### Constructor

```python
Operation(
    operation_type: str,
    path: str,
    original_hash: Optional[str] = None,
    backup_path: Optional[str] = None,
    new_path: Optional[str] = None
)
```

### Properties

- `operation_type`: Type of operation (delete, modify, move, copy, restore)
- `path`: File path
- `original_hash`: Original file hash
- `backup_path`: Backup file path
- `new_path`: New path (for move operations)
