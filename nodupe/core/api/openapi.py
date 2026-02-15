# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""OpenAPI Specification Generator Module.

Provides OpenAPI 3.1.2 specification generation for NoDupeLabs APIs.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


class OpenAPIGenerator:
    """OpenAPI 3.1.2 Specification Generator.

    Generates valid OpenAPI 3.1.2 specifications for NoDupeLabs APIs.
    Supports paths, components, security schemes, and more.
    """

    def __init__(self) -> None:
        """Initialize OpenAPI generator."""
        self.openapi_version: str = "3.1.2"
        self.info: Dict[str, Any] = {
            "title": "NoDupeLabs API",
            "version": "1.0.0",
            "description": "NoDupeLabs API for duplicate file detection"
        }
        self.servers: List[Dict[str, str]] = []
        self.paths: Dict[str, Dict[str, Any]] = {}
        self.components: Dict[str, Any] = {
            "schemas": {},
            "responses": {},
            "parameters": {},
            "securitySchemes": {}
        }
        self.security: List[Dict[str, List[str]]] = []
        self.tags: List[Dict[str, str]] = []

    def set_info(self, title: str, version: str, description: Optional[str] = None) -> "OpenAPIGenerator":
        """Set API information."""
        self.info = {"title": title, "version": version}
        if description:
            self.info["description"] = description
        return self

    def add_server(self, url: str, description: Optional[str] = None) -> "OpenAPIGenerator":
        """Add a server URL."""
        server: Dict[str, str] = {"url": url}
        if description:
            server["description"] = description
        self.servers.append(server)
        return self

    def add_path(self, path: str, method: str, operation: Dict[str, Any]) -> "OpenAPIGenerator":
        """Add an API path/endpoint."""
        method = method.lower()
        if path not in self.paths:
            self.paths[path] = {}
        self.paths[path][method] = operation
        return self

    def add_schema(self, name: str, schema: Dict[str, Any]) -> "OpenAPIGenerator":
        """Add a reusable schema component."""
        self.components["schemas"][name] = schema
        return self

    def generate_spec(self) -> Dict[str, Any]:
        """Generate the complete OpenAPI specification."""
        spec: Dict[str, Any] = {
            "openapi": self.openapi_version,
            "info": self.info,
            "paths": self.paths
        }
        if self.servers:
            spec["servers"] = self.servers
        if self.components and any(self.components.values()):
            spec["components"] = self.components
        return spec

    def to_json(self, spec: Optional[Dict[str, Any]] = None, indent: int = 2) -> str:
        """Convert spec to JSON string."""
        if spec is None:
            spec = self.generate_spec()
        return json.dumps(spec, indent=indent)

    def validate_spec(self, spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate the OpenAPI specification."""
        if spec is None:
            spec = self.generate_spec()
        errors: List[str] = []
        if "openapi" not in spec:
            errors.append("Missing required field: openapi")
        if "info" not in spec:
            errors.append("Missing required field: info")
        if "paths" not in spec:
            errors.append("Missing required field: paths")
        return {"valid": len(errors) == 0, "errors": errors}
