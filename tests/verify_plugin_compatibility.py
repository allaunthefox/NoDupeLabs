#!/usr/bin/env python3

import os
import sys
import traceback
from typing import List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_tool_compatibility_import():
    """Test that ToolCompatibility can be imported and used."""
    try:
        print("🧪 Testing ToolCompatibility import...")

        # Test the import that was failing
        from nodupe.core.tool_system.compatibility import (
            ToolCompatibility,
            ToolCompatibilityError,
        )

        print("✅ ToolCompatibility import successful")

        # Test instantiation
        compat = ToolCompatibility()
        print(f"✅ ToolCompatibility instance created: {type(compat)}")

        # Test basic functionality
        from nodupe.core.tool_system.base import Tool

        class TestTool(Tool):
            @property
            def name(self) -> str:
                return "test_tool"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def dependencies(self) -> list[str]:
                return ["core>=1.0.0"]

            def __init__(self):
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_tool = TestTool()

        # Test compatibility checking
        report = compat.check_compatibility(test_tool)
        print(f"✅ Compatibility check successful: {report}")

        # Test detailed report
        detailed_report = compat.get_compatibility_report(test_tool)
        print(f"✅ Detailed report successful: {detailed_report}")

        return True

    except ImportError as e:
        print(f"❌ ImportError: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False


def test_performance_utils():
    """Test that performance utilities work correctly."""
    try:
        print("\n🧪 Testing performance utilities...")

        from tests.utils import performance

        # Test basic functionality
        def test_func(x):
            return x * 2

        result = performance.benchmark_function_performance(test_func, 10, 2, 5)
        print(f"✅ Performance benchmark successful: {result}")

        # Test memory measurement (should work even without psutil)
        mem_result = performance.measure_memory_usage(test_func, 5, 5)
        print(f"✅ Memory measurement successful: {mem_result}")

        return True

    except ImportError as e:
        print(f"❌ ImportError in performance utils: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error in performance utils: {e}")
        traceback.print_exc()
        return False


def test_test_utils():
    """Test that test_utils.py can be imported."""
    try:
        print("\n🧪 Testing test_utils.py import...")

        # This was the file that had the resource module issue
        import tests.test_utils

        print("✅ test_utils.py import successful")

        return True

    except ImportError as e:
        print(f"❌ ImportError in test_utils: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error in test_utils: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Running verification tests for fixes...")

    results = []
    results.append(test_tool_compatibility_import())
    results.append(test_performance_utils())
    results.append(test_test_utils())

    print(f"\n📊 Results: {sum(results)}/{len(results)} tests passed")

    if all(results):
        print("🎉 All verification tests passed! Fixes are working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
