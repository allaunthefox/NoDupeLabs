import importlib.util
import nodupe
from nodupe.deps import check_dep

def test_vendor_pillow_discovered():
    # importing nodupe should add vendor libs to sys.path
    assert importlib.util.find_spec('pillow') is not None
    assert importlib.util.find_spec('PIL') is not None
    # check_dep should return True because vendor 'pillow' exists
    assert check_dep('pillow') is True

def test_image_api_available():
    from PIL import Image as PILImageModule
    from PIL.Image import Image as ImageClass
    # Ensure module exposes open and class
    assert hasattr(PILImageModule, 'open')
    assert ImageClass is not None
