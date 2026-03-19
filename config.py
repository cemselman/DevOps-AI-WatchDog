"""Load environment-driven application settings into one config object."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


def _default_monitored_services() -> list[str]:
    """Return the default service names monitored by the app."""
    return ["nginx", "docker", "ssh"]


@dataclass(slots=True)
class AppConfig:
    # Central app settings are kept here so every module reads the same values.
    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    auto_approve_low_risk: bool = False
    monitored_services: list[str] = field(default_factory=_default_monitored_services)
    disk_usage_warning_percent: int = 85
    health_log_line_count: int = 20
    security_log_line_count: int = 30
    login_history_count: int = 10
    command_timeout_seconds: int = 30


def _parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse common env-style booleans safely."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_services(value: str | None) -> list[str]:
    """Turn a comma-separated service list into Python strings."""
    if not value:
        return _default_monitored_services()
    services = [item.strip() for item in value.split(",")]
    return [item for item in services if item]


def load_config() -> AppConfig:
    """Load runtime settings from the .env file."""
    load_dotenv()

    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        auto_approve_low_risk=_parse_bool(
            os.getenv("AUTO_APPROVE_LOW_RISK"),
            default=False,
        ),
        monitored_services=_parse_services(os.getenv("MONITORED_SERVICES")),
        disk_usage_warning_percent=int(os.getenv("DISK_USAGE_WARNING_PERCENT", "85")),
        health_log_line_count=int(os.getenv("HEALTH_LOG_LINE_COUNT", "20")),
        security_log_line_count=int(os.getenv("SECURITY_LOG_LINE_COUNT", "30")),
        login_history_count=int(os.getenv("LOGIN_HISTORY_COUNT", "10")),
        command_timeout_seconds=int(os.getenv("COMMAND_TIMEOUT_SECONDS", "30")),
    )
