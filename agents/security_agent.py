"""Define the security review agent and its prompt-building logic."""

from __future__ import annotations

import json

from agents.report import AgentReport
from config import AppConfig
from llm_client import LLMClient
from tools.security.security_tools import collect_all_security_data


AGENT2_SYSTEM_PROMPT = """
You are SecurityReviewAgent, the security and access analyst in a Linux automation project.
You inspect login history, network exposure, SSH activity, and firewall posture.

Rules:
- Be practical and conservative.
- Use only low, medium, or high as the risk level.
- Suggest safe read-only checks before disruptive actions.
- Highlight uncertainty when permissions limit visibility.
""".strip()


def build_security_review_prompt(snapshot_json: str, details: dict) -> str:
    """Build the user prompt used by the security review agent."""
    return f"""
The following JSON data describes the current Linux security and access state.
Write a practical security report for the operator.

Return plain text with these sections:
1. Security summary
2. Risk level
3. Notable findings
4. Recommended low-risk actions
5. Items that need manual review

Snapshot:
{snapshot_json}

Extra details:
{json.dumps(details, indent=2)}
""".strip()


class SecurityReviewAgent:
    def __init__(self, config: AppConfig, llm_client: LLMClient) -> None:
        """Store shared config and the LLM client."""
        self.config = config
        self.llm_client = llm_client

    def run(self) -> AgentReport:
        """Collect security data once and summarize it independently."""
        snapshot, details = collect_all_security_data(
            log_line_count=self.config.security_log_line_count,
            login_history_count=self.config.login_history_count,
        )
        prompt = build_security_review_prompt(
            snapshot_json=snapshot.to_pretty_json(),
            details=details,
        )
        response_text = self.llm_client.ask(AGENT2_SYSTEM_PROMPT, prompt)
        return AgentReport(
            role="security_review",
            snapshot=snapshot.to_dict(),
            details=details,
            message=response_text,
        )
