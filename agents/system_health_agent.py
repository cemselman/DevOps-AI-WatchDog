"""Define the system health agent and its prompt-building logic."""

from __future__ import annotations

import json

from services.llm_client import LLMClient
from shared.agent_report import AgentReport
from shared.config import AppConfig
from tools.system_health.system_health_tools import collect_all_health_data


AGENT1_SYSTEM_PROMPT = """
You are SystemHealthAgent, the system health analyst in a Linux automation project.
Your job is to inspect server health data and write an operator-friendly report.

Rules:
- Stay concise and operational.
- Focus on capacity, service health, and stability risks.
- Do not invent command outputs.
- If something failed, say so clearly.
""".strip()


def build_health_review_prompt(snapshot_json: str, details: dict) -> str:
    """Build the user prompt used by the system health agent."""
    return f"""
The following JSON data describes the current Linux server health state.
Write a practical health report for the operator.

Return plain text with these sections:
1. Executive summary
2. Healthy signals
3. Risky signals
4. Recommended low-risk actions
5. Items that need manual review

Snapshot:
{snapshot_json}

Extra details:
{json.dumps(details, indent=2)}
""".strip()


class SystemHealthAgent:
    def __init__(self, config: AppConfig, llm_client: LLMClient) -> None:
        """Store shared config and the LLM client."""
        self.config = config
        self.llm_client = llm_client

    def run(self) -> AgentReport:
        """Collect health data once and turn it into one LLM-written report."""
        snapshot, details = collect_all_health_data(
            allowed_services=self.config.monitored_services,
            log_line_count=self.config.health_log_line_count,
        )
        prompt = build_health_review_prompt(
            snapshot_json=snapshot.to_pretty_json(),
            details=details,
        )
        llm_summary = self.llm_client.ask(AGENT1_SYSTEM_PROMPT, prompt)

        return AgentReport(
            role="system_health",
            snapshot=snapshot.to_dict(),
            details=details,
            message=llm_summary,
        )
