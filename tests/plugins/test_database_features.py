"""Tests for database feature plugins."""

import os
import tempfile
import pytest
from unittest.mock import Mock

from nodupe.plugins.database.features import (
    DatabaseShardingPlugin,
    DatabaseReplicationPlugin,
    DatabaseExportPlugin,
    DatabaseImportPlugin
)


class TestDatabaseShardingPlugin:
    """Test DatabaseShardingPlugin functionality."""
    
    def test_initialization(self):
        """Test plugin initialization."""
        plugin = DatabaseShardingPlugin()
        
        assert plugin.name == "DatabaseSharding"
        assert plugin.version == "1.0.0"
        assert plugin.dependencies == []
        assert plugin.get_capabilities() == {
            "sharding": True,
            "horizontal_partitioning": True,
            "create_shard": True,
        }
    
    def test_metadata(self):
        """Test plugin metadata."""
        plugin = DatabaseShardingPlugin()
        metadata = plugin.metadata
        
        assert metadata.name == "DatabaseSharding"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "database" in metadata.tags
        assert "sharding" in metadata.tags
    
    def test_initialize_shutdown(self):
        """Test plugin initialization and shutdown."""
        plugin = DatabaseShardingPlugin()
        container = Mock()
        
        # This should not raise an exception
        plugin.initialize(container)
        plugin.shutdown(container)
    
    def test_create_shard(self):
        """Test shard creation."""
        plugin = DatabaseShardingPlugin()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            shard_path = os.path.join(temp_dir, "test_shard.db")
            
            # Create a shard
            result_path = plugin.create_shard("test_shard", shard_path)
            
            # Verify the path is correct
            assert result_path == shard_path
            assert os.path.exists(result_path)
    
    def test_create_shard_invalid_name(self):
        """Test shard creation with invalid name."""
        plugin = DatabaseShardingPlugin()
        
        with pytest.raises(ValueError):
            plugin.create_shard("invalid name with spaces")
    
    def test_list_shards(self):
        """Test listing shards."""
        plugin = DatabaseShardingPlugin()
        
        # Initially empty
        shards = plugin.list_shards()
        assert shards == []


class TestDatabaseReplicationPlugin:
    """Test DatabaseReplicationPlugin functionality."""
    
    def test_initialization(self):
        """Test plugin initialization."""
        plugin = DatabaseReplicationPlugin()
        
        assert plugin.name == "DatabaseReplication"
        assert plugin.version == "1.0.0"
        assert plugin.dependencies == []
        assert plugin.get_capabilities() == {
            "replication": True,
            "data_redundancy": True,
            "sync_data": True,
        }
    
    def test_metadata(self):
        """Test plugin metadata."""
        plugin = DatabaseReplicationPlugin()
        metadata = plugin.metadata
        
        assert metadata.name == "DatabaseReplication"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "database" in metadata.tags
        assert "replication" in metadata.tags
    
    def test_initialize_shutdown(self):
        """Test plugin initialization and shutdown."""
        plugin = DatabaseReplicationPlugin()
        container = Mock()
        
        # This should not raise an exception
        plugin.initialize(container)
        plugin.shutdown(container)


class TestDatabaseExportPlugin:
    """Test DatabaseExportPlugin functionality."""
    
    def test_initialization(self):
        """Test plugin initialization."""
        plugin = DatabaseExportPlugin()
        
        assert plugin.name == "DatabaseExport"
        assert plugin.version == "1.0.0"
        assert plugin.dependencies == []
        assert plugin.get_capabilities() == {
            "export": True,
            "data_migration": True,
            "format_conversion": True,
        }
    
    def test_metadata(self):
        """Test plugin metadata."""
        plugin = DatabaseExportPlugin()
        metadata = plugin.metadata
        
        assert metadata.name == "DatabaseExport"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "database" in metadata.tags
        assert "export" in metadata.tags
    
    def test_initialize_shutdown(self):
        """Test plugin initialization and shutdown."""
        plugin = DatabaseExportPlugin()
        container = Mock()
        
        # This should not raise an exception
        plugin.initialize(container)
        plugin.shutdown(container)


class TestDatabaseImportPlugin:
    """Test DatabaseImportPlugin functionality."""
    
    def test_initialization(self):
        """Test plugin initialization."""
        plugin = DatabaseImportPlugin()
        
        assert plugin.name == "DatabaseImport"
        assert plugin.version == "1.0.0"
        assert plugin.dependencies == []
        assert plugin.get_capabilities() == {
            "import": True,
            "data_migration": True,
            "format_conversion": True,
        }
    
    def test_metadata(self):
        """Test plugin metadata."""
        plugin = DatabaseImportPlugin()
        metadata = plugin.metadata
        
        assert metadata.name == "DatabaseImport"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "database" in metadata.tags
        assert "import" in metadata.tags
    
    def test_initialize_shutdown(self):
        """Test plugin initialization and shutdown."""
        plugin = DatabaseImportPlugin()
        container = Mock()
        
        # This should not raise an exception
        plugin.initialize(container)
        plugin.shutdown(container)


class TestDatabaseFeatureIntegration:
    """Test integration between database feature plugins."""
    
    def test_all_plugins_compatible_with_registry(self):
        """Test that all plugins are compatible with the plugin registry."""
        plugins = [
            DatabaseShardingPlugin(),
            DatabaseReplicationPlugin(),
            DatabaseExportPlugin(),
            DatabaseImportPlugin()
        ]
        
        for plugin in plugins:
            # Verify all required properties exist
            assert hasattr(plugin, 'name')
            assert hasattr(plugin, 'version')
            assert hasattr(plugin, 'dependencies')
            assert hasattr(plugin, 'get_capabilities')
            assert hasattr(plugin, 'metadata')
            assert hasattr(plugin, 'initialize')
            assert hasattr(plugin, 'shutdown')
            
            # Verify metadata properties
            metadata = plugin.metadata
            assert hasattr(metadata, 'name')
            assert hasattr(metadata, 'version')
            assert hasattr(metadata, 'author')
            assert hasattr(metadata, 'license')
            assert hasattr(metadata, 'dependencies')
            assert hasattr(metadata, 'tags')


def test_metadata_immutability():
    """Test that plugin metadata is immutable."""
    plugin = DatabaseShardingPlugin()
    metadata = plugin.metadata
    
    # Attempt to modify metadata should raise an exception
    try:
        metadata.name = "NewName"
        assert False, "Expected metadata to be immutable"
    except:
        # Expected behavior - metadata should be immutable
        pass
    
    # Verify the name is still the original
    assert metadata.name == "DatabaseSharding"