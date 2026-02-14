#!/usr/bin/env python3

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_import():
    """Test basic import of PluginCompatibility."""
    try:
        from nodupe.core.plugin_system.compatibility import PluginCompatibility, PluginCompatibilityError
        print("✅ Import successful in test context")

        # Test instantiation
        compat = PluginCompatibility()
        print(f"✅ Instance created: {type(compat)}")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_import()
    sys.exit(0 if success else 1)
