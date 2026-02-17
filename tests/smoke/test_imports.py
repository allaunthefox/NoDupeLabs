"""Smoke tests that import a curated set of modules to increase baseline coverage."""

import importlib

MODULES = [
    'nodupe.core.tool_system.loader',
    'nodupe.core.tool_system.discovery',
    'nodupe.core.api.ipc',
    'nodupe.core.api.codes',
    'nodupe.core.tool_system.registry',
    'nodupe.core.tool_system.lifecycle',
    'nodupe.core.main',
]


def test_can_import_core_modules():
    for m in MODULES:
        mod = importlib.import_module(m)
        assert mod is not None
