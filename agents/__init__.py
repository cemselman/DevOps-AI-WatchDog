"""Group the specialized agent modules under one package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agents.remediation_advisor_agent import RemediationAdvisorAgent
    from agents.security_agent import SecurityReviewAgent
    from agents.system_health_agent import SystemHealthAgent
    from shared.agent_report import AgentReport

__all__ = ["AgentReport", "RemediationAdvisorAgent", "SecurityReviewAgent", "SystemHealthAgent"]


def __getattr__(name: str) -> Any:
    """Lazy-load agent exports to avoid import-time dependency side effects."""
    export_map = {
        "AgentReport": ("shared.agent_report", "AgentReport"),
        "RemediationAdvisorAgent": (
            "agents.remediation_advisor_agent",
            "RemediationAdvisorAgent",
        ),
        "SecurityReviewAgent": ("agents.security_agent", "SecurityReviewAgent"),
        "SystemHealthAgent": ("agents.system_health_agent", "SystemHealthAgent"),
    }
    if name not in export_map:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = export_map[name]
    module = import_module(module_name)
    return getattr(module, attr_name)
