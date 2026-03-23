"""Typed return model shared by all agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class AgentReport:
    role: str
    snapshot: dict
    details: dict
    message: str

    def to_dict(self) -> dict:
        """Plain dictionary for JSON serialization."""
        return asdict(self)
