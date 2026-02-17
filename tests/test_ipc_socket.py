import json
import os
import socket
import sys
import time
from pathlib import Path


def test_ipc_call(tool, method, params=None):
    socket_path = "/tmp/nodupe.sock"
    if not os.path.exists(socket_path):
        print(f"Error: Socket {socket_path} not found")
        return None

    request = {
        "jsonrpc": "2.0",
        "tool": tool,
        "method": method,
        "params": params or {},
        "id": 1,
    }

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(socket_path)
            client.sendall(json.dumps(request).encode("utf-8"))

            data = client.recv(4096)
            if not data:
                return None

            return json.loads(data.decode("utf-8"))
    except Exception as e:
        print(f"IPC Call error: {e}")
        return None


if __name__ == "__main__":
    print("Testing Tool IPC Socket Interface...")

    # Test LeapYear tool
    print("\n1. Testing leap_year_algorithm.is_leap_year(2024):")
    res = test_ipc_call("leap_year_algorithm", "is_leap_year", {"year": 2024})
    print(json.dumps(res, indent=2))

    # Test Standard Hashing tool (ISO 10118-3)
    print("\n2. Testing hashing_standard.hash_string('hello'):")
    res = test_ipc_call("hashing_standard", "hash_string", {"data": "hello"})
    print(json.dumps(res, indent=2))

    print("\n2b. Verifying ISO 10118-3 compliance check:")
    res = test_ipc_call(
        "hashing_standard", "check_iso_compliance", {"algorithm": "sha256"}
    )
    print(json.dumps(res, indent=2))

    # Test Standard MIME tool
    print("\n3. Testing standard_mime.is_text('text/plain'):")
    res = test_ipc_call("standard_mime", "is_text", {"mime_type": "text/plain"})
    print(json.dumps(res, indent=2))

    # Test Sensitive method (Archive extraction)
    print("\n4. Testing sensitive method (standard_archive.extract_archive):")
    # This should trigger a SECURITY_RISK_FLAGGED event in logs
    res = test_ipc_call(
        "standard_archive",
        "extract_archive",
        {"archive_path": "/nonexistent.zip", "extract_to": "/tmp/out"},
    )
    print(json.dumps(res, indent=2))

    # Test LUT Service
    print("\n5. Testing LUT service (lut_service.describe_code):")
    # Using 120000 (OAIS_SIP_INGEST) as a core archival code
    res = test_ipc_call("lut_service", "describe_code", {"code": 120000})
    print(json.dumps(res, indent=2))
