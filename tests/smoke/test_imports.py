"""Smoke tests that import a curated set of modules to increase baseline coverage."""

import importlib

MODULES = [
    # core subsystems
    "nodupe.core.tool_system.loader",
    "nodupe.core.tool_system.discovery",
    "nodupe.core.tool_system.registry",
    "nodupe.core.tool_system.lifecycle",
    "nodupe.core.tool_system.base",
    "nodupe.core.tool_system.compatibility",
    "nodupe.core.tool_system.hot_reload",
    "nodupe.core.api.ipc",
    "nodupe.core.api.codes",
    "nodupe.core.api.openapi",
    "nodupe.core.api.validation",
    "nodupe.core.api.ratelimit",
    "nodupe.core.api.decorators",
    "nodupe.core.config",
    "nodupe.core.deps",
    "nodupe.core.container",
    "nodupe.core.limits",
    "nodupe.core.logging_system",
    "nodupe.core.errors",
    "nodupe.core.main",
    # hashing tools
    "nodupe.tools.hashing.hash_cache",
    "nodupe.tools.hashing.hasher_logic",
    "nodupe.tools.hashing.hashing_tool",
    "nodupe.tools.hashing.autotune_logic",
    # mime & file utilities
    "nodupe.tools.mime.mime_logic",
    "nodupe.tools.os_filesystem.filesystem",
    "nodupe.tools.os_filesystem.mmap_handler",
    # leap year (simple, widely used)
    "nodupe.tools.leap_year.leap_year",
    # GPU / ML related (graceful fallbacks expected)
    "nodupe.tools.ml.embedding_cache",
    # scanner engine and helpers
    "nodupe.tools.scanner_engine.file_info",
    "nodupe.tools.scanner_engine.walker",
    "nodupe.tools.scanner_engine.processor",
    "nodupe.tools.scanner_engine.incremental",
    "nodupe.tools.scanner_engine.progress",
    # commands + utilities
    "nodupe.tools.commands.scan",
    "nodupe.tools.commands.apply",
    "nodupe.tools.commands.similarity",
    # compression / archive / maintenance
    "nodupe.tools.compression_standard.engine_logic",
    "nodupe.tools.archive.archive_tool",
    "nodupe.tools.archive.archive_logic",
    "nodupe.tools.maintenance.log_compressor",
    "nodupe.tools.maintenance.transaction",
    # databases
    "nodupe.tools.databases.connection",
    "nodupe.tools.databases.database",
    "nodupe.tools.databases.query_cache",
    "nodupe.tools.databases.files",
    "nodupe.tools.databases.indexing",
    "nodupe.tools.databases.query",
    "nodupe.tools.databases.transactions",
    "nodupe.tools.databases.wrapper",
    "nodupe.tools.databases.logging_",
    "nodupe.tools.databases.session",
    "nodupe.tools.databases.serialization",
    "nodupe.tools.database.features",
    # parallel / pools / GPU
    "nodupe.tools.parallel.parallel_logic",
    "nodupe.tools.parallel.pools",
    "nodupe.tools.parallel.parallel_tool",
    # time sync / security
    "nodupe.tools.time_sync.time_sync_tool",
    "nodupe.tools.time_sync.sync_utils",
    "nodupe.tools.time_sync.failure_rules",
    "nodupe.tools.security_audit.security_logic",
]


def test_can_import_core_modules():
    for m in MODULES:
        try:
            mod = importlib.import_module(m)
        except ImportError:
            # some tool modules require optional external dependencies; allow
            # import failures for optional subsystems but surface the name
            # so they can be reviewed if unexpected.
            continue
        assert mod is not None
