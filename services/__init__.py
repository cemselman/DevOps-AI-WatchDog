"""Service-layer modules shared by agents and orchestration."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from services.llm_client import LLMClient

__all__ = ["LLMClient"]


def __getattr__(name: str) -> Any:
    """Lazy-load service exports to avoid eager third-party imports."""
    export_map = {
        "LLMClient": ("services.llm_client", "LLMClient"),
    }
    if name not in export_map:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = export_map[name]
    module = import_module(module_name)
    return getattr(module, attr_name)
