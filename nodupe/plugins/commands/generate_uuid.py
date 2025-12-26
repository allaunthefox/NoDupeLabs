"""UUID Generation plugin for NoDupeLabs.

This plugin provides UUID generation functionality as a standard command
for the NoDupeLabs project. It demonstrates how to create utility plugins
that provide system-wide functionality.

Key Features:
    - Generate RFC 9562 compliant UUID v4
    - Generate UUID-based plugin filenames
    - Validate UUID format
    - Generate marketplace IDs
    - Plugin metadata generation templates
    - Batch UUID generation
    - Standard library only (no external dependencies)

Dependencies:
    - Core modules
    - UUID utilities
"""

from typing import Any, Dict, List
import argparse
import json
from pathlib import Path
from uuid import UUID

# Try to import rich for enhanced formatting, fall back to basic if not available
try:
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
    from rich.panel import Panel
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None
    Table = None
    Panel = None
    Syntax = None
    rprint = print

from nodupe.core.plugin_system.base import Plugin
from nodupe.core.plugin_system.uuid_utils import UUIDUtils


# Plugin metadata (UUID-based specification)
PLUGIN_METADATA = {
    "uuid": "f1a2b3c4-d5e6-4890-abcd-ef1234567890",
    "name": "generate_uuid",
    "display_name": "UUID Generation Plugin",
    "version": "v1.0.0",
    "description": "Generate RFC 9562 compliant UUIDs for plugins and modules",
    "author": "NoDupeLabs Team",
    "category": "utility",
    "dependencies": [],
    "compatibility": {
        "python": ">=3.9",
        "nodupe_core": ">=1.0.0"
    },
    "tags": ["uuid", "generation", "plugin-development", "utility"],
    "marketplace_id": "generate_uuid_f1a2b3c4-d5e6-4890-abcd-ef1234567890"
}


class GenerateUUIDPlugin(Plugin):
    """UUID generation plugin for NoDupeLabs.

    Provides standard UUID generation functionality for the project,
    including plugin metadata generation and validation tools.
    """

    def __init__(self):
        """Initialize UUID generation plugin with UUID metadata."""
        super().__init__(PLUGIN_METADATA)

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._initialized = False

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {
            'commands': ['generate-uuid', 'uuid-validate', 'uuid-plugin-template'],
            'features': ['uuid_generation', 'plugin_metadata_generation', 'validation']
        }

    def register_commands(self, subparsers: Any) -> None:
        """Register UUID generation commands with argument parser."""
        
        # Main UUID generation command
        uuid_parser = subparsers.add_parser('generate-uuid', help='Generate RFC 9562 compliant UUIDs')
        uuid_subparsers = uuid_parser.add_subparsers(dest='uuid_action', help='UUID action to perform')
        
        # Generate single UUID
        gen_parser = uuid_subparsers.add_parser('generate', help='Generate a single UUID')
        gen_parser.add_argument('--count', '-n', type=int, default=1, help='Number of UUIDs to generate')
        gen_parser.add_argument('--format', choices=['simple', 'urn', 'canonical'], default='canonical', help='Output format')
        gen_parser.add_argument('--output', '-o', help='Output file (JSON format)')
        gen_parser.set_defaults(func=self.execute_generate_uuid)
        
        # Validate UUID
        validate_parser = uuid_subparsers.add_parser('validate', help='Validate UUID format')
        validate_parser.add_argument('uuid', help='UUID to validate')
        validate_parser.set_defaults(func=self.execute_validate_uuid)
        
        # Generate plugin template
        template_parser = uuid_subparsers.add_parser('plugin-template', help='Generate plugin metadata template')
        template_parser.add_argument('--name', required=True, help='Plugin name')
        template_parser.add_argument('--version', default='v1.0.0', help='Plugin version')
        template_parser.add_argument('--description', help='Plugin description')
        template_parser.add_argument('--category', choices=['scanning', 'ml', 'security', 'performance', 'ui', 'integration', 'utility'], 
                                    default='utility', help='Plugin category')
        template_parser.add_argument('--output', '-o', help='Output file for plugin template')
        template_parser.set_defaults(func=self.execute_plugin_template)
        
        # Generate filename
        filename_parser = uuid_subparsers.add_parser('filename', help='Generate UUID-based filename')
        filename_parser.add_argument('--name', required=True, help='Plugin name')
        filename_parser.add_argument('--version', default='v1.0.0', help='Plugin version')
        filename_parser.set_defaults(func=self.execute_filename_generation)
        
        # Generate marketplace ID
        marketplace_parser = uuid_subparsers.add_parser('marketplace-id', help='Generate marketplace ID')
        marketplace_parser.add_argument('--name', required=True, help='Plugin name')
        marketplace_parser.add_argument('--uuid', help='UUID (generates if not provided)')
        marketplace_parser.set_defaults(func=self.execute_marketplace_id)

    def execute_generate_uuid(self, args: argparse.Namespace) -> int:
        """Execute UUID generation command."""
        try:
            uuids = []
            for _ in range(args.count):
                uuid_obj = UUIDUtils.generate_uuid_v4()
                
                # Format output
                if args.format == 'simple':
                    uuid_str = str(uuid_obj).replace('-', '')
                elif args.format == 'urn':
                    uuid_str = f"urn:uuid:{uuid_obj}"
                else:  # canonical
                    uuid_str = str(uuid_obj)
                
                uuids.append(uuid_str)
                print(uuid_str)
            
            # Save to file if requested
            if args.output:
                output_data = {
                    'generated_uuids': uuids,
                    'count': len(uuids),
                    'format': args.format,
                    'timestamp': str(uuid_obj)  # Use last UUID as timestamp reference
                }
                
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                print(f"\nUUIDs saved to: {args.output}")
            
            return 0
            
        except Exception as e:
            print(f"[ERROR] UUID generation failed: {e}")
            return 1

    def execute_validate_uuid(self, args: argparse.Namespace) -> int:
        """Execute UUID validation command."""
        try:
            is_valid = UUIDUtils.validate_uuid(args.uuid)
            
            if RICH_AVAILABLE:
                if is_valid:
                    console.print(f"[green]✓ Valid UUID v4:[/green] {args.uuid}")
                    # Display UUID details
                    uuid_obj = UUID(args.uuid)
                    table = Table(title="UUID Details", show_header=True, header_style="bold blue")
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="green")
                    
                    table.add_row("UUID", str(uuid_obj))
                    table.add_row("Version", str(uuid_obj.version))
                    table.add_row("Variant", uuid_obj.variant)
                    table.add_row("RFC 4122 Compliant", "Yes" if uuid_obj.variant == 'RFC 4122' else "No")
                    table.add_row("Canonical Format", "Yes" if len(str(uuid_obj)) == 36 else "No")
                    
                    console.print(table)
                else:
                    console.print(f"[red]✗ Invalid UUID:[/red] {args.uuid}")
            else:
                if is_valid:
                    print(f"✓ Valid UUID v4: {args.uuid}")
                    uuid_obj = UUID(args.uuid)
                    print(f"  Version: {uuid_obj.version}")
                    print(f"  Variant: {uuid_obj.variant}")
                    print(f"  RFC 4122 Compliant: {uuid_obj.variant == 'RFC 4122'}")
                else:
                    print(f"✗ Invalid UUID: {args.uuid}")
            
            return 0 if is_valid else 1
            
        except Exception as e:
            print(f"[ERROR] UUID validation failed: {e}")
            return 1

    def execute_plugin_template(self, args: argparse.Namespace) -> int:
        """Execute plugin template generation command."""
        try:
            # Generate UUID if not provided
            plugin_uuid = UUIDUtils.generate_uuid_v4()
            
            # Create plugin metadata template
            plugin_metadata = {
                "uuid": str(plugin_uuid),
                "name": args.name,
                "display_name": args.name.replace('_', ' ').title(),
                "version": args.version,
                "description": args.description or f"{args.name.replace('_', ' ').title()} plugin",
                "author": "NoDupeLabs Team",
                "category": args.category,
                "dependencies": [],
                "compatibility": {
                    "python": ">=3.9",
                    "nodupe_core": ">=1.0.0"
                },
                "tags": [args.category],
                "marketplace_id": f"{args.name}_{plugin_uuid}"
            }
            
            # Generate class template
            class_name = f"{args.name.replace('_', ' ').title().replace(' ', '')}Plugin"
            
            plugin_code = f'''"""{args.name} plugin for NoDupeLabs.

{args.description or f"{args.name.replace('_', ' ').title()} plugin"}

Key Features:
    - TODO: Add plugin features here

Dependencies:
    - Core modules
"""

from nodupe.core.plugin_system.base import Plugin

# Plugin metadata (UUID-based specification)
PLUGIN_METADATA = {json.dumps(plugin_metadata, indent=4)}

class {class_name}(Plugin):
    """{args.name} plugin implementation."""

    def __init__(self):
        """Initialize {args.name} plugin with UUID metadata."""
        super().__init__(PLUGIN_METADATA)

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._initialized = False

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {{'commands': ['{args.name}']}}

    def register_commands(self, subparsers: Any) -> None:
        """Register {args.name} commands with argument parser."""
        # TODO: Add command registration here
        pass

    def execute_{args.name}(self, args: argparse.Namespace) -> int:
        """Execute {args.name} command."""
        try:
            # TODO: Implement plugin functionality
            print(f"[{args.name.upper()}] Executing {args.name} command")
            return 0
        except Exception as e:
            print(f"[{args.name.upper()} ERROR] {args.name} failed: {{e}}")
            return 1


# Create plugin instance when module is loaded
{args.name}_plugin = {class_name}()


def register_plugin():
    """Register plugin with core system."""
    return {args.name}_plugin


# Export plugin interface
__all__ = ['{args.name}_plugin', 'register_plugin', '{class_name}']
'''
            
            # Display results
            if RICH_AVAILABLE:
                console.print(Panel(f"[bold]Generated Plugin Template for:[/bold] {args.name}", border_style="green"))
                
                # Display metadata
                metadata_str = json.dumps(plugin_metadata, indent=2)
                metadata_syntax = Syntax(metadata_str, "json", theme="monokai", line_numbers=True)
                console.print(Panel(metadata_syntax, title="PLUGIN_METADATA", border_style="blue"))
                
                # Display code template
                code_syntax = Syntax(plugin_code, "python", theme="monokai", line_numbers=True)
                console.print(Panel(code_syntax, title="Plugin Code Template", border_style="yellow"))
            else:
                print(f"Generated Plugin Template for: {args.name}")
                print("=" * 50)
                print("PLUGIN_METADATA:")
                print(json.dumps(plugin_metadata, indent=2))
                print("\nPlugin Code Template:")
                print("=" * 50)
                print(plugin_code)
            
            # Save to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(plugin_code)
                print(f"\nPlugin template saved to: {args.output}")
            
            return 0
            
        except Exception as e:
            print(f"[ERROR] Plugin template generation failed: {e}")
            return 1

    def execute_filename_generation(self, args: argparse.Namespace) -> int:
        """Execute UUID-based filename generation command."""
        try:
            filename = UUIDUtils.generate_plugin_filename(args.name, args.version)
            
            if RICH_AVAILABLE:
                console.print(Panel(f"[bold]Generated UUID-based Filename:[/bold]", border_style="green"))
                console.print(f"[cyan]Plugin Name:[/cyan] {args.name}")
                console.print(f"[cyan]Version:[/cyan] {args.version}")
                console.print(f"[green]Filename:[/green] {filename}")
            else:
                print(f"Generated UUID-based filename: {filename}")
                print(f"  Plugin Name: {args.name}")
                print(f"  Version: {args.version}")
            
            return 0
            
        except Exception as e:
            print(f"[ERROR] Filename generation failed: {e}")
            return 1

    def execute_marketplace_id(self, args: argparse.Namespace) -> int:
        """Execute marketplace ID generation command."""
        try:
            if args.uuid:
                plugin_uuid = args.uuid
                if not UUIDUtils.validate_uuid(plugin_uuid):
                    print(f"[ERROR] Invalid UUID format: {args.uuid}")
                    return 1
            else:
                plugin_uuid = str(UUIDUtils.generate_uuid_v4())
            
            marketplace_id = UUIDUtils.generate_marketplace_id(args.name, plugin_uuid)
            
            if RICH_AVAILABLE:
                console.print(Panel(f"[bold]Generated Marketplace ID:[/bold]", border_style="green"))
                console.print(f"[cyan]Plugin Name:[/cyan] {args.name}")
                console.print(f"[cyan]UUID:[/cyan] {plugin_uuid}")
                console.print(f"[green]Marketplace ID:[/green] {marketplace_id}")
            else:
                print(f"Generated Marketplace ID: {marketplace_id}")
                print(f"  Plugin Name: {args.name}")
                print(f"  UUID: {plugin_uuid}")
            
            return 0
            
        except Exception as e:
            print(f"[ERROR] Marketplace ID generation failed: {e}")
            return 1


# Create plugin instance when module is loaded
generate_uuid_plugin = GenerateUUIDPlugin()


def register_plugin():
    """Register UUID generation plugin with core system."""
    return generate_uuid_plugin


# Export plugin interface
__all__ = ['generate_uuid_plugin', 'register_plugin', 'GenerateUUIDPlugin']
