#!/usr/bin/env python3
"""Scaffold a new plugin for NoDupeLabs."""
import sys
from pathlib import Path


PLUGIN_TEMPLATES = {
    'similarity': '''"""Similarity plugin for {name}."""
from nodupe.core.plugins import SimilarityCommandPlugin


class {class_name}(SimilarityCommandPlugin):
    """Plugin description."""

    name: str = "{name}"
    version: str = "1.0.0"

    def execute(self, args):
        """Execute the plugin."""
        pass
''',
    'database': '''"""Database plugin for {name}."""
from nodupe.core.plugins import DatabasePlugin


class {class_name}(DatabasePlugin):
    """Plugin description."""

    name: str = "{name}"
    version: str = "1.0.0"

    def connect(self):
        """Connect to database."""
        pass

    def execute(self, args):
        """Execute the plugin."""
        pass
''',
    'command': '''"""Command plugin for {name}."""
from nodupe.core.plugins import CommandPlugin


class {class_name}(CommandPlugin):
    """Plugin description."""

    name: str = "{name}"
    version: str = "1.0.0"

    def execute(self, args):
        """Execute the command."""
        pass
''',
}


def create_plugin(plugin_type: str, name: str) -> None:
    """Create a new plugin scaffold."""
    if plugin_type not in PLUGIN_TEMPLATES:
        print(f"Unknown plugin type: {plugin_type}")
        print(f"Available types: {', '.join(PLUGIN_TEMPLATES.keys())}")
        sys.exit(1)
    
    # Create class name from name (PascalCase)
    class_name = ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))
    
    # Determine output path
    plugin_dir = Path('nodupe/plugins') / plugin_type
    output_file = plugin_dir / f'{name}.py'
    
    if output_file.exists():
        print(f"Error: {output_file} already exists")
        sys.exit(1)
    
    # Create directory if needed
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate and write template
    template = PLUGIN_TEMPLATES[plugin_type]
    content = template.format(name=name, class_name=class_name)
    output_file.write_text(content)
    
    print(f"Created: {output_file}")
    print(f"Plugin type: {plugin_type}")
    print(f"Class: {class_name}")


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 3:
        print('Usage: plugin_scaffold.py <type> <name>')
        print(f'Available types: {", ".join(PLUGIN_TEMPLATES.keys())}')
        print('')
        print('Examples:')
        print('  python tools/plugins/plugin_scaffold.py similarity my_similarity')
        print('  python tools/plugins/plugin_scaffold.py database my_database')
        print('  python tools/plugins/plugin_scaffold.py command my_command')
        return 1
    
    plugin_type = sys.argv[1]
    name = sys.argv[2]
    
    create_plugin(plugin_type, name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
