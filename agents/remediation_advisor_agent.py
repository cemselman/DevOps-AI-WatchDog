"""Define the remediation advisor agent and its planning prompt."""

from __future__ import annotations

import json

from agents.report import AgentReport
from llm_client import LLMClient
from tools.remediation.remediation_tools import build_remediation_context


REMEDIATION_SYSTEM_PROMPT = """
You are RemediationAdvisorAgent, the operations planning specialist in a Linux
automation project.

Your job is to read the health and security reports, then produce one clear and
prioritized remediation plan for the operator.

Rules:
- Stay practical and conservative.
- Prefer low-risk diagnostic actions before disruptive changes.
- Separate immediate actions from maintenance-window actions.
- Highlight manual approval points clearly.
- Do not invent command outputs or host facts.
""".strip()


def build_remediation_prompt(snapshot_json: str, details: dict) -> str:
    """Build the user prompt for remediation planning."""
    return f"""
The following JSON data combines the outputs of the system health and security
review agents.

Write a practical remediation plan for the operator.

Return plain text with these sections:
1. Overall remediation strategy
2. Immediate actions
3. Maintenance-window actions
4. Low-risk verification steps
5. Items requiring manual approval

Snapshot:
{snapshot_json}

Extra details:
{json.dumps(details, indent=2)}
""".strip()


class RemediationAdvisorAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        """Store the shared LLM client used by the remediation advisor."""
        self.llm_client = llm_client

    def run(
        self,
        health_report: AgentReport,
        security_report: AgentReport,
        allowed_actions: list[str],
    ) -> AgentReport:
        """Build one remediation plan from the other two agent reports."""
        snapshot, details = build_remediation_context(
            health_report=health_report,
            security_report=security_report,
            allowed_actions=allowed_actions,
        )
        prompt = build_remediation_prompt(
            snapshot_json=json.dumps(snapshot.to_dict(), indent=2),
            details=details,
        )
        response_text = self.llm_client.ask(REMEDIATION_SYSTEM_PROMPT, prompt)
        return AgentReport(
            role="remediation_advisor",
            snapshot=snapshot.to_dict(),
            details=details,
            message=response_text,
        )
