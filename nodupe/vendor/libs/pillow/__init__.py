# Alias package so importlib.find_spec('pillow') succeeds for deps.check
from PIL import Image, open
__all__ = ['Image', 'open']
