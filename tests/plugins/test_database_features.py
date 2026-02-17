"""Tests for database feature tools."""

import os
import tempfile
from unittest.mock import Mock

import pytest

from nodupe.tools.database.features import (
    DatabaseExportTool,
    DatabaseImportTool,
    DatabaseReplicationTool,
    DatabaseShardingTool,
)


class TestDatabaseShardingTool:
    """Test DatabaseShardingTool functionality."""

    def test_initialization(self):
        """Test tool initialization."""
        tool = DatabaseShardingTool()

        assert tool.name == "DatabaseSharding"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []
        assert tool.get_capabilities() == {
            "sharding": True,
            "horizontal_partitioning": True,
            "create_shard": True,
        }

    def test_metadata(self):
        """Test tool metadata."""
        tool = DatabaseShardingTool()
        metadata = tool.metadata

        assert metadata.name == "DatabaseSharding"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "database" in metadata.tags
        assert "sharding" in metadata.tags

    def test_initialize_shutdown(self):
        """Test tool initialization and shutdown."""
        tool = DatabaseShardingTool()
        container = Mock()

        # This should not raise an exception
        tool.initialize(container)
        tool.shutdown(container)

    def test_create_shard(self):
        """Test shard creation."""
        tool = DatabaseShardingTool()

        with tempfile.TemporaryDirectory() as temp_dir:
            shard_path = os.path.join(temp_dir, "test_shard.db")

            # Create a shard
            result_path = tool.create_shard("test_shard", shard_path)

            # Verify the path is correct
            assert result_path == shard_path
            assert os.path.exists(result_path)

    def test_create_shard_invalid_name(self):
        """Test shard creation with invalid name."""
        tool = DatabaseShardingTool()

        with pytest.raises(ValueError):
            tool.create_shard("invalid name with spaces")

    def test_list_shards(self):
        """Test listing shards."""
        tool = DatabaseShardingTool()

        # Initially empty
        shards = tool.list_shards()
        assert shards == []


class TestDatabaseReplicationTool:
    """Test DatabaseReplicationTool functionality."""

    def test_initialization(self):
        """Test tool initialization."""
        tool = DatabaseReplicationTool()

        assert tool.name == "DatabaseReplication"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []
        assert tool.get_capabilities() == {
            "replication": True,
            "data_redundancy": True,
            "sync_data": True,
        }

    def test_metadata(self):
        """Test tool metadata."""
        tool = DatabaseReplicationTool()
        metadata = tool.metadata

        assert metadata.name == "DatabaseReplication"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "database" in metadata.tags
        assert "replication" in metadata.tags

    def test_initialize_shutdown(self):
        """Test tool initialization and shutdown."""
        tool = DatabaseReplicationTool()
        container = Mock()

        # This should not raise an exception
        tool.initialize(container)
        tool.shutdown(container)


class TestDatabaseExportTool:
    """Test DatabaseExportTool functionality."""

    def test_initialization(self):
        """Test tool initialization."""
        tool = DatabaseExportTool()

        assert tool.name == "DatabaseExport"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []
        assert tool.get_capabilities() == {
            "export": True,
            "data_migration": True,
            "format_conversion": True,
        }

    def test_metadata(self):
        """Test tool metadata."""
        tool = DatabaseExportTool()
        metadata = tool.metadata

        assert metadata.name == "DatabaseExport"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "database" in metadata.tags
        assert "export" in metadata.tags

    def test_initialize_shutdown(self):
        """Test tool initialization and shutdown."""
        tool = DatabaseExportTool()
        container = Mock()

        # This should not raise an exception
        tool.initialize(container)
        tool.shutdown(container)


class TestDatabaseImportTool:
    """Test DatabaseImportTool functionality."""

    def test_initialization(self):
        """Test tool initialization."""
        tool = DatabaseImportTool()

        assert tool.name == "DatabaseImport"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []
        assert tool.get_capabilities() == {
            "import": True,
            "data_migration": True,
            "format_conversion": True,
        }

    def test_metadata(self):
        """Test tool metadata."""
        tool = DatabaseImportTool()
        metadata = tool.metadata

        assert metadata.name == "DatabaseImport"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "database" in metadata.tags
        assert "import" in metadata.tags

    def test_initialize_shutdown(self):
        """Test tool initialization and shutdown."""
        tool = DatabaseImportTool()
        container = Mock()

        # This should not raise an exception
        tool.initialize(container)
        tool.shutdown(container)


class TestDatabaseFeatureIntegration:
    """Test integration between database feature tools."""

    def test_all_tools_compatible_with_registry(self):
        """Test that all tools are compatible with the tool registry."""
        tools = [
            DatabaseShardingTool(),
            DatabaseReplicationTool(),
            DatabaseExportTool(),
            DatabaseImportTool()
        ]

        for tool in tools:
            # Verify all required properties exist
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'version')
            assert hasattr(tool, 'dependencies')
            assert hasattr(tool, 'get_capabilities')
            assert hasattr(tool, 'metadata')
            assert hasattr(tool, 'initialize')
            assert hasattr(tool, 'shutdown')

            # Verify metadata properties
            metadata = tool.metadata
            assert hasattr(metadata, 'name')
            assert hasattr(metadata, 'version')
            assert hasattr(metadata, 'author')
            assert hasattr(metadata, 'license')
            assert hasattr(metadata, 'dependencies')
            assert hasattr(metadata, 'tags')


def test_metadata_immutability():
    """Test that tool metadata is immutable."""
    tool = DatabaseShardingTool()
    metadata = tool.metadata

    # Attempt to modify metadata should raise an exception
    try:
        metadata.name = "NewName"
        assert False, "Expected metadata to be immutable"
    except:
        # Expected behavior - metadata should be immutable
        pass

    # Verify the name is still the original
    assert metadata.name == "DatabaseSharding"
