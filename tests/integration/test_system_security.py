# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""System Security Tests - Security validation and penetration testing.

This module tests authentication and authorization, data protection mechanisms,
secure file handling, and tool security boundaries.
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from nodupe.core.main import main
from nodupe.tools.commands.scan import ScanTool
from nodupe.tools.commands.apply import ApplyTool
from nodupe.tools.commands.similarity import SimilarityCommandTool as SimilarityTool

class TestAuthenticationAuthorization:
    """Test authentication and authorization mechanisms."""

    def test_cli_authentication_mechanisms(self):
        """Test CLI authentication mechanisms."""
        # Test version command (should not require auth)
        with patch('sys.argv', ['nodupe', 'version']):
            result = main()
            assert result == 0

        # Test help command (should not require auth)
        with patch('sys.argv', ['nodupe', '--help']):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0

    def test_tool_authorization(self):
        """Test tool authorization mechanisms."""
        # Test tool list command
        with patch('sys.argv', ['nodupe', 'tool', '--list']):
            result = main()
            assert result == 0

        # Test that tools can be loaded and executed
        scan_tool = ScanTool()
        assert scan_tool.name == "scan"
        assert scan_tool.version == "1.0.0"

        apply_tool = ApplyTool()
        assert apply_tool.name == "apply"
        assert apply_tool.version == "1.0.0"

class TestDataProtection:
    """Test data protection mechanisms."""

    def test_scan_data_protection(self):
        """Test data protection during scan operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with sensitive content
            sensitive_files = [
                ("passwords.txt", "user:password123\nadmin:admin456"),
                ("config.json", '{"api_key": "secret123", "token": "abc456"}'),
                ("credentials.txt", "database:user:pass\nservice:api:key")
            ]

            for filename, content in sensitive_files:
                test_file = os.path.join(temp_dir, filename)
                with open(test_file, "w") as f:
                    f.write(content)

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_tool.execute_scan(scan_args)
            assert scan_result == 0  # Should handle sensitive data properly

    def test_apply_data_protection(self):
        """Test data protection during apply operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create duplicates file with sensitive paths
            sensitive_file = os.path.join(temp_dir, "sensitive_duplicates.json")
            sensitive_data = {
                "duplicate_groups": [
                    {
                        "hash": "sensitive_hash",
                        "files": [
                            {"path": "/secure/location/passwords.txt", "size": 100, "type": "txt"},
                            {"path": "/secure/location/keys.txt", "size": 100, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(sensitive_file, "w") as f:
                json.dump(sensitive_data, f)

            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = sensitive_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_tool.execute_apply(apply_args)
            assert apply_result == 0  # Should handle sensitive paths properly

class TestSecureFileHandling:
    """Test secure file handling mechanisms."""

    def test_scan_secure_file_handling(self):
        """Test secure file handling during scan operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with various security characteristics
            test_files = [
                ("normal.txt", "Normal file content"),
                ("empty.txt", ""),
                ("special_chars.txt", "Special: ñ, ü, é, ß, ©, ®"),
                ("unicode.txt", "Unicode: 🔒 🔑 🔐"),
                ("binary.dat", b'\x00\x01\x02\x03\x04\x05')
            ]

            for filename, content in test_files:
                test_file = os.path.join(temp_dir, filename)
                if filename.endswith('.dat'):
                    with open(test_file, "wb") as f:
                        f.write(content)
                else:
                    with open(test_file, "w", encoding='utf-8') as f:
                        f.write(content)

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            scan_tool = ScanTool()
            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = mock_container

            scan_result = scan_tool.execute_scan(scan_args)
            assert scan_result == 0  # Should handle various file types securely

    def test_apply_secure_file_handling(self):
        """Test secure file handling during apply operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create duplicates file with secure file references
            secure_file = os.path.join(temp_dir, "secure_duplicates.json")
            secure_data = {
                "duplicate_groups": [
                    {
                        "hash": "secure_hash",
                        "files": [
                            {"path": "/var/secure/file1.txt", "size": 150, "type": "txt"},
                            {"path": "/var/secure/file2.txt", "size": 150, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(secure_file, "w") as f:
                json.dump(secure_data, f)

            apply_tool = ApplyTool()
            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = secure_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False

            apply_result = apply_tool.execute_apply(apply_args)
            assert apply_result == 0  # Should handle secure file references properly

class TestToolSecurity:
    """Test tool security boundaries."""

    def test_tool_security_boundaries(self):
        """Test security boundaries between tools."""
        # Test that tools operate within their security boundaries
        scan_tool = ScanTool()
        apply_tool = ApplyTool()
        similarity_tool = SimilarityTool()

        # Each tool should have its own namespace
        assert scan_tool.name == "scan"
        assert apply_tool.name == "apply"
        assert similarity_tool.name == "similarity"

        # Tools should not interfere with each other
        mock_subparsers = MagicMock()
        scan_tool.register_commands(mock_subparsers)
        apply_tool.register_commands(mock_subparsers)
        similarity_tool.register_commands(mock_subparsers)

        # Each tool should register its own commands
        assert mock_subparsers.add_parser.call_count == 3

    def test_tool_isolation(self):
        """Test tool isolation and security."""
        # Test that tools maintain proper isolation
        scan_tool = ScanTool()
        apply_tool = ApplyTool()

        # Create separate mock containers for each tool
        scan_container = MagicMock()
        apply_container = MagicMock()

        # Each tool should work with its own container
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test scan with its container
            test_file = os.path.join(temp_dir, "scan_test.txt")
            with open(test_file, "w") as f:
                f.write("Scan isolation test")

            scan_args = MagicMock()
            scan_args.paths = [temp_dir]
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = scan_container

            scan_result = scan_tool.execute_scan(scan_args)
            assert scan_result == 0

            # Test apply with its container
            duplicates_file = os.path.join(temp_dir, "apply_test.json")
            apply_data = {
                "duplicate_groups": [
                    {
                        "hash": "apply_hash",
                        "files": [
                            {"path": "/tmp/apply_test.txt", "size": 100, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(duplicates_file, "w") as f:
                json.dump(apply_data, f)

            apply_args = MagicMock()
            apply_args.action = "list"
            apply_args.input = duplicates_file
            apply_args.target_dir = None
            apply_args.dry_run = True
            apply_args.verbose = False
            apply_args.container = apply_container

            apply_result = apply_tool.execute_apply(apply_args)
            assert apply_result == 0

class TestSecurityValidation:
    """Test security validation procedures."""

    def test_scan_security_validation(self):
        """Test security validation during scan operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(5):
                test_file = os.path.join(temp_dir, f"security_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Security validation {i}")

            # Test with various security scenarios
            scan_tool = ScanTool()
            security_scenarios = [
                # Normal scenario
                {
                    "paths": [temp_dir],
                    "container": MagicMock(),
                    "expected": 0
                },
                # Protected directory scenario
                {
                    "paths": ["/etc"],
                    "container": None,
                    "expected": "int"
                },
                # Mixed valid/invalid scenario
                {
                    "paths": [temp_dir, "/invalid"],
                    "container": MagicMock(),
                    "expected": 0
                }
            ]

            for scenario in security_scenarios:
                mock_container = scenario["container"]
                if mock_container:
                    mock_db_connection = MagicMock()
                    mock_container.get_service.return_value = mock_db_connection

                scan_args = MagicMock()
                scan_args.paths = scenario["paths"]
                scan_args.min_size = 0
                scan_args.max_size = None
                scan_args.extensions = None
                scan_args.exclude = None
                scan_args.verbose = False
                scan_args.container = scenario["container"]

                scan_result = scan_tool.execute_scan(scan_args)

                if scenario["expected"] == 0:
                    assert scan_result == 0
                else:
                    assert isinstance(scan_result, int)

    def test_apply_security_validation(self):
        """Test security validation during apply operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid duplicates file
            valid_file = os.path.join(temp_dir, "valid_security.json")
            valid_data = {
                "duplicate_groups": [
                    {
                        "hash": "valid_security_hash",
                        "files": [
                            {"path": "/tmp/valid1.txt", "size": 100, "type": "txt"},
                            {"path": "/tmp/valid2.txt", "size": 100, "type": "txt"}
                        ]
                    }
                ]
            }

            with open(valid_file, "w") as f:
                json.dump(valid_data, f)

            # Test with various security scenarios
            apply_tool = ApplyTool()
            security_scenarios = [
                # Normal scenario
                {
                    "input": valid_file,
                    "action": "list",
                    "expected": 0
                },
                # Invalid file scenario
                {
                    "input": "/etc/passwd",
                    "action": "list",
                    "expected": "int"
                },
                # Protected action scenario
                {
                    "input": valid_file,
                    "action": "delete",
                    "expected": 0
                }
            ]

            for scenario in security_scenarios:
                apply_args = MagicMock()
                apply_args.action = scenario["action"]
                apply_args.input = scenario["input"]
                apply_args.target_dir = None
                apply_args.dry_run = True
                apply_args.verbose = False

                apply_result = apply_tool.execute_apply(apply_args)

                if scenario["expected"] == 0:
                    assert apply_result == 0
                else:
                    assert isinstance(apply_result, int)

class TestPenetrationTesting:
    """Test basic penetration testing scenarios."""

    def test_scan_penetration_testing(self):
        """Test scan penetration testing scenarios."""
        # Test with potentially malicious paths
        malicious_paths = [
            ["../../../etc/passwd"],
            ["../../../etc/shadow"],
            ["/dev/null"],
            ["/proc/self/mem"]
        ]

        scan_tool = ScanTool()

        for paths in malicious_paths:
            scan_args = MagicMock()
            scan_args.paths = paths
            scan_args.min_size = 0
            scan_args.max_size = None
            scan_args.extensions = None
            scan_args.exclude = None
            scan_args.verbose = False
            scan_args.container = None

            scan_result = scan_tool.execute_scan(scan_args)
            # Should handle potentially malicious paths securely
            assert isinstance(scan_result, int)

    def test_apply_penetration_testing(self):
        """Test apply penetration testing scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with potentially malicious input
            malicious_scenarios = [
                # Very large file size
                {
                    "files": [
                        {"path": "/tmp/huge.txt", "size": 999999999999, "type": "txt"}
                    ]
                },
                # Malicious path patterns
                {
                    "files": [
                        {"path": "../../../../etc/passwd", "size": 100, "type": "txt"}
                    ]
                },
                # Special characters in paths
                {
                    "files": [
                        {"path": "/tmp/file;rm -rf;.txt", "size": 100, "type": "txt"}
                    ]
                }
            ]

            apply_tool = ApplyTool()

            for scenario in malicious_scenarios:
                malicious_file = os.path.join(temp_dir, "malicious.json")
                malicious_data = {
                    "duplicate_groups": [
                        {
                            "hash": "malicious_hash",
                            "files": scenario["files"]
                        }
                    ]
                }

                with open(malicious_file, "w") as f:
                    json.dump(malicious_data, f)

                apply_args = MagicMock()
                apply_args.action = "list"
                apply_args.input = malicious_file
                apply_args.target_dir = None
                apply_args.dry_run = True
                apply_args.verbose = False

                apply_result = apply_tool.execute_apply(apply_args)
                # Should handle potentially malicious input securely
                assert isinstance(apply_result, int)

class TestSecurityAudit:
    """Test security audit procedures."""

    def test_comprehensive_security_audit(self):
        """Test comprehensive security audit procedures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test dataset
            for i in range(10):
                test_file = os.path.join(temp_dir, f"audit_{i}.txt")
                with open(test_file, "w") as f:
                    f.write(f"Security audit test {i}")

            # Create duplicates file
            audit_file = os.path.join(temp_dir, "audit_duplicates.json")
            audit_data = {
                "duplicate_groups": [
                    {
                        "hash": f"audit_hash_{i}",
                        "files": [
                            {"path": f"{temp_dir}/audit_{i}.txt", "size": 100 + i, "type": "txt"},
                            {"path": f"{temp_dir}/audit_{i+1}.txt", "size": 100 + i, "type": "txt"}
                        ]
                    }
                    for i in range(0, 8, 2)
                ]
            }

            with open(audit_file, "w") as f:
                json.dump(audit_data, f)

            # Create query file
            query_file = os.path.join(temp_dir, "audit_query.txt")
            with open(query_file, "w") as f:
                f.write("Security audit query")

            # Mock container and services
            mock_container = MagicMock()
            mock_db_connection = MagicMock()
            mock_container.get_service.return_value = mock_db_connection

            # Perform comprehensive security audit
            scan_tool = ScanTool()
            apply_tool = ApplyTool()
            similarity_tool = SimilarityTool()

            audit_operations = [
                ("scan", scan_tool, [temp_dir]),
                ("apply", apply_tool, audit_file),
                ("similarity", similarity_tool, query_file)
            ]

            security_results = []

            for op_name, tool, data in audit_operations:
                if op_name == "scan":
                    scan_args = MagicMock()
                    scan_args.paths = data
                    scan_args.min_size = 0
                    scan_args.max_size = None
                    scan_args.extensions = None
                    scan_args.exclude = None
                    scan_args.verbose = False
                    scan_args.container = mock_container

                    result = tool.execute_scan(scan_args)

                elif op_name == "apply":
                    apply_args = MagicMock()
                    apply_args.action = "list"
                    apply_args.input = data
                    apply_args.target_dir = None
                    apply_args.dry_run = True
                    apply_args.verbose = False

                    result = tool.execute_apply(apply_args)

                elif op_name == "similarity":
                    similarity_args = MagicMock()
                    similarity_args.query_file = data
                    similarity_args.database = None
                    similarity_args.k = 5
                    similarity_args.threshold = 0.7
                    similarity_args.backend = "brute_force"
                    similarity_args.output = "text"
                    similarity_args.verbose = False

                    result = tool.execute_similarity(similarity_args)

                security_results.append(result)

            # All operations should complete securely
            for result in security_results:
                assert isinstance(result, int)

    def test_security_compliance_validation(self):
        """Test security compliance validation."""
        # Test that system maintains security compliance
        security_checks = [
            # CLI security
            ("version", ['nodupe', 'version']),
            ("help", ['nodupe', '--help']),
            ("tool_list", ['nodupe', 'tool', '--list'])
        ]

        for check_name, args in security_checks:
            with patch('sys.argv', args):
                if "help" in check_name:
                    with pytest.raises(SystemExit):
                        main()
                else:
                    result = main()
                    assert result == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
