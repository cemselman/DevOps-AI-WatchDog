"""Read-only Linux health data collectors used by SystemHealthAgent.

This module contains functions for operational health checks such as:
- disk usage
- disk I/O
- memory usage
- uptime
- service status
- failed services
- docker health
- network health
- kernel errors
- log rotation health
- nginx service logs
- recent system logs
- directory size summaries

Typical examples:
- ``get_disk_usage()`` to inspect root filesystem usage
- ``get_service_status("docker", ["nginx", "docker", "ssh"])``
- ``collect_all_health_data(...)`` to assemble one structured report input
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from tools.command_utils import run_command


@dataclass(slots=True)
class SystemSnapshot:
    # Sent to the LLM as machine-readable context by SystemHealthAgent.
    disk: dict
    disk_io: dict
    memory: dict
    uptime: str
    services: dict[str, dict]
    failed_services: dict
    docker_health: dict
    network_health: dict
    kernel_errors: dict
    log_rotation_health: dict
    nginx: dict
    recent_logs: dict

    def to_dict(self) -> dict:
        """Convert the snapshot dataclass to a plain dictionary."""
        return asdict(self)

    def to_pretty_json(self) -> str:
        """Format the snapshot for LLM prompts and debug output."""
        return json.dumps(self.to_dict(), indent=2)


def get_disk_usage() -> dict:
    """Read root filesystem usage."""
    result = run_command(["df", "-h", "/"])
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    usage_line = lines[1] if len(lines) > 1 else ""

    data = result.to_dict()
    data["root_filesystem_line"] = usage_line
    return data


def get_inode_usage() -> dict:
    """Read inode usage for the root filesystem."""
    return run_command(["df", "-i", "/"]).to_dict()


def get_memory_usage() -> dict:
    """Read memory statistics in megabytes."""
    return run_command(["free", "-m"]).to_dict()


def get_disk_io() -> dict:
    """Read disk I/O statistics when iostat is available."""
    return run_command(["iostat", "-xz", "1", "1"]).to_dict()


def get_uptime() -> str:
    """Read uptime and load average."""
    result = run_command(["uptime"])
    return result.stdout or result.stderr


def get_service_status(service_name: str, allowed_services: list[str]) -> dict:
    """Read one service status only if it is explicitly allowed."""
    if service_name not in allowed_services:
        return {
            "service": service_name,
            "allowed": False,
            "message": "Service is not on the safe allowlist.",
        }

    data = run_command(["systemctl", "status", service_name, "--no-pager"]).to_dict()
    data["service"] = service_name
    data["allowed"] = True
    return data


def get_recent_logs(line_count: int) -> dict:
    """Read a limited slice of the system journal."""
    return run_command(
        ["journalctl", "-n", str(line_count), "--no-pager", "--output", "short"]
    ).to_dict()


def get_kernel_errors(line_count: int) -> dict:
    """Read recent kernel error entries from the journal."""
    return run_command(
        ["journalctl", "-k", "-p", "err", "-n", str(line_count), "--no-pager"]
    ).to_dict()


def get_nginx_logs(line_count: int) -> dict:
    """Read recent nginx service logs from systemd journal."""
    return run_command(
        ["journalctl", "-u", "nginx.service", "-n", str(line_count), "--no-pager"]
    ).to_dict()


def get_failed_services() -> dict:
    """Read the current list of failed systemd services."""
    return run_command(["systemctl", "--failed", "--no-pager", "--no-legend"]).to_dict()


def get_docker_health() -> dict:
    """Read a compact view of Docker containers and point-in-time stats."""
    return {
        "containers": run_command(
            [
                "docker",
                "ps",
                "--format",
                "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}\t{{.Image}}",
            ]
        ).to_dict(),
        "stats": run_command(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}",
            ]
        ).to_dict(),
    }


def get_network_health() -> dict:
    """Read interface and route information for quick network diagnostics."""
    return {
        "interfaces": run_command(["ip", "-brief", "address"]).to_dict(),
        "routes": run_command(["ip", "route"]).to_dict(),
    }


def get_log_rotation_health() -> dict:
    """Read logrotate service and timer status from systemd."""
    return {
        "service": run_command(
            ["systemctl", "status", "logrotate.service", "--no-pager"]
        ).to_dict(),
        "timer": run_command(
            ["systemctl", "status", "logrotate.timer", "--no-pager"]
        ).to_dict(),
    }


def get_var_log_sizes() -> dict:
    """Inspect the main size distribution under /var/log."""
    return run_command(["du", "-xh", "--max-depth=1", "/var/log"]).to_dict()


def get_root_directory_sizes() -> dict:
    """Inspect top-level size distribution under /."""
    return run_command(["du", "-xh", "--max-depth=1", "/"]).to_dict()


def get_swap_usage() -> dict:
    """Combine swap and memory outputs for one health snapshot."""
    return {
        "free": run_command(["free", "-m"]).to_dict(),
        "swapon": run_command(["swapon", "--show"]).to_dict(),
    }


def collect_all_health_data(
    allowed_services: list[str],
    log_line_count: int,
) -> tuple[SystemSnapshot, dict]:
    """Collect health data once and return both the snapshot and full details.

    Every command runs exactly once; both the compact snapshot and the
    extended details dict are derived from the same collected data.
    """
    disk = get_disk_usage()
    disk_io = get_disk_io()
    memory = get_memory_usage()
    uptime = get_uptime()
    recent_logs = get_recent_logs(log_line_count)
    kernel_errors = get_kernel_errors(log_line_count)
    services = {
        name: get_service_status(name, allowed_services)
        for name in allowed_services
    }
    failed_services = get_failed_services()
    docker_health = get_docker_health()
    network_health = get_network_health()
    log_rotation_health = get_log_rotation_health()
    nginx = {
        "service_status": services.get(
            "nginx",
            get_service_status("nginx", allowed_services),
        ),
        "logs": get_nginx_logs(log_line_count),
    }

    snapshot = SystemSnapshot(
        disk=disk,
        disk_io=disk_io,
        memory=memory,
        uptime=uptime,
        services=services,
        failed_services=failed_services,
        docker_health=docker_health,
        network_health=network_health,
        kernel_errors=kernel_errors,
        log_rotation_health=log_rotation_health,
        nginx=nginx,
        recent_logs=recent_logs,
    )

    details = {
        "disk": disk,
        "disk_io": disk_io,
        "memory": memory,
        "uptime": uptime,
        "swap": get_swap_usage(),
        "inode": get_inode_usage(),
        "root_sizes": get_root_directory_sizes(),
        "var_log_sizes": get_var_log_sizes(),
        "failed_services": failed_services,
        "docker_health": docker_health,
        "network_health": network_health,
        "kernel_errors": kernel_errors,
        "log_rotation_health": log_rotation_health,
        "nginx": nginx,
        "recent_logs": recent_logs,
        "services": services,
    }

    return snapshot, details
