
import pytest
import shutil
import json
import os
from pathlib import Path
from argparse import Namespace
from nodupe.core.container import ServiceContainer
from nodupe.core.database.connection import DatabaseConnection
from nodupe.core.database.files import FileRepository
from nodupe.plugins.commands.scan import ScanPlugin
from nodupe.plugins.commands.similarity import SimilarityCommandPlugin
from nodupe.plugins.commands.plan import PlanPlugin
from nodupe.plugins.commands.apply import ApplyPlugin

@pytest.fixture
def db_connection():
    # Use memory database for speed and isolation
    db = DatabaseConnection(":memory:")
    # Initialize basic schema if needed (FileRepository does this usually? No, SchemaManager does)
    # Checking implementation: SchemaManager handles it. FileRepo might assume table exists.
    # Let's ensure schema.
    from nodupe.core.database.schema import DatabaseSchema
    schema = DatabaseSchema(db.get_connection())
    schema.create_schema()
    return db

@pytest.fixture
def container(db_connection):
    c = ServiceContainer()
    c.register_service('database', db_connection)
    # Similarity Manager is technically optional for hash-based check but code checks for it.
    # We can skip it or mock it if needed, but the unified code falls back nicely.
    return c

@pytest.fixture
def test_data(temp_dir):
    # Create structure:
    # root/
    #   original.txt (content A)
    #   dup1.txt (content A)
    #   sub/
    #     dup2.txt (content A)
    #   unique.txt (content B)
    
    root = temp_dir / "data"
    root.mkdir()
    (root / "sub").mkdir()
    
    content_a = "Duplicate content A"
    content_b = "Unique content B"
    
    (root / "original.txt").write_text(content_a)
    (root / "dup1.txt").write_text(content_a)
    (root / "sub" / "dup2.txt").write_text(content_a)
    (root / "unique.txt").write_text(content_b)
    
    return root

def test_full_workflow(container, test_data, temp_dir):
    """Verify the full workflow: Scan -> Similarity -> Plan -> Apply"""
    
    db = container.get_service('database')
    repo = FileRepository(db)
    
    # -------------------------------------------------------------------------
    # 1. SCAN
    # -------------------------------------------------------------------------
    scan_plugin = ScanPlugin()
    args_scan = Namespace(
        paths=[str(test_data)],
        exclude=[],
        min_size=0,
        max_size=None,
        extensions=None,
        verbose=True,
        container=container
    )
    
    exit_code = scan_plugin.execute_scan(args_scan)
    assert exit_code == 0
    
    files = repo.get_all_files()
    assert len(files) == 4
    
    # -------------------------------------------------------------------------
    # 2. SIMILARITY (Hash)
    # -------------------------------------------------------------------------
    sim_plugin = SimilarityCommandPlugin()
    args_sim = Namespace(
        metric='hash',
        verbose=True,
        container=container
    )
    
    exit_code = sim_plugin.execute_similarity(args_sim)
    assert exit_code == 0
    
    # Verify duplicates marked in DB
    # We expect 2 duplicate records (for dup1 and sub/dup2) and 1 original
    # (or some permuntation depending on sorting)
    duplicates = repo.get_duplicate_files()
    assert len(duplicates) == 2
    
    # Verify unique file is NOT duplicate
    unique_file = repo.get_file_by_path(str(test_data / "unique.txt"))
    assert unique_file['is_duplicate'] is False

    # -------------------------------------------------------------------------
    # 3. PLAN
    # -------------------------------------------------------------------------
    plan_plugin = PlanPlugin()
    plan_output = temp_dir / "test_plan.json"
    args_plan = Namespace(
        strategy='newest', # or oldest
        output=str(plan_output),
        container=container
    )
    
    exit_code = plan_plugin.execute_plan(args_plan)
    assert exit_code == 0
    assert plan_output.exists()
    
    with open(plan_output) as f:
        plan = json.load(f)
        
    assert plan['metadata']['stats']['duplicates_found'] == 2
    assert len(plan['actions']) >= 2 # 2 Deletes + 1 Keep usually
    
    # -------------------------------------------------------------------------
    # 4. APPLY (Move)
    # -------------------------------------------------------------------------
    apply_plugin = ApplyPlugin()
    move_dest = temp_dir / "moved_duplicates"
    args_apply = Namespace(
        plan=str(plan_output),
        action='move',
        destination=str(move_dest),
        dry_run=False,
        verbose=True,
        container=container
    )
    
    exit_code = apply_plugin.execute_apply(args_apply)
    assert exit_code == 0
    
    # Verify files moved
    assert move_dest.exists()
    moved_files = list(move_dest.glob("**/*.txt"))
    assert len(moved_files) >= 2  # At least 2 duplicates moved
    
    # Verify correct number of files remain: 1 keeper from dup group + unique.txt
    remaining = list(test_data.glob("**/*.txt"))
    assert len(remaining) == 2  # 1 keeper + 1 unique 
