#!/usr/bin/env python3
"""Batch update all plugins to UUID specification.

This script systematically updates all plugins in the NoDupeLabs project
to follow the UUID specification for naming and metadata.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# UUID mappings for plugins
PLUGIN_UUIDS = {
    "archive": "b1c2d3e4-f5a6-7890-abcd-ef1234567890",
    "mount": "c1d2e3f4-a5b6-7890-abcd-ef1234567890", 
    "plan": "d1e2f3a4-b5c6-7890-abcd-ef1234567890",
    "rollback": "e1f2a3b4-c5d6-7890-abcd-ef1234567890",
    "verify": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "accessibility": "a1b2c3d4-e5f6-7890-abcd-ef1234567891",
    "leap_year": "b1c2d3e4-f5a6-7890-abcd-ef1234567891",
    "time_sync": "c1d2e3f4-a5b6-7890-abcd-ef1234567891",
    "similarity_backend": "d1e2f3a4-b5c6-7890-abcd-ef1234567891",
    "scan_enhanced": "e1f2a3b4-c5d6-7890-abcd-ef1234567891"
}

PLUGIN_CATEGORIES = {
    "archive": "utility",
    "mount": "utility", 
    "plan": "utility",
    "rollback": "utility",
    "verify": "utility",
    "accessibility": "ui",
    "leap_year": "utility",
    "time_sync": "utility",
    "similarity_backend": "ml",
    "scan_enhanced": "scanning"
}

PLUGIN_DESCRIPTIONS = {
    "archive": "Archive plugin implementation",
    "mount": "Mount plugin implementation",
    "plan": "Plan plugin implementation",
    "rollback": "Rollback plugin implementation", 
    "verify": "Verify plugin implementation",
    "accessibility": "Accessibility plugin implementation",
    "leap_year": "Leap year plugin implementation",
    "time_sync": "Time sync plugin implementation",
    "similarity_backend": "Similarity search backend plugin",
    "scan_enhanced": "Enhanced scan plugin with Cascade-Autotune integration"
}


def generate_plugin_metadata(plugin_name: str) -> str:
    """Generate UUID-based plugin metadata."""
    uuid = PLUGIN_UUIDS.get(plugin_name)
    if not uuid:
        raise ValueError(f"No UUID defined for plugin: {plugin_name}")
    
    category = PLUGIN_CATEGORIES.get(plugin_name, "utility")
    description = PLUGIN_DESCRIPTIONS.get(plugin_name, f"{plugin_name} plugin")
    
    return f'''# Plugin metadata (UUID-based specification)
PLUGIN_METADATA = {{
    "uuid": "{uuid}",
    "name": "{plugin_name}",
    "display_name": "{description}",
    "version": "v1.0.0",
    "description": "{description}",
    "author": "NoDupeLabs Team",
    "category": "{category}",
    "dependencies": [],
    "compatibility": {{
        "python": ">=3.9",
        "nodupe_core": ">=1.0.0"
    }},
    "tags": ["{category}", "plugin"],
    "marketplace_id": "{plugin_name}_{uuid}"
}}
'''


def update_plugin_file(file_path: Path) -> bool:
    """Update a single plugin file to UUID specification."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract plugin name from filename
        plugin_name = file_path.stem
        
        # Check if already has UUID metadata
        if 'PLUGIN_METADATA' in content:
            print(f"  [SKIP] {plugin_name} already has UUID metadata")
            return False
        
        # Generate new metadata
        metadata = generate_plugin_metadata(plugin_name)
        
        # Find the import section and add metadata after imports
        import_pattern = r'^(.*?)(from nodupe\.core\.plugin_system\.base import Plugin.*?)$'
        match = re.search(import_pattern, content, re.DOTALL | re.MULTILINE)
        
        if match:
            # Insert metadata after the import section
            before_imports = match.group(1)
            imports = match.group(2)
            after_imports = content[match.end():]
            
            new_content = before_imports + imports + '\n\n' + metadata + after_imports
            
            # Update class initialization
            class_pattern = rf'class {plugin_name.title()}Plugin\(Plugin\):'
            if re.search(class_pattern, new_content):
                # Replace class definition
                new_class_def = f'''class {plugin_name.title()}Plugin(Plugin):
    """{plugin_name} plugin implementation."""

    def __init__(self):
        """Initialize {plugin_name} plugin with UUID metadata."""
        super().__init__(PLUGIN_METADATA)'''
                
                new_content = re.sub(
                    rf'class {plugin_name.title()}Plugin\(Plugin\):.*?def __init__\(self\):.*?"""Initialize.*?plugin.*?"""',
                    new_class_def,
                    new_content,
                    flags=re.DOTALL
                )
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"  [UPDATED] {plugin_name}")
            return True
        else:
            print(f"  [ERROR] Could not find import pattern in {plugin_name}")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Failed to update {plugin_name}: {e}")
        return False


def find_plugin_files() -> List[Path]:
    """Find all plugin files that need updating."""
    plugin_files = []
    
    # Search in plugins directory
    plugins_dir = Path("nudupe/plugins")
    if plugins_dir.exists():
        for py_file in plugins_dir.rglob("*.py"):
            # Skip __init__.py files and already updated files
            if (py_file.name != "__init__.py" and 
                "PLUGIN_METADATA" not in py_file.read_text()):
                
                # Check if it contains a Plugin class
                content = py_file.read_text()
                if re.search(r'class.*Plugin\(Plugin\):', content):
                    plugin_files.append(py_file)
    
    return plugin_files


def main():
    """Main function to update all plugins."""
    print("Updating NoDupeLabs plugins to UUID specification...")
    print("=" * 60)
    
    # Find plugin files
    plugin_files = find_plugin_files()
    
    if not plugin_files:
        print("No plugin files found to update.")
        return
    
    print(f"Found {len(plugin_files)} plugin files to update:")
    for file_path in plugin_files:
        print(f"  - {file_path}")
    
    print("\nUpdating plugins...")
    print("-" * 40)
    
    updated_count = 0
    for file_path in plugin_files:
        if update_plugin_file(file_path):
            updated_count += 1
    
    print("-" * 40)
    print(f"Updated {updated_count} plugins to UUID specification.")
    
    if updated_count > 0:
        print("\nNext steps:")
        print("1. Test the updated plugins")
        print("2. Update any plugin discovery code if needed")
        print("3. Update documentation")
        print("4. Consider renaming files to UUID format")


if __name__ == "__main__":
    main()
