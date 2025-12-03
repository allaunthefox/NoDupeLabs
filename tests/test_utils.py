# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import os
import tempfile
import unittest
from pathlib import Path
from nodupe.utils.hashing import validate_hash_algo, hash_file
from nodupe.utils.filesystem import should_skip, detect_context, get_mime_safe, get_permissions

class TestUtils(unittest.TestCase):
    def test_validate_hash_algo(self):
        self.assertEqual(validate_hash_algo("sha512"), "sha512")
        self.assertEqual(validate_hash_algo("SHA256"), "sha256")
        
        with self.assertRaises(ValueError):
            validate_hash_algo("invalid_algo")

    def test_hash_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"hello world")
            tmp_path = Path(tmp.name)
        
        try:
            # sha512 of "hello world"
            expected_sha512 = "309ecc489c12d6eb4cc40f50c902f2b4d0ed77ee511a7c7a9bcd3ca86d4cd86f989dd35bc5ff499670da34255b45b0cfd830e81f605dcf7dc5542e93ae9cd76f"
            self.assertEqual(hash_file(tmp_path, "sha512"), expected_sha512)
            
            # md5 of "hello world"
            expected_md5 = "5eb63bbbe01eeed093cb22bb8f5acdc3"
            self.assertEqual(hash_file(tmp_path, "md5"), expected_md5)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_should_skip(self):
        ignore_list = [".git", "node_modules"]
        
        self.assertTrue(should_skip(Path("/path/to/.git/config"), ignore_list))
        self.assertTrue(should_skip(Path("/path/to/node_modules/package.json"), ignore_list))
        self.assertFalse(should_skip(Path("/path/to/src/main.py"), ignore_list))

    def test_detect_context(self):
        self.assertEqual(detect_context(Path("/home/user/Downloads/extracted/file.txt")), "archived")
        self.assertEqual(detect_context(Path("/home/user/Documents/project/file.txt")), "unarchived")
        self.assertEqual(detect_context(Path("/backup/2025/data.db")), "archived")

    def test_get_mime_safe(self):
        self.assertEqual(get_mime_safe(Path("image.webp")), "image/webp")
        self.assertEqual(get_mime_safe(Path("document.pdf")), "application/pdf")
        self.assertEqual(get_mime_safe(Path("unknown.xyz123")), "application/octet-stream")

    def test_get_permissions(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            # Set permissions to 644 (rw-r--r--)
            os.chmod(tmp_path, 0o644)
            perms = get_permissions(tmp_path)
            # The output format is octal string, e.g., '0o644'
            self.assertEqual(perms, "0o644")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

if __name__ == "__main__":
    unittest.main()
