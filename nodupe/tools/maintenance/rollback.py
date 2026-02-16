"""Rollback CLI commands for NoDupeLabs."""
import click
import sys
from pathlib import Path
from nodupe.core.rollback import SnapshotManager, TransactionLog, RollbackManager


@click.group()
def rollback():
    """Rollback and snapshot management commands."""
    pass


@rollback.command('list')
@click.option('--snapshots', is_flag=True, help='List snapshots')
@click.option('--transactions', is_flag=True, help='List transactions')
def list_cmd(snapshots, transactions):
    """List snapshots or transactions."""
    snapshot_mgr = SnapshotManager()
    tx_log = TransactionLog()

    if snapshots or not transactions:
        click.echo("=== Snapshots ===")
        snaps = snapshot_mgr.list_snapshots()
        if not snaps:
            click.echo("No snapshots found.")
        for s in snaps:
            click.echo(f"  {s['snapshot_id']}: {s['timestamp']} ({s['file_count']} files)")

    if transactions:
        click.echo("\n=== Transactions ===")
        txs = tx_log.list_transactions()
        if not txs:
            click.echo("No transactions found.")
        for t in txs:
            click.echo(f"  {t['transaction_id']}: {t['timestamp']} [{t['status']}] ({t['operation_count']} ops)")


@rollback.command('create')
@click.argument('paths', nargs=-1, required=True)
def create_cmd(paths):
    """Create a snapshot of specified paths."""
    snapshot_mgr = SnapshotManager()

    path_list = [str(Path(p).absolute()) for p in paths]
    snapshot = snapshot_mgr.create_snapshot(path_list)

    click.echo(f"Created snapshot: {snapshot.snapshot_id}")
    click.echo(f"  Files: {len(snapshot.files)}")


@rollback.command('restore')
@click.argument('snapshot_id')
def restore_cmd(snapshot_id):
    """Restore files from a snapshot."""
    snapshot_mgr = SnapshotManager()

    success = snapshot_mgr.restore_snapshot(snapshot_id)
    if success:
        click.echo(f"Restored snapshot: {snapshot_id}")
    else:
        click.echo(f"Failed to restore snapshot: {snapshot_id}", err=True)
        sys.exit(1)


@rollback.command('delete')
@click.argument('snapshot_id')
def delete_cmd(snapshot_id):
    """Delete a snapshot."""
    snapshot_mgr = SnapshotManager()

    success = snapshot_mgr.delete_snapshot(snapshot_id)
    if success:
        click.echo(f"Deleted snapshot: {snapshot_id}")
    else:
        click.echo(f"Snapshot not found: {snapshot_id}", err=True)


@rollback.command('undo')
def undo_cmd():
    """Undo the last transaction."""
    snapshot_mgr = SnapshotManager()
    tx_log = TransactionLog()
    manager = RollbackManager(snapshot_mgr, tx_log)

    success = manager.undo_last_operation()
    if success:
        click.echo("Undid last operation")
    else:
        click.echo("No operation to undo", err=True)


if __name__ == '__main__':
    rollback()
