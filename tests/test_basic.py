import pytest
from nodupe.scanner import validate_hash_algo  # type: ignore # pylint: disable=import-error
from nodupe.categorizer import categorize_file  # type: ignore # pylint: disable=import-error

def test_validate_hash_algo():
    assert validate_hash_algo("sha512") == "sha512"
    assert validate_hash_algo("SHA256") == "sha256"
    
    with pytest.raises(ValueError):
        validate_hash_algo("invalid_algo")

def test_categorize_file():
    # Images
    cat = categorize_file("image/jpeg", "photo.jpg")
    assert cat["category"] == "image"
    
    # Archives
    cat = categorize_file("application/zip", "backup.zip")
    assert cat["category"] == "archive"
    
    # Text
    cat = categorize_file("text/plain", "readme.txt")
    assert cat["category"] == "text"
    
    # Unknown
    cat = categorize_file("application/octet-stream", "unknown.bin")
    assert cat["category"] == "other"
