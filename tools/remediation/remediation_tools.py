"""Combine agent findings into a remediation planning context.

This module does not execute shell commands. Instead, it takes the structured
outputs of the health and security agents and turns them into one shared
context that a remediation-focused agent can use to prioritize next steps.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from agents.report import AgentReport


_ACTION_DESCRIPTIONS = {
    "check_cron_security": "Review cron jobs and scheduled tasks.",
    "check_disk": "Re-check root filesystem usage before cleanup decisions.",
    "check_disk_io": "Inspect storage latency before changing workloads.",
    "check_docker_health": "Review running containers and point-in-time Docker stats.",
    "check_docker_security": "Inspect Docker security options and socket exposure.",
    "check_fail2ban_status": "Verify brute-force protection status.",
    "check_failed_services": "List failed systemd services that may need recovery.",
    "check_firewall": "Verify host firewall policy and open access.",
    "check_log_rotation_health": "Confirm logrotate is healthy to avoid log growth.",
    "check_memory": "Re-check memory pressure before changing processes.",
    "check_network_health": "Inspect interfaces and routes for network issues.",
    "check_open_ports": "Review listening ports and exposed services.",
    "check_uptime": "Confirm load and uptime before deeper remediation.",
    "check_user_account_audit": "Review local users and privileged group membership.",
    "check_world_writable_files": "Inspect risky file permissions in common paths.",
    "inspect_root_sizes": "Locate large directories under root.",
    "inspect_var_log_sizes": "Locate large logs and log directories.",
    "list_active_sessions": "Review current interactive sessions.",
    "list_failed_logins": "Review recent failed authentication attempts.",
    "list_recent_logins": "Review recent successful authentication history.",
    "read_kernel_errors": "Check recent kernel-level error messages.",
    "read_nginx_logs": "Inspect recent nginx service logs.",
    "read_ssh_config_audit": "Review effective SSH daemon configuration.",
    "read_ssh_logs": "Inspect recent SSH service logs.",
    "read_sudo_activity": "Review recent sudo command activity.",
    "read_system_logs": "Inspect recent general system journal entries.",
    "status_service": "Check one monitored service status explicitly.",
}


@dataclass(slots=True)
class RemediationSnapshot:
    """High-level remediation inputs prepared for the advisor agent."""

    priority_signals: list[dict]
    low_risk_actions: dict[str, dict]

    def to_dict(self) -> dict:
        """Convert the remediation snapshot to a plain dictionary."""
        return asdict(self)


def build_safe_action_catalog(allowed_actions: list[str]) -> dict[str, dict]:
    """Describe the available low-risk actions in operator-friendly language."""
    catalog: dict[str, dict] = {}
    for action_name in sorted(allowed_actions):
        catalog[action_name] = {
            "action_name": action_name,
            "description": _ACTION_DESCRIPTIONS.get(
                action_name,
                "Low-risk diagnostic action available to the operator.",
            ),
        }
    return catalog


def _message_has_error(text: str) -> bool:
    """Detect simple command or permission errors in collected text."""
    lowered = text.lower()
    return any(
        token in lowered
        for token in ("permission denied", "command not found", "failed", "inactive")
    )


def build_priority_signals(
    health_report: AgentReport,
    security_report: AgentReport,
) -> list[dict]:
    """Extract a few concrete remediation signals from the agent reports."""
    signals: list[dict] = []

    health_text = health_report.message
    security_text = security_report.message

    if "85%" in health_text or "disk usage" in health_text.lower():
        signals.append(
            {
                "source": "system_health",
                "priority": "high",
                "signal": "Root filesystem pressure detected.",
            }
        )

    if "nginx" in health_text.lower() and "inactive" in health_text.lower():
        signals.append(
            {
                "source": "system_health",
                "priority": "medium",
                "signal": "nginx may be inactive or not serving traffic.",
            }
        )

    if "root ssh" in security_text.lower() or "root login" in security_text.lower():
        signals.append(
            {
                "source": "security_review",
                "priority": "high",
                "signal": "Remote root access should be validated.",
            }
        )

    if "fail2ban" in security_text.lower():
        signals.append(
            {
                "source": "security_review",
                "priority": "medium",
                "signal": "Host brute-force protection status needs review.",
            }
        )

    if not signals:
        signals.append(
            {
                "source": "combined",
                "priority": "medium",
                "signal": "No single dominant issue detected; use the reports to build a staged plan.",
            }
        )

    return signals


def build_remediation_context(
    health_report: AgentReport,
    security_report: AgentReport,
    allowed_actions: list[str],
) -> tuple[RemediationSnapshot, dict]:
    """Build one combined context for the remediation advisor agent."""
    low_risk_actions = build_safe_action_catalog(allowed_actions)
    priority_signals = build_priority_signals(health_report, security_report)

    details = {
        "health_report": health_report.to_dict(),
        "security_report": security_report.to_dict(),
        "known_command_or_permission_issues": {
            "system_health": _message_has_error(health_report.message),
            "security_review": _message_has_error(security_report.message),
        },
        "available_low_risk_actions": low_risk_actions,
        "priority_signals": priority_signals,
    }

    snapshot = RemediationSnapshot(
        priority_signals=priority_signals,
        low_risk_actions=low_risk_actions,
    )

    return snapshot, details
