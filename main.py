"""Run both agents, print results, and save Markdown/JSON reports."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from agents.report import AgentReport
from agents.remediation_advisor_agent import RemediationAdvisorAgent
from agents.security_agent import SecurityReviewAgent
from agents.system_health_agent import SystemHealthAgent
from services.llm_client import LLMClient
from shared.config import load_config
from tools.command_utils import configure_timeout
from tools.security.security_allowlisted_actions import SecurityActionExecutor
from tools.system_health.system_health_allowlisted_actions import (
    SystemHealthActionExecutor,
)

log = logging.getLogger("watchdog")

REPORTS_DIR = Path("reports")
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"


def print_banner(title: str) -> None:
    """Render a visible terminal banner for the current stage."""
    print(f"{BOLD}{CYAN}=== {title} ==={RESET}")


def print_section(title: str) -> None:
    """Render a smaller terminal section heading."""
    print(f"{BOLD}{YELLOW}{title}{RESET}")


def build_json_report(
    health_report: AgentReport,
    security_report: AgentReport,
    remediation_report: AgentReport,
    allowed_actions: list[str],
) -> dict:
    """Create a structured JSON version of the combined report."""
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "project": "DevOps Watchdog",
        "agents": {
            "system_health": {
                "name": "SystemHealthAgent",
                "role": health_report.role,
                "report": health_report.to_dict(),
            },
            "security_review": {
                "name": "SecurityReviewAgent",
                "role": security_report.role,
                "report": security_report.to_dict(),
            },
            "remediation_advisor": {
                "name": "RemediationAdvisorAgent",
                "role": remediation_report.role,
                "report": remediation_report.to_dict(),
            },
        },
        "safe_actions": allowed_actions,
    }


def build_combined_report(
    health_report: AgentReport,
    security_report: AgentReport,
    remediation_report: AgentReport,
) -> str:
    """Combine both independent agent outputs into one markdown report."""
    return "\n".join(
        [
            "# DevOps Watchdog Report",
            "",
            "## System Health",
            health_report.message,
            "",
            "## Security Review",
            security_report.message,
            "",
            "## Remediation Advisor",
            remediation_report.message,
            "",
            "## Operator Note",
            (
                "The first two agents ran independently. SystemHealthAgent "
                "focused on capacity and service stability, "
                "SecurityReviewAgent focused on access and security signals, "
                "and RemediationAdvisorAgent turned both outputs into one "
                "prioritized operator plan."
            ),
        ]
    )


def save_report(final_text: str, timestamp: str) -> Path:
    """Persist the final markdown report under reports/."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"watchdog_report_{timestamp}.md"
    report_path.write_text(final_text + "\n", encoding="utf-8")
    return report_path


def save_json_report(report_data: dict, timestamp: str) -> Path:
    """Persist the structured JSON report under reports/."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"watchdog_report_{timestamp}.json"
    report_path.write_text(
        json.dumps(report_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report_path


def main() -> None:
    """Boot the app, run both independent agents, and save the final report."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    config = load_config()
    configure_timeout(config.command_timeout_seconds)

    try:
        llm_client = LLMClient(
            api_key=config.openai_api_key,
            model=config.openai_model,
        )
    except ValueError as exc:
        log.error("%s — update .env and re-run.", exc)
        return

    health_agent = SystemHealthAgent(config, llm_client)
    security_agent = SecurityReviewAgent(config, llm_client)
    remediation_agent = RemediationAdvisorAgent(llm_client)

    # Executors are not called for automation in this version.  They are
    # instantiated here so the operator can see which low-risk actions the
    # system *would* support once AUTO_APPROVE_LOW_RISK is enabled.
    system_health_executor = SystemHealthActionExecutor(
        allowed_services=config.monitored_services,
        auto_approve_low_risk=config.auto_approve_low_risk,
        health_log_line_count=config.health_log_line_count,
    )
    security_executor = SecurityActionExecutor(
        auto_approve_low_risk=config.auto_approve_low_risk,
        security_log_line_count=config.security_log_line_count,
        login_history_count=config.login_history_count,
    )
    allowed_actions = sorted(
        system_health_executor.describe_allowed_actions()
        + security_executor.describe_allowed_actions()
    )

    print_banner("DevOps Watchdog")
    log.info("Model: %s", config.openai_model)
    log.info("Allowed safe actions: %s", ", ".join(allowed_actions))

    print_section("Step 1: SystemHealthAgent runs the system health review")
    health_report = health_agent.run()
    log.info("SystemHealthAgent finished.")
    print(health_report.message)
    print()

    print_section("Step 2: SecurityReviewAgent runs the security review")
    security_report = security_agent.run()
    log.info("SecurityReviewAgent finished.")
    print(security_report.message)
    print()

    print_section("Step 3: RemediationAdvisorAgent builds the action plan")
    remediation_report = remediation_agent.run(
        health_report=health_report,
        security_report=security_report,
        allowed_actions=allowed_actions,
    )
    log.info("RemediationAdvisorAgent finished.")
    print(remediation_report.message)
    print()

    combined_report = build_combined_report(
        health_report,
        security_report,
        remediation_report,
    )
    json_report = build_json_report(
        health_report=health_report,
        security_report=security_report,
        remediation_report=remediation_report,
        allowed_actions=allowed_actions,
    )
    report_timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    markdown_report_path = save_report(combined_report, timestamp=report_timestamp)
    json_report_path = save_json_report(json_report, timestamp=report_timestamp)

    print_section("Final step: Reports created")
    log.info("Markdown report -> %s", markdown_report_path)
    log.info("JSON report     -> %s", json_report_path)


if __name__ == "__main__":
    main()
