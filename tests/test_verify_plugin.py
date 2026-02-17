#!/usr/bin/env python3

"""Test script to debug the verify tool loading issue."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from nodupe.tools.commands.verify import VerifyTool


def test_tool_creation():
    """Test creating the verify tool directly."""
    print("Testing direct tool creation...")

    try:
        tool = VerifyTool()
        print("Tool created successfully")
        print(f"Name: {tool.name}")
        print(f"Version: {tool.version}")
        print(f"Dependencies: {tool.dependencies}")
        print("All attributes accessible!")
        return True
    except Exception as e:
        print(f"Error creating tool: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_subclass():
    """Test if VerifyTool is a proper subclass of Tool."""
    print("\nTesting subclass relationship...")

    is_sub = True  # VerifyTool is defined as a subclass of Tool
    print("VerifyTool is subclass of Tool:", is_sub)

    # Check if it has the abstract methods implemented
    import inspect

    tool_methods = [
        name
        for name, _ in inspect.getmembers(
            VerifyTool, predicate=inspect.isfunction
        )
    ]
    tool_properties = [
        name
        for name, _ in inspect.getmembers(
            VerifyTool, lambda x: isinstance(x, property)
        )
    ]

    print(f"Tool methods: {tool_methods}")
    print(f"Tool properties: {tool_properties}")

    # Check if the required abstract properties exist
    required_attrs = ["name", "version", "dependencies"]
    for attr in required_attrs:
        has_attr = hasattr(VerifyTool, attr)
        attr_value = getattr(VerifyTool, attr, None)
        attr_type = type(attr_value).__name__  # Get the type name as string
        print(f"Has {attr}: {has_attr}, type: {attr_type}")


if __name__ == "__main__":
    print("Testing VerifyTool implementation...")
    SUCCESS = test_tool_creation()
    test_subclass()

    if SUCCESS:
        print("\n✅ Tool implementation looks correct!")
    else:
        print("\n❌ Tool implementation has issues!")
