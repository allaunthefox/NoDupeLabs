"""Quick smoke-import tests to raise baseline coverage.

These tests only import and instantiate lightweight components (no background
threads or external services are started). They help exercise module-level
initialization paths safely and increase the repository's baseline coverage.
"""

import importlib


def test_smoke_import_core_components():
    # Import and instantiate core classes without side-effects
    core_loader_mod = importlib.import_module("nodupe.core.loader")
    CoreLoader = getattr(core_loader_mod, "CoreLoader")
    loader = CoreLoader()
    assert hasattr(loader, "initialize")
    assert loader.initialized is False

    tools_mod = importlib.import_module("nodupe.core.tools")
    assert hasattr(tools_mod, "tool_manager")


def test_smoke_import_tool_system_components():
    # Import tool-system components and create instances (no start())
    registry_mod = importlib.import_module("nodupe.core.tool_system.registry")
    ToolRegistry = getattr(registry_mod, "ToolRegistry")
    reg = ToolRegistry()
    assert hasattr(reg, "register")

    loader_mod = importlib.import_module("nodupe.core.tool_system.loader")
    ToolLoader = getattr(loader_mod, "ToolLoader")
    tl = ToolLoader(reg)
    assert tl.registry is reg

    lifecycle_mod = importlib.import_module("nodupe.core.tool_system.lifecycle")
    create_lifecycle_manager = getattr(lifecycle_mod, "create_lifecycle_manager", None)
    # create_lifecycle_manager may or may not be present; just ensure import succeeds
    assert lifecycle_mod is not None


def test_smoke_import_hot_reload_and_leap_year():
    # ToolHotReload __init__ is safe (it doesn't start the background thread)
    hot_reload_mod = importlib.import_module("nodupe.core.tool_system.hot_reload")
    ToolHotReload = getattr(hot_reload_mod, "ToolHotReload")
    hr = ToolHotReload()
    assert hasattr(hr, "watch_tool")

    # LeapYear tool is safe to instantiate and run a simple method
    leap_mod = importlib.import_module("nodupe.tools.leap_year.leap_year")
    LeapYearTool = getattr(leap_mod, "LeapYearTool")
    ly = LeapYearTool()
    assert ly.is_leap_year(2024) is True


def test_smoke_ipc_and_ratelimiter():
    # ToolIPCServer can be instantiated without starting the server
    ipc_mod = importlib.import_module("nodupe.core.api.ipc")
    ToolIPCServer = getattr(ipc_mod, "ToolIPCServer")
    registry_mod = importlib.import_module("nodupe.core.tool_system.registry")
    ToolRegistry = getattr(registry_mod, "ToolRegistry")
    reg = ToolRegistry()

    server = ToolIPCServer(reg)
    assert hasattr(server, "start") and hasattr(server, "stop")

    # RateLimiter basic behavior
    rl_mod = importlib.import_module("nodupe.core.api.ratelimit")
    RateLimiter = getattr(rl_mod, "RateLimiter")
    rl = RateLimiter(requests_per_minute=5)
    assert rl.check_rate_limit() is True
    for _ in range(3):
        rl.check_rate_limit("client1")
    assert isinstance(rl.throttle("client1"), float)


def test_smoke_query_cache_operations():
    qc_mod = importlib.import_module("nodupe.tools.databases.query_cache")
    QueryCache = getattr(qc_mod, "QueryCache")
    qc = QueryCache(max_size=2, ttl_seconds=1)

    assert qc.get_result("select 1") is None
    qc.set_result("select 1", result=[1])
    assert qc.get_result("select 1") == [1]

    qc.set_result("select 2", result=[2])
    qc.set_result("select 3", result=[3])  # should evict oldest
    stats = qc.get_stats()
    assert "hits" in stats and "misses" in stats


def test_smoke_database_indexing_basic():
    import sqlite3

    idx_mod = importlib.import_module("nodupe.tools.databases.indexing")
    DatabaseIndexing = getattr(idx_mod, "DatabaseIndexing")

    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
    conn.commit()

    di = DatabaseIndexing(conn)
    # Create a simple index on an existing table
    di.create_index("idx_test_value", "test", ["value"], if_not_exists=True)
    indexes = di.get_indexes("test")
    assert any("idx_test_value" in idx["name"] for idx in indexes)

    # Test convenience helper
    create_covering_index = getattr(idx_mod, "create_covering_index", None)
    if create_covering_index:
        create_covering_index(conn, "idx_covering", "test", ["value"], ["id"])
        indexes = di.get_indexes("test")
        assert any("idx_covering" in idx["name"] for idx in indexes)


def test_smoke_cli_handler_help():
    main_mod = importlib.import_module("nodupe.core.main")
    CLIHandler = getattr(main_mod, "CLIHandler")

    class DummyLoader:
        pass

    dummy = DummyLoader()
    dummy.tool_registry = None
    dummy.container = None
    dummy.config = None

    cli = CLIHandler(dummy)
    # Running with no args prints help and returns 0
    rc = cli.run([])
    assert rc == 0


def test_query_cache_advanced_operations():
    qc_mod = importlib.import_module("nodupe.tools.databases.query_cache")
    QueryCache = getattr(qc_mod, "QueryCache")
    qc = QueryCache(max_size=3, ttl_seconds=1)

    qc.set_result("select a", result={"a": 1})
    qc.set_result("select b", result={"b": 2})
    qc.set_result("select c", result={"c": 3})

    assert qc.is_cached("select a") is True
    assert qc.get_cached_queries()

    # Resize down to force evictions
    qc.resize(1)
    assert qc.get_cache_size() <= 1

    # Invalidate and validate cache
    qc.invalidate("select b")
    qc.invalidate_all()
    assert qc.get_cache_size() == 0

    # Test invalidate_by_prefix and get_memory_usage
    qc.set_result("user:1:query", result=[1])
    qc.set_result("user:2:query", result=[2])
    removed = qc.invalidate_by_prefix("user:1")
    assert isinstance(removed, int)
    assert isinstance(qc.get_memory_usage(), int)


def test_database_indexing_stats_and_info():
    import sqlite3

    idx_mod = importlib.import_module("nodupe.tools.databases.indexing")
    DatabaseIndexing = getattr(idx_mod, "DatabaseIndexing")

    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, val TEXT)")
    conn.commit()

    di = DatabaseIndexing(conn)
    di.create_index("idx_demo_val", "demo", ["val"], if_not_exists=True)

    info = di.get_index_info("idx_demo_val")
    assert isinstance(info, list)

    stats = di.get_index_stats()
    assert isinstance(stats, dict)


def test_ratelimiter_and_decorator():
    rl_mod = importlib.import_module("nodupe.core.api.ratelimit")
    RateLimiter = getattr(rl_mod, "RateLimiter")
    rate_limited = getattr(rl_mod, "rate_limited")
    RateLimitExceeded = getattr(rl_mod, "RateLimitExceeded")

    rl = RateLimiter(requests_per_minute=2)
    assert rl.check_rate_limit()

    @rate_limited(requests_per_minute=2)
    def small_func():
        return "ok"

    assert small_func() == "ok"
    assert small_func() == "ok"
    try:
        small_func()
        raised = False
    except RateLimitExceeded:
        raised = True
    assert raised is True


def test_cli_apply_overrides_and_ipc_log_event():
    # Test CLIHandler._apply_overrides behavior
    main_mod = importlib.import_module("nodupe.core.main")
    CLIHandler = getattr(main_mod, "CLIHandler")

    class DummyLoader:
        pass

    dummy = DummyLoader()
    dummy.tool_registry = None
    dummy.container = None
    dummy.config = type("C", (), {"config": {}})()

    cli = CLIHandler(dummy)
    ns = type("N", (), {"cores": 4, "max_workers": 8, "batch_size": 32})()
    cli._apply_overrides(ns)
    assert dummy.config.config["cpu_cores"] == 4
    assert dummy.config.config["max_workers"] == 8
    assert dummy.config.config["batch_size"] == 32

    # Test IPC _log_event (no side-effects)
    ipc_mod = importlib.import_module("nodupe.core.api.ipc")
    ToolIPCServer = getattr(ipc_mod, "ToolIPCServer")
    registry_mod = importlib.import_module("nodupe.core.tool_system.registry")
    ToolRegistry = getattr(registry_mod, "ToolRegistry")
    reg = ToolRegistry()
    server = ToolIPCServer(reg)

    from nodupe.core.api.codes import ActionCode

    server._log_event(ActionCode.FAU_GEN_START, "smoke-test", level="debug")
    # no exception == success
