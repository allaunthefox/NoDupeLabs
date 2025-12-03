# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import unittest
from unittest.mock import MagicMock, patch
from nodupe.commands.init import cmd_init
from nodupe.commands.scan import cmd_scan
from nodupe.commands.plan import cmd_plan
from nodupe.commands.apply import cmd_apply
from nodupe.commands.rollback import cmd_rollback
from nodupe.commands.verify import cmd_verify
from nodupe.commands.mount import cmd_mount
from nodupe.commands.archive import cmd_archive_list, cmd_archive_extract
from nodupe.commands.similarity import cmd_similarity_build

class TestCommandsStructure(unittest.TestCase):
    def test_command_signatures(self):
        # All commands should accept (args, cfg)
        self.assertTrue(callable(cmd_init))
        self.assertTrue(callable(cmd_scan))
        self.assertTrue(callable(cmd_plan))
        self.assertTrue(callable(cmd_apply))
        self.assertTrue(callable(cmd_rollback))
        self.assertTrue(callable(cmd_verify))
        self.assertTrue(callable(cmd_mount))
        self.assertTrue(callable(cmd_archive_list))
        self.assertTrue(callable(cmd_archive_extract))
        self.assertTrue(callable(cmd_similarity_build))

    def test_cmd_init_creates_config(self):
        # Mock args and ensure_config
        args = MagicMock()
        args.preset = "default"
        args.force = False
        
        with patch("nodupe.commands.init.ensure_config") as mock_ensure:
            with patch("pathlib.Path.exists", return_value=False):
                ret = cmd_init(args, {})
                self.assertEqual(ret, 0)
                mock_ensure.assert_called_once_with("nodupe.yml", preset="default")

    def test_cmd_init_respects_existing_config(self):
        args = MagicMock()
        args.preset = "default"
        args.force = False
        
        with patch("nodupe.commands.init.ensure_config") as mock_ensure:
            with patch("pathlib.Path.exists", return_value=True):
                ret = cmd_init(args, {})
                self.assertEqual(ret, 1)
                mock_ensure.assert_not_called()

    def test_cmd_init_force_overwrite(self):
        args = MagicMock()
        args.preset = "default"
        args.force = True
        
        with patch("nodupe.commands.init.ensure_config") as mock_ensure:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.unlink") as mock_unlink:
                    ret = cmd_init(args, {})
                    self.assertEqual(ret, 0)
                    mock_unlink.assert_called_once()
                    mock_ensure.assert_called_once_with("nodupe.yml", preset="default")

if __name__ == "__main__":
    unittest.main()
