# pylint: disable=logging-fstring-interpolation
"""Tool Loader Module.

Dynamic tool loading and management using standard library only.

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation

Key Features:
    - Safe tool loading with validation
    - Tool dependency resolution
    - Tool lifecycle management
    - Graceful error handling
    - Standard library only (no external dependencies)

Dependencies:
    - importlib (standard library)
    - pathlib (standard library)
    - typing (standard library)
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional

from .base import Tool
from .registry import ToolRegistry


class ToolLoaderError(Exception):
    """Tool loader error"""


class ToolLoader:
    """Handle tool loading and management.

    Provides safe tool loading with validation, dependency resolution,
    and lifecycle management.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        """Initialize tool loader.

        Args:
            registry: Tool registry instance
        """
        self.registry = registry or ToolRegistry()
        self._loaded_tools: dict[str, Tool] = {}
        self._tool_modules: dict[str, Any] = {}
        self.container = None

    def initialize(self, container: Any) -> None:
        """Initialize tool loader with container.

        Args:
            container: Dependency container instance
        """
        self.container = container

    def load_tool(self, tool: Tool) -> Tool:
        """Load a tool instance.

        Args:
            tool: Tool instance to load

        Returns:
            The loaded tool instance
        """
        # Validate input type
        if not isinstance(tool, Tool):
            raise ToolLoaderError("Tool instance must inherit from Tool base class")

        # Validate tool name early to avoid silently accepting invalid names
        try:
            name_val = tool.name
        except Exception as e:
            raise ToolLoaderError(f"Invalid tool instance: {e}") from e

        if name_val is None or not isinstance(name_val, str):
            raise ToolLoaderError("Tool must have a string name (None not allowed)")
        # Allow empty-string names (tests rely on accepting empty names in some
        # edge-cases); do not reject empty names here.

        # Ensure the concrete class provides required lifecycle methods
        required_methods = ["initialize", "shutdown", "get_capabilities"]
        for method in required_methods:
            cls_method = getattr(type(tool), method, None)
            base_method = getattr(Tool, method, None)
            if cls_method is None or cls_method == base_method:
                raise ToolLoaderError(
                    f"Tool class must implement required method: {method}"
                )

        # Try to initialize the tool and capture any exceptions
        try:
            tool.initialize(self.container)
        except Exception as e:
            raise ToolLoaderError(
                f"Tool.initialize() failed for {name_val}: {e}"
            ) from e

        self._loaded_tools[name_val] = tool
        return tool

    def load_tool_from_file(self, tool_path: Path) -> Optional[type[Tool]]:
        """Load a tool from a Python file.

        Args:
            tool_path: Path to tool file

        Returns:
            Tool class or None if loading failed

        Raises:
            ToolLoaderError: If tool loading fails
        """
        try:
            # Validate file path
            if not tool_path.exists():
                raise ToolLoaderError(f"Tool file does not exist: {tool_path}")

            if not tool_path.suffix == ".py":
                raise ToolLoaderError(f"Tool file must be Python: {tool_path}")

            # Create a package-aware module name so relative imports inside
            # tool modules work (e.g. `from .connection import ...`). If the
            # tool file lives under a top-level 'nodupe' package directory we
            # build a qualified module name like
            # 'nodupe.tools.databases.embeddings'. Otherwise fall back to a
            # unique synthetic name.
            def _module_name_for_path(p: Path) -> str:
                parts = list(p.parts)
                try:
                    idx = parts.index("nodupe")
                    rel = parts[idx:]
                    rel[-1] = rel[-1].rsplit(".", 1)[0]
                    return ".".join(rel)
                except ValueError:
                    # No nodupe ancestor found; use fallback synthetic name
                    return f"tool_{p.stem}_{id(p)}"

            module_name = _module_name_for_path(tool_path)
            spec = importlib.util.spec_from_file_location(
                module_name, tool_path
            )
            if spec is None or spec.loader is None:
                raise ToolLoaderError(
                    f"Could not create module spec: {tool_path}"
                )

            # If the module name represents a package-qualified path (for
            # example: 'nodupe.tools.pkg.tool_mod'), make sure all parent
            # package entries exist in sys.modules and have a correct
            # __path__ that includes the directory on disk where the
            # package lives. This fixes relative imports inside dynamically
            # loaded tool modules and avoids collisions with an already
            # imported top-level 'nodupe' package.
            import types

            pkg_parts = module_name.split(".")[:-1]
            if pkg_parts:
                try:
                    idx = list(tool_path.parts).index("nodupe")
                except ValueError:
                    idx = None

                if idx is not None:
                    rel_parts = list(tool_path.parts)[
                        idx:-1
                    ]  # exclude filename
                    for i in range(len(rel_parts)):
                        pkg_name = ".".join(rel_parts[: i + 1])
                        pkg_dir = Path(*tool_path.parts[: idx + i + 1])
                        existing = sys.modules.get(pkg_name)
                        if existing is None:
                            mod = types.ModuleType(pkg_name)
                            mod.__path__ = [str(pkg_dir)]
                            sys.modules[pkg_name] = mod
                        else:
                            pkg_path = getattr(existing, "__path__", None)
                            if pkg_path is None:
                                existing.__path__ = [str(pkg_dir)]
                            elif str(pkg_dir) not in pkg_path:
                                existing.__path__.insert(0, str(pkg_dir))

            module = importlib.util.module_from_spec(spec)
            # Ensure the module is available in sys.modules under the
            # package-aware name so internal relative imports resolve.
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find tool class in module
            tool_class = self._find_tool_class(module)
            if tool_class is None:
                raise ToolLoaderError(f"No Tool subclass found in: {tool_path}")

            # Validate tool class
            if not self._validate_tool_class(tool_class):
                raise ToolLoaderError(f"Invalid tool class: {tool_class}")

            # Check for accessibility compliance
            import logging

            from ..api.codes import ActionCode

            logger = logging.getLogger(__name__)

            # Check if the tool inherits from AccessibleTool
            from .base import AccessibleTool

            if issubclass(tool_class, AccessibleTool):
                logger.info(
                    f"[{ActionCode.ACC_ISO_CMP}] Tool {tool_class.__name__} is ISO accessibility compliant"
                )
            else:
                logger.info(
                    f"[{ActionCode.ACC_FEATURE_DISABLED}] Tool {tool_class.__name__} does not implement accessibility features"
                )

            # Store module reference
            self._tool_modules[tool_class.__name__] = module

            return tool_class

        except Exception as e:
            if isinstance(e, ToolLoaderError):
                raise
            raise ToolLoaderError(
                f"Failed to load tool {tool_path}: {e}"
            ) from e

    def load_tool_from_directory(
        self, tool_dir: Path, recursive: bool = False
    ) -> list[type[Tool]]:
        """Load all tools from a directory.

        Args:
            tool_dir: Directory containing tool files
            recursive: If True, search subdirectories

        Returns:
            List of loaded tool classes

        Raises:
            ToolLoaderError: If tool loading fails
        """
        try:
            if not tool_dir.exists():
                raise ToolLoaderError(
                    f"Tool directory does not exist: {tool_dir}"
                )

            if not tool_dir.is_dir():
                raise ToolLoaderError(f"Path is not a directory: {tool_dir}")

            # Find Python files, excluding __init__.py files
            pattern = "**/*.py" if recursive else "*.py"
            python_files = list(tool_dir.glob(pattern))

            # Filter out __init__.py files as they're not tools
            python_files = [f for f in python_files if f.name != "__init__.py"]

            loaded_tools: list[type[Tool]] = []
            for file_path in python_files:
                try:
                    tool_class = self.load_tool_from_file(file_path)
                    if tool_class:
                        loaded_tools.append(tool_class)
                except ToolLoaderError:
                    # Continue loading other tools even if one fails
                    continue

            return loaded_tools

        except Exception as e:
            if isinstance(e, ToolLoaderError):
                raise
            raise ToolLoaderError(
                f"Failed to load tools from {tool_dir}: {e}"
            ) from e

    def load_tool_by_name(
        self, tool_name: str, tool_dirs: list[Path]
    ) -> Optional[type[Tool]]:
        """Load a tool by name from specified directories.

        Args:
            tool_name: Name of tool to load
            tool_dirs: List of directories to search

        Returns:
            Tool class or None if not found

        Raises:
            ToolLoaderError: If tool loading fails
        """
        for tool_dir in tool_dirs:
            tool_path = tool_dir / f"{tool_name}.py"
            if tool_path.exists():
                return self.load_tool_from_file(tool_path)

            # Also try subdirectory with __init__.py
            tool_subdir = tool_dir / tool_name
            if tool_subdir.exists() and (tool_subdir / "__init__.py").exists():
                return self.load_tool_from_file(tool_subdir / "__init__.py")

        return None

    def instantiate_tool(
        self, tool_class: type[Tool], *args: Any, **kwargs: Any
    ) -> Tool:
        """Instantiate a tool class.

        Args:
            tool_class: Tool class to instantiate
            *args: Arguments to pass to tool constructor
            **kwargs: Keyword arguments to pass to tool constructor

        Returns:
            Tool instance

        Raises:
            ToolLoaderError: If instantiation fails
        """
        try:
            instance = tool_class(*args, **kwargs)
            return instance
        except Exception as e:
            raise ToolLoaderError(
                f"Failed to instantiate tool {tool_class}: {e}"
            ) from e

    def register_loaded_tool(
        self, tool_instance: Tool, tool_path: Optional[Path] = None
    ) -> None:
        """Register a loaded tool with the registry.

        Args:
            tool_instance: Tool instance to register
            tool_path: Optional path where tool was loaded from

        Raises:
            ToolLoaderError: If registration fails
        """
        try:
            self.registry.register(tool_instance)

        except Exception as e:
            raise ToolLoaderError(
                f"Failed to register tool {tool_instance.name}: {e}"
            ) from e

    def unload_tool(self, tool_name: Any) -> bool:
        """Unload a tool.

        Args:
            tool_name: Name of tool or Tool instance to unload

        Returns:
            True if tool was unloaded, False if not found
        """
        if not isinstance(tool_name, str):
            tool_name = tool_name.name

        if tool_name in self._loaded_tools:
            tool_instance = self._loaded_tools[tool_name]

            # Shutdown tool
            try:
                tool_instance.shutdown()
            except Exception as e:
                # Log or print error but continue with unloading
                print(f"Warning: Error shutting down tool {tool_name}: {e}")

            # Remove from registry
            try:
                self.registry.unregister(tool_name)
            except KeyError:
                pass  # Tool might not be registered in registry

            # Remove from loaded tools
            del self._loaded_tools[tool_name]

            # Remove module from sys.modules if it exists
            module_name = getattr(tool_instance, "__module__", None)
            if module_name and module_name in sys.modules:
                del sys.modules[module_name]

            return True

        return False

    def get_loaded_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a loaded tool instance.

        Args:
            tool_name: Name of tool to get

        Returns:
            Tool instance or None if not loaded
        """
        return self._loaded_tools.get(tool_name)

    def get_all_loaded_tools(self) -> dict[str, Tool]:
        """Get all loaded tool instances.

        Returns:
            Dictionary of tool name to instance
        """
        return self._loaded_tools.copy()

    def _find_tool_class(self, module: Any) -> Optional[type[Tool]]:
        """Find Tool subclass in module.

        Args:
            module: Module to search

        Returns:
            Tool class or None if not found
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Tool)
                and attr != Tool
            ):
                return attr
        return None

    def _validate_tool_class(self, tool_class: type[Tool]) -> bool:
        """Validate tool class.

        Args:
            tool_class: Tool class to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required attributes exist
            required_attrs = ["name"]
            for attr in required_attrs:
                if not hasattr(tool_class, attr):
                    return False

            # Check name is valid
            # For properties, we need to check if it's a property descriptor
            name_attr = getattr(tool_class, "name")

            # Check if it's a property descriptor
            if isinstance(name_attr, property):
                # For property, try to instantiate the class and get the value
                try:
                    temp_instance = tool_class()
                    name = temp_instance.name
                except Exception:
                    return False
            else:
                # It's a class attribute
                name = name_attr

            return not (
                not name or not isinstance(name, str) or not name.strip()
            )

        except Exception:
            return False


def create_tool_loader(registry: Optional[ToolRegistry] = None) -> ToolLoader:
    """Create a tool loader instance.

    Args:
        registry: Optional tool registry instance

    Returns:
        ToolLoader instance
    """
    return ToolLoader(registry)
