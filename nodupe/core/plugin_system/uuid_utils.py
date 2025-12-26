"""UUID Utilities for Plugin System.

Provides UUID generation, validation, and filename utilities for the
NoDupeLabs plugin system with UUID-based naming convention support.

Key Features:
    - UUID v4 generation with cryptographic security
    - Plugin filename generation and validation
    - UUID-based plugin identification
    - Marketplace ID generation
    - Standard library only (no external dependencies)

Dependencies:
    - uuid (standard library)
    - re (standard library)
    - pathlib (standard library)
"""

from uuid import UUID, uuid4
from pathlib import Path
import re
from typing import Optional, Tuple, Dict, Any


class UUIDValidationError(Exception):
    """UUID validation error"""


class UUIDUtils:
    """Utilities for UUID-based plugin operations."""

    # UUID v4 pattern for validation (RFC 9562 compliant)
    UUID_V4_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )

    # Plugin filename pattern: {name}_{uuid}.v{version}.py
    PLUGIN_FILENAME_PATTERN = re.compile(
        r'^(?P<name>[a-z][a-z0-9_]{1,49})_'  # Plugin name
        r'(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})'  # UUID v4
        r'\.v(?P<version>\d+\.\d+\.\d+)\.py$',  # Version
        re.IGNORECASE
    )

    @staticmethod
    def generate_uuid_v4() -> UUID:
        """Generate a cryptographically secure UUID v4.
        
        Returns:
            UUID: Generated UUID v4 object
        """
        return uuid4()

    @staticmethod
    def is_valid_uuid(uuid_str: str) -> bool:
        """Validate that a string is a valid UUID v4 (RFC 9562 compliant).
        
        Args:
            uuid_str: String to validate
            
        Returns:
            bool: True if valid UUID v4, False otherwise
        """
        if not isinstance(uuid_str, str):
            return False
        
        try:
            # Use Python's standard library UUID validation
            uuid_obj = UUID(uuid_str)
            
            # Check RFC 9562 compliance
            if uuid_obj.version != 4:
                return False
            
            # Check variant field (must be RFC 4122)
            # The variant property returns a string description, not the literal "RFC 4122"
            if uuid_obj.variant != 'specified in RFC 4122':
                return False
            
            # Check canonical string representation (36 characters)
            if len(str(uuid_obj)) != 36:
                return False
            
            return True
            
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate that a string is a valid UUID v4 (RFC 9562 compliant).
        
        Args:
            uuid_str: String to validate
            
        Returns:
            bool: True if valid UUID v4, False otherwise
        """
        return UUIDUtils.is_valid_uuid(uuid_str)

    @staticmethod
    def validate_plugin_name(name: str) -> bool:
        """Validate plugin name format.
        
        Args:
            name: Plugin name to validate
            
        Returns:
            bool: True if valid plugin name, False otherwise
        """
        if not isinstance(name, str):
            return False
        
        # Must be 2-50 characters, lowercase letters, numbers, and underscores only
        # Must start with a letter
        pattern = re.compile(r'^[a-z][a-z0-9_]{1,49}$')
        return bool(pattern.match(name))

    @staticmethod
    def validate_version(version: str) -> bool:
        """Validate semantic version format.
        
        Args:
            version: Version string to validate
            
        Returns:
            bool: True if valid version format, False otherwise
        """
        if not isinstance(version, str):
            return False
        
        # Must follow semantic versioning format (v1.2.3)
        pattern = re.compile(r'^v\d+\.\d+\.\d+$')
        return bool(pattern.match(version))

    @staticmethod
    def generate_plugin_filename(name: str, version: str) -> str:
        """Generate a UUID-based filename for a plugin.
        
        Args:
            name: Plugin name
            version: Plugin version (with 'v' prefix)
            
        Returns:
            str: Generated filename
            
        Raises:
            UUIDValidationError: If name or version format is invalid
        """
        if not UUIDUtils.validate_plugin_name(name):
            raise UUIDValidationError(f"Invalid plugin name format: {name}")
        
        if not UUIDUtils.validate_version(version):
            raise UUIDValidationError(f"Invalid version format: {version}")
        
        # Generate UUID and create filename
        plugin_uuid = UUIDUtils.generate_uuid_v4()
        return f"{name}_{plugin_uuid}.{version}.py"

    @staticmethod
    def parse_plugin_filename(filename: str) -> Optional[Dict[str, str]]:
        """Parse a UUID-based plugin filename.
        
        Args:
            filename: Plugin filename to parse
            
        Returns:
            Dict with 'name', 'uuid', and 'version' keys if valid, None otherwise
        """
        match = UUIDUtils.PLUGIN_FILENAME_PATTERN.match(filename)
        if not match:
            return None
        
        return {
            'name': match.group('name'),
            'uuid': match.group('uuid'),
            'version': match.group('version')
        }

    @staticmethod
    def validate_plugin_filename(filename: str) -> bool:
        """Validate that a filename follows UUID-based plugin naming convention.
        
        Args:
            filename: Filename to validate
            
        Returns:
            bool: True if valid UUID-based plugin filename, False otherwise
        """
        return UUIDUtils.parse_plugin_filename(filename) is not None

    @staticmethod
    def generate_marketplace_id(name: str, uuid_str: str) -> str:
        """Generate a marketplace ID for a plugin.
        
        Args:
            name: Plugin name
            uuid_str: Plugin UUID string
            
        Returns:
            str: Marketplace ID (UTF-8 encoded)
            
        Raises:
            UUIDValidationError: If name, UUID format is invalid, or contains non-UTF-8 characters
        """
        if not UUIDUtils.validate_plugin_name(name):
            raise UUIDValidationError(f"Invalid plugin name format: {name}")
        
        if not UUIDUtils.validate_uuid(uuid_str):
            raise UUIDValidationError(f"Invalid UUID format: {uuid_str}")
        
        marketplace_id = f"{name}_{uuid_str}"
        
        # Ensure UTF-8 encoding compliance
        try:
            # Validate UTF-8 encoding
            marketplace_id.encode('utf-8')
            
            # Check for invalid characters
            if '\x00' in marketplace_id:
                raise UUIDValidationError("Marketplace ID contains null bytes")
            
            # Check length limit (255 characters when UTF-8 encoded)
            utf8_length = len(marketplace_id.encode('utf-8'))
            if utf8_length > 255:
                raise UUIDValidationError(f"Marketplace ID too long: {utf8_length} bytes (max 255)")
            
            # Check for control characters (except tab, newline, carriage return which are generally safe)
            import string
            for char in marketplace_id:
                if ord(char) < 32 and char not in '\t\n\r':
                    raise UUIDValidationError(f"Marketplace ID contains invalid control character: {ord(char)}")
                elif ord(char) == 127:  # DEL character
                    raise UUIDValidationError("Marketplace ID contains DEL character")
            
        except UnicodeEncodeError as e:
            raise UUIDValidationError(f"Marketplace ID contains non-UTF-8 characters: {e}")
        
        return marketplace_id

    @staticmethod
    def extract_plugin_info_from_file(file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract plugin information from a Python file.
        
        Args:
            file_path: Path to plugin file
            
        Returns:
            Dict with plugin information if valid, None otherwise
        """
        try:
            # Parse filename
            filename_info = UUIDUtils.parse_plugin_filename(file_path.name)
            if not filename_info:
                return None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = UUIDUtils._extract_metadata_from_content(content)
            
            # Merge filename info with metadata
            plugin_info = {
                'name': filename_info['name'],
                'uuid': filename_info['uuid'],
                'version': f"v{filename_info['version']}",  # Add 'v' prefix
                'file_path': str(file_path),
                'marketplace_id': UUIDUtils.generate_marketplace_id(
                    filename_info['name'], 
                    filename_info['uuid']
                )
            }
            
            # Add metadata fields if present
            for key in ['display_name', 'description', 'author', 'category', 'dependencies', 'capabilities']:
                if key in metadata:
                    plugin_info[key] = metadata[key]
            
            return plugin_info
            
        except Exception:
            return None

    @staticmethod
    def _extract_metadata_from_content(content: str) -> Dict[str, Any]:
        """Extract metadata from plugin file content.
        
        Args:
            content: Python file content
            
        Returns:
            Dict with extracted metadata
        """
        import ast
        
        metadata = {}
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'PLUGIN_METADATA':
                            if isinstance(node.value, ast.Dict):
                                # Extract metadata from dictionary
                                for key, value in zip(node.value.keys, node.value.values):
                                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                        key_name = key.value
                                        if isinstance(value, ast.Constant):
                                            metadata[key_name] = value.value
                                        elif isinstance(value, ast.List):
                                            # Parse list values
                                            metadata[key_name] = [item.value for item in value.elts if isinstance(item, ast.Constant)]
                                        elif isinstance(value, ast.Dict):
                                            # Parse dict values
                                            dict_value = {}
                                            for k, v in zip(value.keys, value.values):
                                                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                                    dict_value[k.value] = v.value
                                            metadata[key_name] = dict_value
        except SyntaxError:
            pass
        
        return metadata

    @staticmethod
    def is_uuid_plugin_file(file_path: Path) -> bool:
        """Check if a file is a UUID-based plugin file.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            bool: True if file is a UUID-based plugin, False otherwise
        """
        # Check filename format
        if not UUIDUtils.validate_plugin_filename(file_path.name):
            return False
        
        # Check file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Must have PLUGIN_METADATA
            if 'PLUGIN_METADATA' not in content:
                return False
            
            # Must have class that inherits from Plugin
            if 'class' not in content or 'Plugin' not in content:
                return False
            
            # Must have required methods
            required_methods = ['initialize', 'shutdown', 'get_capabilities']
            for method in required_methods:
                if f'def {method}' not in content:
                    return False
            
            return True
            
        except Exception:
            return False

    @staticmethod
    def get_plugin_categories() -> Dict[str, str]:
        """Get standard plugin categories.
        
        Returns:
            Dict mapping category codes to descriptions
        """
        return {
            'scanning': 'File scanning and detection plugins',
            'ml': 'Machine learning and AI integration',
            'security': 'Security analysis and validation',
            'performance': 'Performance optimization plugins',
            'ui': 'User interface enhancements',
            'integration': 'External system integrations',
            'utility': 'General utility plugins'
        }

    @staticmethod
    def validate_category(category: str) -> bool:
        """Validate plugin category.
        
        Args:
            category: Category to validate
            
        Returns:
            bool: True if valid category, False otherwise
        """
        standard_categories = UUIDUtils.get_plugin_categories()
        
        # Check if it's a standard category
        if category in standard_categories:
            return True
        
        # Check if it's a custom category (lowercase letters and hyphens only, 3-20 chars)
        pattern = re.compile(r'^[a-z][a-z0-9-]{2,19}$')
        return bool(pattern.match(category))


def create_uuid_utils() -> UUIDUtils:
    """Create a UUID utilities instance.
    
    Returns:
        UUIDUtils instance
    """
    return UUIDUtils()
