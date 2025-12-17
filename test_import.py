#!/usr/bin/env python3

import sys
import traceback

try:
    print("Attempting to import PluginCompatibility...")
    from nodupe.core.plugin_system.compatibility import PluginCompatibility, PluginCompatibilityError
    print("✅ Import successful!")

    # Try to create an instance
    print("Creating PluginCompatibility instance...")
    compat = PluginCompatibility()
    print(f"✅ Instance created: {type(compat)}")

    # Check if it has the expected methods
    print("Checking methods...")
    assert hasattr(compat, 'check_compatibility')
    assert hasattr(compat, 'get_compatibility_report')
    assert hasattr(compat, 'initialize')
    assert hasattr(compat, 'shutdown')
    print("✅ All expected methods found!")

except ImportError as e:
    print(f"❌ ImportError: {e}")
    print("Traceback:")
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error: {e}")
    print("Traceback:")
    traceback.print_exc()
