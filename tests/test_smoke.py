"""Smoke tests — verify core modules import and basic structures work.

These tests never call the OpenAI API; they exercise configuration loading,
dataclass contracts, and tool-level command wrappers so regressions are
caught before an expensive LLM round-trip.
"""

from __future__ import annotations

import json
import os
import unittest


class TestConfig(unittest.TestCase):
    """Ensure config loads and produces sensible defaults."""

    def test_load_config_returns_dataclass(self) -> None:
        os.environ.setdefault("OPENAI_API_KEY", "test-key")
        from config import AppConfig, load_config

        cfg = load_config()
        self.assertIsInstance(cfg, AppConfig)
        self.assertIsInstance(cfg.monitored_services, list)
        self.assertGreater(len(cfg.monitored_services), 0)

    def test_default_timeout_is_positive(self) -> None:
        os.environ.setdefault("OPENAI_API_KEY", "test-key")
        from config import load_config

        cfg = load_config()
        self.assertGreater(cfg.command_timeout_seconds, 0)


class TestCommandUtils(unittest.TestCase):
    """Verify the low-level command runner."""

    def test_run_command_echo(self) -> None:
        from tools.command_utils import CommandResult, run_command

        result = run_command(["echo", "hello"])
        self.assertIsInstance(result, CommandResult)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hello", result.stdout)

    def test_run_command_missing_binary(self) -> None:
        from tools.command_utils import run_command

        result = run_command(["__nonexistent_binary_xyz__"])
        self.assertEqual(result.exit_code, 127)

    def test_to_dict_returns_dict(self) -> None:
        from tools.command_utils import run_command

        result = run_command(["echo", "test"])
        d = result.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("stdout", d)
        self.assertIn("exit_code", d)


class TestAgentReport(unittest.TestCase):
    """Verify the typed report dataclass."""

    def test_to_dict_roundtrip(self) -> None:
        from agents.report import AgentReport

        report = AgentReport(
            role="test",
            snapshot={"disk": "ok"},
            details={"uptime": "1h"},
            message="All clear.",
        )
        d = report.to_dict()
        self.assertEqual(d["role"], "test")
        self.assertEqual(d["message"], "All clear.")
        json_str = json.dumps(d)
        self.assertIn("test", json_str)


class TestRemediationTools(unittest.TestCase):
    """Verify remediation context building."""

    def test_build_remediation_context(self) -> None:
        from agents.report import AgentReport
        from tools.remediation.remediation_tools import build_remediation_context

        health_report = AgentReport(
            role="system_health",
            snapshot={"disk": {"stdout": "85%"}},
            details={"services": {"nginx": {"allowed": True}}},
            message="Disk usage is 85% and nginx is inactive.",
        )
        security_report = AgentReport(
            role="security_review",
            snapshot={"open_ports": {"stdout": "22 80 443"}},
            details={"fail2ban_status": {"client": {"stderr": "Command not found"}}},
            message="Remote root login should be validated and fail2ban is missing.",
        )

        snapshot, details = build_remediation_context(
            health_report=health_report,
            security_report=security_report,
            allowed_actions=["check_disk", "check_firewall", "read_nginx_logs"],
        )

        snapshot_dict = snapshot.to_dict()
        self.assertIn("priority_signals", snapshot_dict)
        self.assertIn("low_risk_actions", snapshot_dict)
        self.assertIn("check_disk", details["available_low_risk_actions"])


class TestRemediationAgent(unittest.TestCase):
    """Verify the remediation advisor agent without calling OpenAI."""

    def test_run_returns_agent_report(self) -> None:
        from agents.remediation_advisor_agent import RemediationAdvisorAgent
        from agents.report import AgentReport

        class FakeLLMClient:
            def ask(self, system_prompt: str, user_prompt: str) -> str:
                return "Immediate actions:\n- Check disk\n- Verify root access"

        agent = RemediationAdvisorAgent(FakeLLMClient())
        health_report = AgentReport(
            role="system_health",
            snapshot={"disk": {"stdout": "85%"}},
            details={},
            message="Disk usage is 85%.",
        )
        security_report = AgentReport(
            role="security_review",
            snapshot={"sessions": {"stdout": "root pts/0"}},
            details={},
            message="Remote root login should be validated.",
        )

        report = agent.run(
            health_report=health_report,
            security_report=security_report,
            allowed_actions=["check_disk", "check_firewall"],
        )
        self.assertEqual(report.role, "remediation_advisor")
        self.assertIn("priority_signals", report.snapshot)
        self.assertIn("check_firewall", report.details["available_low_risk_actions"])


class TestActionModels(unittest.TestCase):
    """Verify ActionExecutionResult shape."""

    def test_fields_exist(self) -> None:
        from tools.action_models import ActionExecutionResult

        result = ActionExecutionResult(
            action_name="check_disk",
            executed=True,
            details={"stdout": "/dev/sda1"},
        )
        self.assertTrue(result.executed)
        self.assertEqual(result.action_name, "check_disk")


class TestHealthTools(unittest.TestCase):
    """Run a couple of real (read-only) system commands."""

    def test_get_uptime_returns_string(self) -> None:
        from tools.system_health.system_health_tools import get_uptime

        uptime = get_uptime()
        self.assertIsInstance(uptime, str)
        self.assertGreater(len(uptime), 0)

    def test_get_disk_usage_has_keys(self) -> None:
        from tools.system_health.system_health_tools import get_disk_usage

        data = get_disk_usage()
        self.assertIn("stdout", data)
        self.assertIn("exit_code", data)
        self.assertIn("root_filesystem_line", data)

    def test_get_nginx_logs_has_keys(self) -> None:
        from tools.system_health.system_health_tools import get_nginx_logs

        data = get_nginx_logs(5)
        self.assertIn("stdout", data)
        self.assertIn("stderr", data)
        self.assertIn("exit_code", data)

    def test_collect_all_health_data_includes_new_sections(self) -> None:
        from tools.system_health.system_health_tools import collect_all_health_data

        snapshot, details = collect_all_health_data(
            allowed_services=["nginx", "docker", "ssh"],
            log_line_count=5,
        )
        snapshot_dict = snapshot.to_dict()
        self.assertIn("docker_health", snapshot_dict)
        self.assertIn("failed_services", snapshot_dict)
        self.assertIn("network_health", snapshot_dict)
        self.assertIn("kernel_errors", snapshot_dict)
        self.assertIn("log_rotation_health", snapshot_dict)
        self.assertIn("disk_io", snapshot_dict)
        self.assertIn("nginx", details)


class TestHealthActions(unittest.TestCase):
    """Verify system health action registration."""

    def test_allowlist_includes_new_actions(self) -> None:
        from tools.system_health.system_health_allowlisted_actions import (
            SystemHealthActionExecutor,
        )

        executor = SystemHealthActionExecutor(allowed_services=["nginx", "docker", "ssh"])
        actions = executor.describe_allowed_actions()
        self.assertIn("check_docker_health", actions)
        self.assertIn("check_failed_services", actions)
        self.assertIn("check_network_health", actions)
        self.assertIn("read_kernel_errors", actions)
        self.assertIn("check_log_rotation_health", actions)
        self.assertIn("check_disk_io", actions)


class TestSecurityTools(unittest.TestCase):
    """Run a couple of real (read-only) security commands."""

    def test_get_open_ports_has_keys(self) -> None:
        from tools.security.security_tools import get_open_ports

        data = get_open_ports()
        self.assertIn("stdout", data)
        self.assertIn("exit_code", data)

    def test_collect_all_security_data_includes_new_sections(self) -> None:
        from tools.security.security_tools import collect_all_security_data

        snapshot, details = collect_all_security_data(
            log_line_count=5,
            login_history_count=5,
        )
        snapshot_dict = snapshot.to_dict()
        self.assertIn("sudo_activity", snapshot_dict)
        self.assertIn("ssh_config_audit", snapshot_dict)
        self.assertIn("cron_security", snapshot_dict)
        self.assertIn("world_writable_files", snapshot_dict)
        self.assertIn("user_account_audit", snapshot_dict)
        self.assertIn("fail2ban_status", snapshot_dict)
        self.assertIn("docker_security", snapshot_dict)
        self.assertIn("docker_security", details)


class TestSecurityActions(unittest.TestCase):
    """Verify security action registration."""

    def test_allowlist_includes_new_actions(self) -> None:
        from tools.security.security_allowlisted_actions import SecurityActionExecutor

        executor = SecurityActionExecutor()
        actions = executor.describe_allowed_actions()
        self.assertIn("read_sudo_activity", actions)
        self.assertIn("read_ssh_config_audit", actions)
        self.assertIn("check_cron_security", actions)
        self.assertIn("check_world_writable_files", actions)
        self.assertIn("check_user_account_audit", actions)
        self.assertIn("check_fail2ban_status", actions)
        self.assertIn("check_docker_security", actions)


if __name__ == "__main__":
    unittest.main()
