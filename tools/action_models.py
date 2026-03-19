"""Shared models used by low-risk action executors.

Right now this module contains ``ActionExecutionResult``, the standard response
shape returned by both health and security action executors.

Keeping this model in one file avoids duplication and makes both action layers
return the same structure:
- ``action_name``: which allowlisted action was requested
- ``executed``: whether the action really ran
- ``details``: the result payload or rejection reason
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ActionExecutionResult:
    # We keep execution metadata separate from raw command output.
    action_name: str
    executed: bool
    details: dict
