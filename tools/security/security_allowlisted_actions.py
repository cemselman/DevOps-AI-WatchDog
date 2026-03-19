"""Allowlisted low-risk actions for security and access checks.

This module is the execution side of the security tool layer.
It exposes only predefined, read-oriented actions instead of letting the AI
invent arbitrary shell commands.

Examples of allowlisted actions:
- ``check_open_ports``
- ``check_firewall``
- ``read_sudo_activity``
- ``read_ssh_config_audit``
- ``check_cron_security``
- ``check_world_writable_files``
- ``check_user_account_audit``
- ``check_fail2ban_status``
- ``check_docker_security``
- ``read_ssh_logs``
- ``list_recent_logins``

Typical usage:
- build a ``SecurityActionExecutor``
- inspect ``describe_allowed_actions()``
- call ``run("check_open_ports")`` when automation policy allows it
"""

from __future__ import annotations

from tools.action_models import ActionExecutionResult
from tools.security.security_tools import (
    get_active_sessions,
    get_cron_security,
    get_docker_security,
    get_failed_logins,
    get_fail2ban_status,
    get_firewall_status,
    get_open_ports,
    get_recent_logins,
    get_ssh_config_audit,
    get_ssh_logs,
    get_sudo_activity,
    get_user_account_audit,
    get_world_writable_files,
)


class SecurityActionExecutor:
    def __init__(
        self,
        auto_approve_low_risk: bool = False,
        security_log_line_count: int = 30,
        login_history_count: int = 10,
    ) -> None:
        """Register the low-risk actions related to security review."""
        self.auto_approve_low_risk = auto_approve_low_risk
        self.security_log_line_count = security_log_line_count
        self.login_history_count = login_history_count
        self.allowed_actions = {
            "check_open_ports": self._check_open_ports,
            "check_firewall": self._check_firewall,
            "read_sudo_activity": self._read_sudo_activity,
            "read_ssh_config_audit": self._read_ssh_config_audit,
            "check_cron_security": self._check_cron_security,
            "check_world_writable_files": self._check_world_writable_files,
            "check_user_account_audit": self._check_user_account_audit,
            "check_fail2ban_status": self._check_fail2ban_status,
            "check_docker_security": self._check_docker_security,
            "read_ssh_logs": self._read_ssh_logs,
            "list_active_sessions": self._list_active_sessions,
            "list_recent_logins": self._list_recent_logins,
            "list_failed_logins": self._list_failed_logins,
        }

    def describe_allowed_actions(self) -> list[str]:
        """Expose the current allowlist for logs and operator visibility."""
        return sorted(self.allowed_actions.keys())

    def run(self, action_name: str, **kwargs) -> ActionExecutionResult:
        """Execute one security action only when it is explicitly enabled."""
        if action_name not in self.allowed_actions:
            return ActionExecutionResult(
                action_name=action_name,
                executed=False,
                details={
                    "message": "Action rejected. It is not on the security allowlist.",
                    "allowed_actions": self.describe_allowed_actions(),
                },
            )

        if not self.auto_approve_low_risk:
            return ActionExecutionResult(
                action_name=action_name,
                executed=False,
                details={
                    "message": (
                        "Low-risk automation is disabled. This security action is available but not auto-executed."
                    ),
                    "suggested_parameters": kwargs,
                },
            )

        return ActionExecutionResult(
            action_name=action_name,
            executed=True,
            details=self.allowed_actions[action_name](**kwargs),
        )

    def _check_open_ports(self) -> dict:
        """Return current listening ports."""
        return get_open_ports()

    def _check_firewall(self) -> dict:
        """Return firewall status if available."""
        return get_firewall_status()

    def _read_sudo_activity(self) -> dict:
        """Return recent sudo-related logs."""
        return get_sudo_activity(self.security_log_line_count)

    def _read_ssh_config_audit(self) -> dict:
        """Return the effective SSH daemon configuration."""
        return get_ssh_config_audit()

    def _check_cron_security(self) -> dict:
        """Return cron service and configuration details."""
        return get_cron_security()

    def _check_world_writable_files(self) -> dict:
        """Return world-writable files in common high-risk paths."""
        return get_world_writable_files()

    def _check_user_account_audit(self) -> dict:
        """Return basic account and privilege group details."""
        return get_user_account_audit()

    def _check_fail2ban_status(self) -> dict:
        """Return fail2ban status if available."""
        return get_fail2ban_status()

    def _check_docker_security(self) -> dict:
        """Return Docker security details."""
        return get_docker_security()

    def _read_ssh_logs(self) -> dict:
        """Return recent SSH-related logs."""
        return get_ssh_logs(self.security_log_line_count)

    def _list_active_sessions(self) -> dict:
        """Return current active user sessions."""
        return get_active_sessions()

    def _list_recent_logins(self) -> dict:
        """Return recent successful login history."""
        return get_recent_logins(self.login_history_count)

    def _list_failed_logins(self) -> dict:
        """Return recent failed login history."""
        return get_failed_logins(self.login_history_count)
