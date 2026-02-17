import json
from unittest.mock import Mock

import pytest

from nodupe.core.api.ipc import ToolIPCServer


def test_send_response_and_error_and_log_event():
    registry = Mock()
    server = ToolIPCServer(registry, socket_path="/tmp/doesnotexist.sock")

    # Mock connection with sendall
    conn = Mock()

    # send response
    server._send_response(conn, {"ok": True}, request_id=42)
    assert conn.sendall.called
    sent = json.loads(conn.sendall.call_args[0][0].decode("utf-8"))
    assert sent["id"] == 42
    assert "result" in sent

    # send error
    conn.reset_mock()
    server._send_error(conn, "err", request_id=99, code=123456)
    assert conn.sendall.called
    err_sent = json.loads(conn.sendall.call_args[0][0].decode("utf-8"))
    assert err_sent["id"] == 99
    assert "error" in err_sent

    # log event should call logging (patch logger at runtime)
    mock_logger = Mock()
    from pytest import MonkeyPatch
    from nodupe.core.api.codes import ActionCode

    with MonkeyPatch.context() as m:
        m.setattr("logging.getLogger", lambda name=None: mock_logger)
        server._log_event(ActionCode.FAU_GEN_START, "msg", level="info", extra=1)
        mock_logger.info.assert_called()
