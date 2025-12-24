"""
Test suite for database file operations functionality.
Tests file record management and storage from nodupe.core.database.files.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection


class TestFileRecordManager:
    """Test FileRecordManager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create a temporary database for testing
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_connection = DatabaseConnection(db_path=self.db_path)
        self.db_connection.initialize_database()
        self.file_manager = FileRepository(self.db_connection)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_record_manager_initialization(self):
        """Test FileRecordManager initialization."""
        assert self.file_manager is not None
        assert self.file_manager.db is not None
    
    def test_create_file_record(self):
        """Test creating file records."""
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        file_info = {
            'path': test_file,
            'size': os.path.getsize(test_file),
            'modified_time': os.path.getmtime(test_file),
            'hash': 'test_hash_123',
            'created_time': os.path.getctime(test_file),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        # Create file record
        file_id = self.file_manager.add_file(file_info['path'], file_info['size'], file_info['modified_time'], file_info['hash'])
        assert file_id is not None
        assert isinstance(file_id, int)
        
        # Verify record was created
        record = self.file_manager.get_file(file_id)
        assert record is not None
        assert record['path'] == test_file
        assert record['hash'] == 'test_hash_123'
        assert record['size'] == os.path.getsize(test_file)
    
    def test_get_file_by_id(self):
        """Test getting file by ID."""
        # Create test file
        test_file = os.path.join(self.temp_dir, 'get_test.txt')
        with open(test_file, 'w') as f:
            f.write('get test content')
        
        file_info = {
            'path': test_file,
            'size': os.path.getsize(test_file),
            'modified_time': os.path.getmtime(test_file),
            'hash': 'get_test_hash',
            'created_time': os.path.getctime(test_file),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file_id = self.file_manager.add_file(file_info['path'], file_info['size'], file_info['modified_time'], file_info['hash'])
        
        # Get file by ID
        record = self.file_manager.get_file(file_id)
        assert record is not None
        assert record['id'] == file_id
        assert record['path'] == test_file
        assert record['hash'] == 'get_test_hash'
    
    def test_get_file_by_path(self):
        """Test getting file by path."""
        # Create test file
        test_file = os.path.join(self.temp_dir, 'path_test.txt')
        with open(test_file, 'w') as f:
            f.write('path test content')
        
        file_info = {
            'path': test_file,
            'size': os.path.getsize(test_file),
            'modified_time': os.path.getmtime(test_file),
            'hash': 'path_test_hash',
            'created_time': os.path.getctime(test_file),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        self.file_manager.add_file(file_info['path'], file_info['size'], file_info['modified_time'], file_info['hash'])
        
        # Get file by path
        record = self.file_manager.get_file_by_path(test_file)
        assert record is not None
        assert record['path'] == test_file
        assert record['hash'] == 'path_test_hash'
        assert record['size'] == os.path.getsize(test_file)
    
    def test_update_file_record(self):
        """Test updating file records."""
        # Create test file
        test_file = os.path.join(self.temp_dir, 'update_test.txt')
        with open(test_file, 'w') as f:
            f.write('update test content')
        
        file_info = {
            'path': test_file,
            'size': os.path.getsize(test_file),
            'modified_time': os.path.getmtime(test_file),
            'hash': 'initial_hash',
            'created_time': os.path.getctime(test_file),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file_id = self.file_manager.add_file(file_info['path'], file_info['size'], file_info['modified_time'], file_info['hash'])
        
        # Update the record
        update_result = self.file_manager.update_file(file_id, hash='updated_hash', size=500)
        assert update_result is True
        
        # Verify update
        updated_record = self.file_manager.get_file(file_id)
        assert updated_record['hash'] == 'updated_hash'
        assert updated_record['size'] == 500
    
    def test_update_file_record_nonexistent(self):
        """Test updating non-existent file record."""
        # Try to update a file that doesn't exist
        update_result = self.file_manager.update_file(999999, hash='updated_hash')
        assert update_result is False
    
    def test_mark_as_duplicate(self):
        """Test marking files as duplicates."""
        # Create two test files
        file1 = os.path.join(self.temp_dir, 'file1.txt')
        file2 = os.path.join(self.temp_dir, 'file2.txt')
        
        with open(file1, 'w') as f:
            f.write('duplicate content')
        with open(file2, 'w') as f:
            f.write('duplicate content')  # Same content
        
        file1_info = {
            'path': file1,
            'size': os.path.getsize(file1),
            'modified_time': os.path.getmtime(file1),
            'hash': 'duplicate_hash',
            'created_time': os.path.getctime(file1),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file2_info = {
            'path': file2,
            'size': os.path.getsize(file2),
            'modified_time': os.path.getmtime(file2),
            'hash': 'duplicate_hash',  # Same hash
            'created_time': os.path.getctime(file2),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file1_id = self.file_manager.add_file(file1_info['path'], file1_info['size'], file1_info['modified_time'], file1_info['hash'])
        file2_id = self.file_manager.add_file(file2_info['path'], file2_info['size'], file2_info['modified_time'], file2_info['hash'])
        
        # Mark file2 as duplicate of file1
        duplicate_result = self.file_manager.mark_as_duplicate(file2_id, file1_id)
        assert duplicate_result is True
        
        # Verify file2 is marked as duplicate
        file2_record = self.file_manager.get_file(file2_id)
        assert file2_record['is_duplicate'] is True
        assert file2_record['duplicate_of'] == file1_id
    
    def test_find_duplicates_by_hash(self):
        """Test finding duplicates by hash."""
        # Create test files with same hash
        file1 = os.path.join(self.temp_dir, 'dup1.txt')
        file2 = os.path.join(self.temp_dir, 'dup2.txt')
        file3 = os.path.join(self.temp_dir, 'unique.txt')
        
        with open(file1, 'w') as f:
            f.write('duplicate content')
        with open(file2, 'w') as f:
            f.write('duplicate content')  # Same as file1
        with open(file3, 'w') as f:
            f.write('unique content')
        
        file1_info = {
            'path': file1,
            'size': os.path.getsize(file1),
            'modified_time': os.path.getmtime(file1),
            'hash': 'duplicate_hash',
            'created_time': os.path.getctime(file1),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file2_info = {
            'path': file2,
            'size': os.path.getsize(file2),
            'modified_time': os.path.getmtime(file2),
            'hash': 'duplicate_hash',  # Same as file1
            'created_time': os.path.getctime(file2),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file3_info = {
            'path': file3,
            'size': os.path.getsize(file3),
            'modified_time': os.path.getmtime(file3),
            'hash': 'unique_hash',
            'created_time': os.path.getctime(file3),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        self.file_manager.add_file(file1_info['path'], file1_info['size'], file1_info['modified_time'], file1_info['hash'])
        self.file_manager.add_file(file2_info['path'], file2_info['size'], file2_info['modified_time'], file2_info['hash'])
        self.file_manager.add_file(file3_info['path'], file3_info['size'], file3_info['modified_time'], file3_info['hash'])
        
        # Find duplicates by hash
        duplicates = self.file_manager.find_duplicates_by_hash('duplicate_hash')
        assert len(duplicates) == 2  # Should find both duplicate files
        
        paths = [d['path'] for d in duplicates]
        assert file1 in paths
        assert file2 in paths
        assert file3 not in paths  # Should not include unique file
    
    def test_find_duplicates_by_size(self):
        """Test finding duplicates by size."""
        # Create test files with same size
        file1 = os.path.join(self.temp_dir, 'size1.txt')
        file2 = os.path.join(self.temp_dir, 'size2.txt')
        file3 = os.path.join(self.temp_dir, 'diff_size.txt')
        
        same_content = 'same size content'
        diff_content = 'different content'
        
        with open(file1, 'w') as f:
            f.write(same_content)
        with open(file2, 'w') as f:
            f.write(same_content)  # Same size as file1
        with open(file3, 'w') as f:
            f.write(diff_content)  # Different size
        
        file1_info = {
            'path': file1,
            'size': os.path.getsize(file1),
            'modified_time': os.path.getmtime(file1),
            'hash': 'hash1',
            'created_time': os.path.getctime(file1),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file2_info = {
            'path': file2,
            'size': os.path.getsize(file2),
            'modified_time': os.path.getmtime(file2),
            'hash': 'hash2',
            'created_time': os.path.getctime(file2),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file3_info = {
            'path': file3,
            'size': os.path.getsize(file3),
            'modified_time': os.path.getmtime(file3),
            'hash': 'hash3',
            'created_time': os.path.getctime(file3),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        self.file_manager.add_file(file1_info['path'], file1_info['size'], file1_info['modified_time'], file1_info['hash'])
        self.file_manager.add_file(file2_info['path'], file2_info['size'], file2_info['modified_time'], file2_info['hash'])
        self.file_manager.add_file(file3_info['path'], file3_info['size'], file3_info['modified_time'], file3_info['hash'])
        
        # Find duplicates by size
        size_duplicates = self.file_manager.find_duplicates_by_size(len(same_content))
        assert len(size_duplicates) >= 2  # Should find both same-size files
        
        paths = [d['path'] for d in size_duplicates]
        assert file1 in paths
        assert file2 in paths
    
    def test_get_all_files(self):
        """Test getting all files."""
        # Create multiple test files
        test_files = []
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f'all_files_test_{i}.txt')
            with open(file_path, 'w') as f:
                f.write(f'test content {i}')
            test_files.append(file_path)
        
        # Create file records
        for i, file_path in enumerate(test_files):
            file_info = {
                'path': file_path,
                'size': os.path.getsize(file_path),
                'modified_time': os.path.getmtime(file_path),
                'hash': f'hash_{i}',
                'created_time': os.path.getctime(file_path),
                'scanned_at': 1234567890 + i,
                'updated_at': 1234567890 + i
            }
            self.file_manager.add_file(file_info['path'], file_info['size'], file_info['modified_time'], file_info['hash'])
        
        # Get all files
        all_files = self.file_manager.get_all_files()
        assert len(all_files) == 5
        
        # Verify all files are present
        paths = [f['path'] for f in all_files]
        for test_file in test_files:
            assert test_file in paths
    
    def test_delete_file(self):
        """Test deleting file records."""
        # Create test file
        test_file = os.path.join(self.temp_dir, 'delete_test.txt')
        with open(test_file, 'w') as f:
            f.write('delete test content')
        
        file_info = {
            'path': test_file,
            'size': os.path.getsize(test_file),
            'modified_time': os.path.getmtime(test_file),
            'hash': 'delete_hash',
            'created_time': os.path.getctime(test_file),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file_id = self.file_manager.add_file(file_info['path'], file_info['size'], file_info['modified_time'], file_info['hash'])
        assert file_id is not None
        
        # Delete the file record
        delete_result = self.file_manager.delete_file(file_id)
        assert delete_result is True
        
        # Verify file is deleted
        deleted_record = self.file_manager.get_file(file_id)
        assert deleted_record is None
    
    def test_delete_file_nonexistent(self):
        """Test deleting non-existent file."""
        # Try to delete a file that doesn't exist
        delete_result = self.file_manager.delete_file(999999)
        assert delete_result is False
    
    def test_get_duplicate_files(self):
        """Test getting duplicate files."""
        # Create test files
        file1 = os.path.join(self.temp_dir, 'orig.txt')
        file2 = os.path.join(self.temp_dir, 'dup1.txt')
        file3 = os.path.join(self.temp_dir, 'dup2.txt')
        file4 = os.path.join(self.temp_dir, 'unique.txt')
        
        with open(file1, 'w') as f:
            f.write('original content')
        with open(file2, 'w') as f:
            f.write('original content')  # Duplicate
        with open(file3, 'w') as f:
            f.write('original content')  # Duplicate
        with open(file4, 'w') as f:
            f.write('unique content')
        
        file1_info = {
            'path': file1,
            'size': os.path.getsize(file1),
            'modified_time': os.path.getmtime(file1),
            'hash': 'orig_hash',
            'created_time': os.path.getctime(file1),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file2_info = {
            'path': file2,
            'size': os.path.getsize(file2),
            'modified_time': os.path.getmtime(file2),
            'hash': 'orig_hash',
            'created_time': os.path.getctime(file2),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file3_info = {
            'path': file3,
            'size': os.path.getsize(file3),
            'modified_time': os.path.getmtime(file3),
            'hash': 'orig_hash',
            'created_time': os.path.getctime(file3),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file4_info = {
            'path': file4,
            'size': os.path.getsize(file4),
            'modified_time': os.path.getmtime(file4),
            'hash': 'unique_hash',
            'created_time': os.path.getctime(file4),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file1_id = self.file_manager.add_file(file1_info['path'], file1_info['size'], file1_info['modified_time'], file1_info['hash'])
        file2_id = self.file_manager.add_file(file2_info['path'], file2_info['size'], file2_info['modified_time'], file2_info['hash'])
        file3_id = self.file_manager.add_file(file3_info['path'], file3_info['size'], file3_info['modified_time'], file3_info['hash'])
        self.file_manager.add_file(file4_info['path'], file4_info['size'], file4_info['modified_time'], file4_info['hash'])
        
        # Mark files as duplicates
        self.file_manager.mark_as_duplicate(file2_id, file1_id)
        self.file_manager.mark_as_duplicate(file3_id, file1_id)
        
        # Get duplicate files
        duplicate_files = self.file_manager.get_duplicate_files()
        assert len(duplicate_files) == 2  # Should find 2 duplicate files
        
        ids = [f['id'] for f in duplicate_files]
        assert file2_id in ids
        assert file3_id in ids
        assert file1_id not in ids  # Original file should not be in duplicates
    
    def test_get_original_files(self):
        """Test getting original (non-duplicate) files."""
        # Create test files
        file1 = os.path.join(self.temp_dir, 'orig.txt')
        file2 = os.path.join(self.temp_dir, 'dup1.txt')
        file3 = os.path.join(self.temp_dir, 'unique.txt')
        
        with open(file1, 'w') as f:
            f.write('original content')
        with open(file2, 'w') as f:
            f.write('original content')  # Duplicate
        with open(file3, 'w') as f:
            f.write('unique content')
        
        file1_info = {
            'path': file1,
            'size': os.path.getsize(file1),
            'modified_time': os.path.getmtime(file1),
            'hash': 'orig_hash',
            'created_time': os.path.getctime(file1),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file2_info = {
            'path': file2,
            'size': os.path.getsize(file2),
            'modified_time': os.path.getmtime(file2),
            'hash': 'orig_hash',
            'created_time': os.path.getctime(file2),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file3_info = {
            'path': file3,
            'size': os.path.getsize(file3),
            'modified_time': os.path.getmtime(file3),
            'hash': 'unique_hash',
            'created_time': os.path.getctime(file3),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file1_id = self.file_manager.add_file(file1_info['path'], file1_info['size'], file1_info['modified_time'], file1_info['hash'])
        file2_id = self.file_manager.add_file(file2_info['path'], file2_info['size'], file2_info['modified_time'], file2_info['hash'])
        file3_id = self.file_manager.add_file(file3_info['path'], file3_info['size'], file3_info['modified_time'], file3_info['hash'])
        
        # Mark file2 as duplicate
        self.file_manager.mark_as_duplicate(file2_id, file1_id)
        
        # Get original files
        original_files = self.file_manager.get_original_files()
        assert len(original_files) == 2  # Should find 2 original files (file1 and file3)
        
        ids = [f['id'] for f in original_files]
        assert file1_id in ids  # Original file
        assert file3_id in ids  # Unique file
        assert file2_id not in ids  # Duplicate file should not be included
    
    def test_count_files(self):
        """Test counting total files."""
        # Initially should be 0
        assert self.file_manager.count_files() == 0
        
        # Add some files
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f'count_test_{i}.txt')
            with open(file_path, 'w') as f:
                f.write(f'count test {i}')
            
            file_info = {
                'path': file_path,
                'size': os.path.getsize(file_path),
                'modified_time': os.path.getmtime(file_path),
                'hash': f'count_hash_{i}',
                'created_time': os.path.getctime(file_path),
                'scanned_at': 1234567890 + i,
                'updated_at': 1234567890 + i
            }
            self.file_manager.add_file(file_info['path'], file_info['size'], file_info['modified_time'], file_info['hash'])
        
        # Should count 3 files
        assert self.file_manager.count_files() == 3
    
    def test_count_duplicates(self):
        """Test counting duplicate files."""
        # Initially should be 0
        assert self.file_manager.count_duplicates() == 0
        
        # Create test files
        file1 = os.path.join(self.temp_dir, 'count_orig.txt')
        file2 = os.path.join(self.temp_dir, 'count_dup1.txt')
        file3 = os.path.join(self.temp_dir, 'count_dup2.txt')
        
        with open(file1, 'w') as f:
            f.write('original content')
        with open(file2, 'w') as f:
            f.write('original content')  # Duplicate
        with open(file3, 'w') as f:
            f.write('original content')  # Duplicate
        
        file1_info = {
            'path': file1,
            'size': os.path.getsize(file1),
            'modified_time': os.path.getmtime(file1),
            'hash': 'count_orig_hash',
            'created_time': os.path.getctime(file1),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file2_info = {
            'path': file2,
            'size': os.path.getsize(file2),
            'modified_time': os.path.getmtime(file2),
            'hash': 'count_orig_hash',
            'created_time': os.path.getctime(file2),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file3_info = {
            'path': file3,
            'size': os.path.getsize(file3),
            'modified_time': os.path.getmtime(file3),
            'hash': 'count_orig_hash',
            'created_time': os.path.getctime(file3),
            'scanned_at': 1234567890,
            'updated_at': 1234567890
        }
        
        file1_id = self.file_manager.add_file(file1_info['path'], file1_info['size'], file1_info['modified_time'], file1_info['hash'])
        file2_id = self.file_manager.add_file(file2_info['path'], file2_info['size'], file2_info['modified_time'], file2_info['hash'])
        file3_id = self.file_manager.add_file(file3_info['path'], file3_info['size'], file3_info['modified_time'], file3_info['hash'])
        
        # Mark files as duplicates
        self.file_manager.mark_as_duplicate(file2_id, file1_id)
        self.file_manager.mark_as_duplicate(file3_id, file1_id)
        
        # Should count 2 duplicate files
        assert self.file_manager.count_duplicates() == 2
    
    def test_batch_add_files(self):
        """Test batch adding multiple files."""
        # Create multiple test files
        test_files = []
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f'batch_test_{i}.txt')
            with open(file_path, 'w') as f:
                f.write(f'batch test content {i}')
            test_files.append({
                'path': file_path,
                'size': os.path.getsize(file_path),
                'modified_time': os.path.getmtime(file_path),
                'hash': f'batch_hash_{i}',
                'created_time': os.path.getctime(file_path),
                'scanned_at': 1234567890 + i,
                'updated_at': 1234567890 + i
            })
        
        # Batch add files
        added_count = self.file_manager.batch_add_files(test_files)
        assert added_count == 5
        
        # Verify all files were added
        all_files = self.file_manager.get_all_files()
        assert len(all_files) == 5
        
        # Verify file contents
        for i, file_data in enumerate(test_files):
            record = self.file_manager.get_file_by_path(file_data['path'])
            assert record is not None
            assert record['hash'] == f'batch_hash_{i}'
            assert record['size'] == file_data['size']
    
    def test_clear_all_files(self):
        """Test clearing all file records."""
        # Add some test files
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f'clear_test_{i}.txt')
            with open(file_path, 'w') as f:
                f.write(f'clear test {i}')
            
            file_info = {
                'path': file_path,
                'size': os.path.getsize(file_path),
                'modified_time': os.path.getmtime(file_path),
                'hash': f'clear_hash_{i}',
                'created_time': os.path.getctime(file_path),
                'scanned_at': 1234567890 + i,
                'updated_at': 1234567890 + i
            }
            self.file_manager.add_file(file_info['path'], file_info['size'], file_info['modified_time'], file_info['hash'])
        
        # Verify files exist
        assert self.file_manager.count_files() == 3
        
        # Clear all files
        self.file_manager.clear_all_files()
        
        # Verify all files are cleared
        assert self.file_manager.count_files() == 0
        all_files = self.file_manager.get_all_files()
        assert len(all_files) == 0


def test_file_record_manager_class_creation():
    """Test that FileRecordManager class can be instantiated."""
    db_path = os.path.join(tempfile.gettempdir(), 'test_creation.db')
    
    try:
        db_connection = DatabaseConnection(db_path=db_path)
        db_connection.initialize_database()
        
        file_manager = FileRepository(db_connection)  # Changed to correct class name
        assert file_manager is not None
        assert hasattr(file_manager, 'add_file')  # Changed to correct method name
        assert hasattr(file_manager, 'get_file')
        assert hasattr(file_manager, 'get_file_by_path')
        assert hasattr(file_manager, 'update_file')
        assert hasattr(file_manager, 'mark_as_duplicate')
        assert hasattr(file_manager, 'find_duplicates_by_hash')
        assert hasattr(file_manager, 'find_duplicates_by_size')
        assert hasattr(file_manager, 'get_all_files')
        assert hasattr(file_manager, 'delete_file')
        assert hasattr(file_manager, 'get_duplicate_files')
        assert hasattr(file_manager, 'get_original_files')
        assert hasattr(file_manager, 'count_files')
        assert hasattr(file_manager, 'count_duplicates')
        assert hasattr(file_manager, 'batch_add_files')
        assert hasattr(file_manager, 'clear_all_files')
        
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_get_file_repository_function():
    """Test the get_file_repository function."""
    from nodupe.core.database.files import get_file_repository
    
    # Test with default path
    repo = get_file_repository()
    assert repo is not None
    assert isinstance(repo, FileRepository)  # Changed to correct class name
    
    # Test with custom path
    custom_path = os.path.join(tempfile.gettempdir(), 'custom_repo.db')
    try:
        custom_repo = get_file_repository(custom_path)
        assert custom_repo is not None
        assert isinstance(custom_repo, FileRepository)  # Changed to correct class name
    finally:
        if os.path.exists(custom_path):
            os.remove(custom_path)


if __name__ == "__main__":
    pytest.main([__file__])
