#!/usr/bin/env python3

"""Test script to debug the verify plugin loading issue."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from nodupe.core.plugin_system.base import Plugin
from nodupe.plugins.commands.verify import VerifyPlugin

def test_plugin_creation():
    """Test creating the verify plugin directly."""
    print("Testing direct plugin creation...")
    
    try:
        plugin = VerifyPlugin()
        print(f"Plugin created successfully")
        print(f"Name: {plugin.name}")
        print(f"Version: {plugin.version}")
        print(f"Dependencies: {plugin.dependencies}")
        print("All attributes accessible!")
        return True
    except Exception as e:
        print(f"Error creating plugin: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_issubclass():
    """Test if VerifyPlugin is a proper subclass of Plugin."""
    print("\nTesting issubclass relationship...")
    
    is_sub = issubclass(VerifyPlugin, Plugin)
    print(f"VerifyPlugin is subclass of Plugin: {is_sub}")
    
    # Check if it has the abstract methods implemented
    import inspect
    plugin_methods = [name for name, _ in inspect.getmembers(VerifyPlugin, predicate=inspect.isfunction)]
    plugin_properties = [name for name, _ in inspect.getmembers(VerifyPlugin, lambda x: isinstance(x, property))]
    
    print(f"Plugin methods: {plugin_methods}")
    print(f"Plugin properties: {plugin_properties}")
    
    # Check if the required abstract properties exist
    required_attrs = ['name', 'version', 'dependencies']
    for attr in required_attrs:
        has_attr = hasattr(VerifyPlugin, attr)
        attr_type = type(getattr(VerifyPlugin, attr, None))
        print(f"Has {attr}: {has_attr}, type: {attr_type}")

if __name__ == "__main__":
    print("Testing VerifyPlugin implementation...")
    success = test_plugin_creation()
    test_issubclass()
    
    if success:
        print("\n✅ Plugin implementation looks correct!")
    else:
        print("\n❌ Plugin implementation has issues!")
