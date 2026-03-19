"""Allowlisted low-risk actions for system health operations.

This module is the execution side of the health tool layer.
It does not decide *what* to run from free-form AI text; instead it exposes a
fixed allowlist of safe actions such as:
- ``check_disk``
- ``check_disk_io``
- ``check_memory``
- ``check_failed_services``
- ``check_docker_health``
- ``check_network_health``
- ``read_kernel_errors``
- ``check_log_rotation_health``
- ``read_nginx_logs``
- ``read_system_logs``
- ``status_service``

Typical usage:
- build a ``SystemHealthActionExecutor``
- call ``describe_allowed_actions()`` to show what is safe
- call ``run("check_disk")`` only when low-risk automation is enabled
"""

from __future__ import annotations

from tools.action_models import ActionExecutionResult
from tools.system_health.system_health_tools import (
    get_disk_usage,
    get_disk_io,
    get_docker_health,
    get_failed_services,
    get_kernel_errors,
    get_log_rotation_health,
    get_memory_usage,
    get_network_health,
    get_nginx_logs,
    get_recent_logs,
    get_root_directory_sizes,
    get_service_status,
    get_uptime,
    get_var_log_sizes,
)


class SystemHealthActionExecutor:
    def __init__(
        self,
        allowed_services: list[str],
        auto_approve_low_risk: bool = False,
        health_log_line_count: int = 20,
    ) -> None:
        """Register the low-risk actions related to system health."""
        self.allowed_services = allowed_services
        self.auto_approve_low_risk = auto_approve_low_risk
        self.health_log_line_count = health_log_line_count
        self.allowed_actions = {
            "check_disk": self._check_disk,
            "check_disk_io": self._check_disk_io,
            "check_memory": self._check_memory,
            "check_uptime": self._check_uptime,
            "check_failed_services": self._check_failed_services,
            "check_docker_health": self._check_docker_health,
            "check_network_health": self._check_network_health,
            "read_kernel_errors": self._read_kernel_errors,
            "check_log_rotation_health": self._check_log_rotation_health,
            "read_nginx_logs": self._read_nginx_logs,
            "read_system_logs": self._read_system_logs,
            "inspect_var_log_sizes": self._inspect_var_log_sizes,
            "inspect_root_sizes": self._inspect_root_sizes,
            "status_service": self._status_service,
        }

    def describe_allowed_actions(self) -> list[str]:
        """Expose the current allowlist for logs and operator visibility."""
        return sorted(self.allowed_actions.keys())

    def run(self, action_name: str, **kwargs) -> ActionExecutionResult:
        """Execute one health action only when it is explicitly enabled."""
        if action_name not in self.allowed_actions:
            return ActionExecutionResult(
                action_name=action_name,
                executed=False,
                details={
                    "message": "Action rejected. It is not on the health allowlist.",
                    "allowed_actions": self.describe_allowed_actions(),
                },
            )

        if not self.auto_approve_low_risk:
            return ActionExecutionResult(
                action_name=action_name,
                executed=False,
                details={
                    "message": (
                        "Low-risk automation is disabled. This health action is available but not auto-executed."
                    ),
                    "suggested_parameters": kwargs,
                },
            )

        return ActionExecutionResult(
            action_name=action_name,
            executed=True,
            details=self.allowed_actions[action_name](**kwargs),
        )

    def _check_disk(self) -> dict:
        """Return disk usage details."""
        return get_disk_usage()

    def _check_disk_io(self) -> dict:
        """Return disk I/O details."""
        return get_disk_io()

    def _check_memory(self) -> dict:
        """Return memory usage details."""
        return get_memory_usage()

    def _check_uptime(self) -> dict:
        """Return uptime details."""
        return {"uptime": get_uptime()}

    def _check_failed_services(self) -> dict:
        """Return the list of failed systemd services."""
        return get_failed_services()

    def _check_docker_health(self) -> dict:
        """Return Docker container and stats details."""
        return get_docker_health()

    def _check_network_health(self) -> dict:
        """Return network interface and route details."""
        return get_network_health()

    def _read_kernel_errors(self) -> dict:
        """Return recent kernel error logs."""
        return get_kernel_errors(self.health_log_line_count)

    def _check_log_rotation_health(self) -> dict:
        """Return logrotate service and timer status."""
        return get_log_rotation_health()

    def _read_system_logs(self) -> dict:
        """Return recent journal entries."""
        return get_recent_logs(self.health_log_line_count)

    def _read_nginx_logs(self) -> dict:
        """Return recent nginx-related logs."""
        return get_nginx_logs(self.health_log_line_count)

    def _inspect_var_log_sizes(self) -> dict:
        """Return size distribution inside /var/log."""
        return get_var_log_sizes()

    def _inspect_root_sizes(self) -> dict:
        """Return size distribution at the root directory."""
        return get_root_directory_sizes()

    def _status_service(self, service_name: str) -> dict:
        """Return one allowed service status."""
        return get_service_status(service_name, self.allowed_services)
