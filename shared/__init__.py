"""Shared application modules used across the project."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.config import AppConfig

__all__ = ["AppConfig", "load_config"]


def __getattr__(name: str) -> Any:
    """Lazy-load shared exports to keep package imports lightweight."""
    export_map = {
        "AppConfig": ("shared.config", "AppConfig"),
        "load_config": ("shared.config", "load_config"),
    }
    if name not in export_map:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = export_map[name]
    module = import_module(module_name)
    return getattr(module, attr_name)
