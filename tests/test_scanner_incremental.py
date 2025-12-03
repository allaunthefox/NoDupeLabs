import tempfile
import time
from pathlib import Path
from nodupe.scanner import threaded_hash

def test_threaded_hash_incremental():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        f1 = root / "f1.txt"
        f1.write_bytes(b"content1")
        
        # First scan
        res1, _, _ = threaded_hash([str(root)], ignore=[])
        assert len(res1) == 1
        path1, size1, mtime1, hash1, _, _, _, _ = res1[0]
        
        # Build known_files dict
        known = {path1: (size1, mtime1, hash1)}
        
        # Second scan - should use cached hash
        # We can verify this by mocking hash_file, but simpler is to trust the logic
        # or check if mtime is preserved.
        
        # Let's modify the file but keep mtime/size same (hard to do without tools)
        # Instead, let's modify the known hash to a fake one.
        # If it uses the cache, it will return the fake hash.
        
        fake_hash = "fake_hash_123"
        known_fake = {path1: (size1, mtime1, fake_hash)}
        
        res2, _, _ = threaded_hash([str(root)], ignore=[], known_files=known_fake)
        assert len(res2) == 1
        assert res2[0][3] == fake_hash
        
        # Now modify file (touch) -> mtime changes
        time.sleep(1.1) # Ensure mtime diff
        f1.touch()
        
        res3, _, _ = threaded_hash([str(root)], ignore=[], known_files=known_fake)
        assert len(res3) == 1
        # Should NOT be fake hash because mtime changed
        assert res3[0][3] != fake_hash
        assert res3[0][3] == hash1 # Content is same, so real hash is same
