"""Read-only Linux security and access collectors used by SecurityReviewAgent.

This module focuses on signals related to authentication, exposure, and access:
- active sessions
- recent logins
- failed logins
- open ports
- firewall visibility
- SSH journal entries
- sudo activity
- SSH config audit
- cron security
- world-writable file checks
- user account audit
- fail2ban status
- Docker security

Typical examples:
- ``get_active_sessions()`` to see current logged-in users
- ``get_open_ports()`` to inspect listening services
- ``collect_all_security_data(...)`` to create one structured security input
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from tools.command_utils import run_command


@dataclass(slots=True)
class SecuritySnapshot:
    # Sent to the LLM as machine-readable context by SecurityReviewAgent.
    active_sessions: dict
    recent_logins: dict
    failed_logins: dict
    open_ports: dict
    firewall_status: dict
    ssh_logs: dict
    sudo_activity: dict
    ssh_config_audit: dict
    cron_security: dict
    world_writable_files: dict
    user_account_audit: dict
    fail2ban_status: dict
    docker_security: dict

    def to_dict(self) -> dict:
        """Convert the security dataclass to a plain dictionary."""
        return asdict(self)

    def to_pretty_json(self) -> str:
        """Format the security snapshot for LLM prompts and debug output."""
        return json.dumps(self.to_dict(), indent=2)


def get_active_sessions() -> dict:
    """List currently logged-in users."""
    return run_command(["who"]).to_dict()


def get_recent_logins(login_history_count: int) -> dict:
    """Read recent successful login history."""
    return run_command(["last", "-n", str(login_history_count)]).to_dict()


def get_failed_logins(login_history_count: int) -> dict:
    """Read recent failed login history when available."""
    return run_command(["lastb", "-n", str(login_history_count)]).to_dict()


def get_open_ports() -> dict:
    """List listening TCP and UDP ports."""
    return run_command(["ss", "-tuln"]).to_dict()


def get_firewall_status() -> dict:
    """Read UFW status when the command exists on the host."""
    return run_command(["ufw", "status"]).to_dict()


def get_ssh_logs(line_count: int) -> dict:
    """Read recent SSH-related journal entries."""
    return run_command(
        ["journalctl", "-u", "ssh.service", "-n", str(line_count), "--no-pager"]
    ).to_dict()


def get_sudo_activity(line_count: int) -> dict:
    """Read recent sudo-related journal entries."""
    return run_command(
        ["journalctl", "_COMM=sudo", "-n", str(line_count), "--no-pager"]
    ).to_dict()


def get_ssh_config_audit() -> dict:
    """Read effective SSH daemon configuration when available."""
    return run_command(["sshd", "-T"]).to_dict()


def get_cron_security() -> dict:
    """Read cron service status and common cron configuration locations."""
    return {
        "service": run_command(["systemctl", "status", "cron.service", "--no-pager"]).to_dict(),
        "system_crontab": run_command(["sed", "-n", "1,120p", "/etc/crontab"]).to_dict(),
        "cron_d": run_command(["ls", "-la", "/etc/cron.d"]).to_dict(),
    }


def get_world_writable_files() -> dict:
    """Read world-writable files from a few common high-risk paths."""
    return run_command(
        [
            "find",
            "/tmp",
            "/var/tmp",
            "/var/www",
            "/home",
            "-xdev",
            "-type",
            "f",
            "-perm",
            "-0002",
        ]
    ).to_dict()


def get_user_account_audit() -> dict:
    """Read basic account and privilege group information."""
    return {
        "passwd": run_command(["getent", "passwd"]).to_dict(),
        "sudo_group": run_command(["getent", "group", "sudo"]).to_dict(),
        "root_group": run_command(["getent", "group", "root"]).to_dict(),
    }


def get_fail2ban_status() -> dict:
    """Read fail2ban service and client status when installed."""
    return {
        "service": run_command(
            ["systemctl", "status", "fail2ban.service", "--no-pager"]
        ).to_dict(),
        "client": run_command(["fail2ban-client", "status"]).to_dict(),
    }


def get_docker_security() -> dict:
    """Read Docker security-relevant runtime and daemon information."""
    return {
        "containers": run_command(
            [
                "docker",
                "ps",
                "--format",
                "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}",
            ]
        ).to_dict(),
        "security_options": run_command(
            ["docker", "info", "--format", "{{json .SecurityOptions}}"]
        ).to_dict(),
        "daemon_socket": run_command(["ls", "-l", "/var/run/docker.sock"]).to_dict(),
    }


def collect_all_security_data(
    log_line_count: int,
    login_history_count: int,
) -> tuple[SecuritySnapshot, dict]:
    """Collect security data once and return both the snapshot and full details.

    Every command runs exactly once; both the compact snapshot and the
    extended details dict are derived from the same collected data.
    """
    active_sessions = get_active_sessions()
    recent_logins = get_recent_logins(login_history_count)
    failed_logins = get_failed_logins(login_history_count)
    open_ports = get_open_ports()
    firewall_status = get_firewall_status()
    ssh_logs = get_ssh_logs(log_line_count)
    sudo_activity = get_sudo_activity(log_line_count)
    ssh_config_audit = get_ssh_config_audit()
    cron_security = get_cron_security()
    world_writable_files = get_world_writable_files()
    user_account_audit = get_user_account_audit()
    fail2ban_status = get_fail2ban_status()
    docker_security = get_docker_security()

    snapshot = SecuritySnapshot(
        active_sessions=active_sessions,
        recent_logins=recent_logins,
        failed_logins=failed_logins,
        open_ports=open_ports,
        firewall_status=firewall_status,
        ssh_logs=ssh_logs,
        sudo_activity=sudo_activity,
        ssh_config_audit=ssh_config_audit,
        cron_security=cron_security,
        world_writable_files=world_writable_files,
        user_account_audit=user_account_audit,
        fail2ban_status=fail2ban_status,
        docker_security=docker_security,
    )

    details = {
        "active_sessions": active_sessions,
        "recent_logins": recent_logins,
        "failed_logins": failed_logins,
        "open_ports": open_ports,
        "firewall_status": firewall_status,
        "ssh_logs": ssh_logs,
        "sudo_activity": sudo_activity,
        "ssh_config_audit": ssh_config_audit,
        "cron_security": cron_security,
        "world_writable_files": world_writable_files,
        "user_account_audit": user_account_audit,
        "fail2ban_status": fail2ban_status,
        "docker_security": docker_security,
    }

    return snapshot, details
