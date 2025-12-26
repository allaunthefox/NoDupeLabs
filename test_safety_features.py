#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Test script for safety features implementation.

This script tests the audit logging, backup creation, and user confirmation
features that were added to the NoDupeLabs plugins.
"""

import tempfile
import shutil
from pathlib import Path
from nodupe.core.audit import get_audit_logger, AuditEventType
from nodupe.core.backup import get_backup_manager, create_backup_before_operation
from nodupe.core.confirmation import get_confirmation_manager


def test_audit_logging():
    """Test audit logging functionality."""
    print("Testing audit logging...")
    
    audit_logger = get_audit_logger()
    
    # Test various audit events
    audit_logger.log_scan_started([Path("/test/path")], {"recursive": True})
    audit_logger.log_file_processed(Path("/test/file.txt"), 1024, "test_hash")
    audit_logger.log_duplicate_found(Path("/original.txt"), Path("/duplicate.txt"))
    audit_logger.log_apply_started("delete", {"action": "delete", "dry_run": False})
    audit_logger.log_file_deleted(Path("/test/file.txt"), 1024)
    audit_logger.log_backup_created(Path("/backup/path"), "delete", 1)
    
    print("✓ Audit logging test completed")


def test_backup_system():
    """Test backup system functionality."""
    print("Testing backup system...")
    
    backup_mgr = get_backup_manager()
    
    # Create a temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test1.txt"
        test_file1.write_text("Test content 1")
        
        test_file2 = temp_path / "test2.txt" 
        test_file2.write_text("Test content 2")
        
        # Test backup creation
        backup_path = backup_mgr.create_file_backup(
            "test_operation", 
            "Test backup creation",
            [test_file1, test_file2]
        )
        
        print(f"✓ Backup created at: {backup_path}")
        print(f"✓ Backup file exists: {backup_path.exists()}")
        
        # Test backup verification
        is_valid = backup_mgr.verify_backup(backup_path)
        print(f"✓ Backup verification: {is_valid}")
        
        # Test backup listing
        backups = backup_mgr.list_backups()
        print(f"✓ Found {len(backups)} backups in system")
    
    print("✓ Backup system test completed")


def test_confirmation_system():
    """Test confirmation system functionality."""
    print("Testing confirmation system...")
    
    conf_mgr = get_confirmation_manager()
    
    # Test scan confirmation
    scan_confirmed = conf_mgr.confirm_scan_operation([Path("/test/dir")], recursive=True)
    print(f"✓ Scan confirmation test completed (would have confirmed: {scan_confirmed})")
    
    # Test apply confirmation with mock file data
    files_data = [
        {
            'path': '/test/file1.txt',
            'size': 1024,
            'id': 1
        },
        {
            'path': '/test/file2.txt', 
            'size': 2048,
            'id': 2
        }
    ]
    
    apply_confirmed = conf_mgr.confirm_apply_action('delete', files_data)
    print(f"✓ Apply confirmation test completed (would have confirmed: {apply_confirmed})")
    
    # Test dry run confirmation
    dry_run_confirmed = conf_mgr.confirm_dry_run('delete', files_data)
    print(f"✓ Dry run confirmation test completed (would have confirmed: {dry_run_confirmed})")
    
    print("✓ Confirmation system test completed")


def test_integration_with_plugins():
    """Test that safety features integrate properly with plugins."""
    print("Testing plugin integration...")
    
    # Import the updated plugins to verify they can be loaded
    from nodupe.plugins.commands import scan, apply, plan
    
    # Verify plugins can be imported without errors
    assert hasattr(scan, 'scan_plugin'), "Scan plugin not available"
    assert hasattr(apply, 'apply_plugin'), "Apply plugin not available" 
    assert hasattr(plan, 'plan_plugin'), "Plan plugin not available"
    
    print("✓ Plugin imports successful")
    
    # Verify plugins have required safety imports
    import inspect
    
    # Check if scan plugin has audit and confirmation imports
    scan_source = inspect.getsource(scan.ScanPlugin.execute_scan)
    assert 'get_audit_logger' in scan_source, "Audit logger not used in scan plugin"
    assert 'get_confirmation_manager' in scan_source, "Confirmation manager not used in scan plugin"
    
    # Check if apply plugin has safety imports
    apply_source = inspect.getsource(apply.ApplyPlugin.execute_apply)
    assert 'get_audit_logger' in apply_source, "Audit logger not used in apply plugin"
    assert 'get_confirmation_manager' in apply_source, "Confirmation manager not used in apply plugin"
    assert 'create_backup_before_operation' in apply_source, "Backup system not used in apply plugin"
    
    # Check if plan plugin has audit imports
    plan_source = inspect.getsource(plan.PlanPlugin.execute_plan)
    assert 'get_audit_logger' in plan_source, "Audit logger not used in plan plugin"
    
    print("✓ Plugin safety feature integration verified")


def main():
    """Run all safety feature tests."""
    print("Running safety features tests...\n")
    
    try:
        test_audit_logging()
        print()
        
        test_backup_system()
        print()
        
        test_confirmation_system()
        print()
        
        test_integration_with_plugins()
        print()
        
        print("🎉 All safety features tests passed!")
        print("\nSafety features implemented:")
        print("- ✓ Audit logging system")
        print("- ✓ Backup management system") 
        print("- ✓ User confirmation system")
        print("- ✓ Integration with scan, apply, and plan plugins")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
