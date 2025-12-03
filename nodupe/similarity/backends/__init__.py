"""Discoverable similarity backends loader.

This package exposes mechanisms to discover available similarity backend modules
found inside the `nodupe.similarity.backends` package. Each backend module
should provide a `create(dim: int)` factory function returning an object that
implements `add(vectors, ids)` and `search(vector, k)`.

Backend modules can be added/removed independently, making the system modular.
"""
from __future__ import annotations
import importlib
import pkgutil
from typing import Dict, Callable, List

_BACKENDS: Dict[str, object] = {}


def _discover():
    # scan submodules in this package
    package = __name__
    # pkgutil requires a package object
    mod = importlib.import_module(package)
    path = getattr(mod, '__path__', [])
    for finder, name, ispkg in pkgutil.iter_modules(path):
        if name.startswith('_'):
            continue
        full = f"{package}.{name}"
        try:
            m = importlib.import_module(full)
            if hasattr(m, 'create'):
                _BACKENDS[name] = m
        except Exception:
            # Ignore modules that fail to import so adding/removing remains safe
            continue


def list_backends() -> List[str]:
    if not _BACKENDS:
        _discover()
    return sorted(_BACKENDS.keys())


def get_factory(name: str):
    if not _BACKENDS:
        _discover()
    mod = _BACKENDS.get(name)
    if not mod:
        return None
    return getattr(mod, 'create', None)


def default_backend_name() -> str:
    # Prefer faiss if available, else bruteforce. Only pick modules that expose 'available()' and return True
    names = list_backends()
    for prefer in ('faiss_backend', 'faiss', 'bruteforce_backend', 'bruteforce'):
        if prefer in names:
            mod = _BACKENDS.get(prefer)
            if mod is None:
                continue
            avail = getattr(mod, 'available', None)
            if callable(avail):
                try:
                    if avail():
                        return prefer
                except Exception:
                    continue
            else:
                # if backend doesn't expose availability, assume present
                return prefer
    return names[0] if names else ''


__all__ = ['list_backends', 'get_factory', 'default_backend_name']
