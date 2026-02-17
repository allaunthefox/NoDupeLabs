import argparse
from types import SimpleNamespace
from unittest.mock import Mock, patch

from nodupe.tools.commands.lut_command import LUTTool
from nodupe.core.api.codes import ActionCode


def test_lut_tool_basic_properties():
    t = LUTTool()
    assert t.name == "lut_service"
    assert t.version == "1.0.0"
    assert t.dependencies == []


def test_api_methods_and_initialize():
    t = LUTTool()
    fake_container = Mock()
    t.initialize(fake_container)
    fake_container.register_service.assert_called_with("lut_service", t)

    methods = t.api_methods
    assert "get_codes" in methods and "describe_code" in methods
    # check that describe_code delegates to ActionCode.get_description
    assert methods["describe_code"](ActionCode.FIA_UAU_INIT) == ActionCode.get_description(ActionCode.FIA_UAU_INIT)


def test_run_standalone_help_and_lookup(capfd):
    t = LUTTool()

    # No args -> prints help and returns 0
    rc = t.run_standalone([])
    assert rc == 0

    # With --code argument it should print a code description
    rc = t.run_standalone(["--code", str(ActionCode.FIA_UAU_INIT)])
    assert rc == 0
    out = capfd.readouterr().out
    assert "Code" in out


def test_get_capabilities_contains_expected_keys():
    t = LUTTool()
    caps = t.get_capabilities()
    assert "specification" in caps and "features" in caps
