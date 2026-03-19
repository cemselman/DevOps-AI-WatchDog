"""Shared subprocess helpers for all tool modules.

This module is the lowest-level execution layer under ``tools/``.
Other modules should not call ``subprocess`` directly; instead they should use
``run_command()`` so command results always come back in the same shape.

Typical examples:
- ``run_command(["df", "-h", "/"])`` for disk usage
- ``run_command(["ss", "-tuln"])`` for open ports

This keeps stdout/stderr normalization, timeout handling, and JSON-safe text
conversion in one place.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from dataclasses import asdict, dataclass

log = logging.getLogger("watchdog.cmd")


@dataclass(slots=True)
class CommandResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int

    def to_dict(self) -> dict:
        """Return a plain dictionary suitable for JSON serialization."""
        return asdict(self)


def _normalize_output(value: str | bytes | None, default: str = "") -> str:
    """Convert subprocess output to plain text safe for JSON serialization."""
    if value is None:
        return default
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return value.strip()


DEFAULT_TIMEOUT: int = 30


def configure_timeout(seconds: int) -> None:
    """Override the default command timeout at startup."""
    global DEFAULT_TIMEOUT  # noqa: PLW0603
    DEFAULT_TIMEOUT = seconds


def run_command(command: list[str], *, timeout: int | None = None) -> CommandResult:
    """Run one safe command and capture its output."""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout if timeout is not None else DEFAULT_TIMEOUT,
            check=False,
        )
        return CommandResult(
            command=shlex.join(command),
            stdout=_normalize_output(completed.stdout),
            stderr=_normalize_output(completed.stderr),
            exit_code=completed.returncode,
        )
    except FileNotFoundError as exc:
        log.warning("Command not found: %s", shlex.join(command))
        return CommandResult(
            command=shlex.join(command),
            stdout="",
            stderr=str(exc),
            exit_code=127,
        )
    except subprocess.TimeoutExpired as exc:
        log.warning("Command timed out: %s", shlex.join(command))
        return CommandResult(
            command=shlex.join(command),
            stdout=_normalize_output(exc.stdout),
            stderr=_normalize_output(exc.stderr, default="Command timed out."),
            exit_code=124,
        )
