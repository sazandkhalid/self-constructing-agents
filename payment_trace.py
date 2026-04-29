"""
Payment trace writer.

Writes structured step-by-step output from the payment simulation
to logs/payment_trace.jsonl so the visualization can read live data.

Each entry in payment_trace.jsonl represents one completed payment step
with the agent's actual output, skills used, tools called, and timing.
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

TRACE_PATH = Path(__file__).parent / "logs" / "payment_trace.jsonl"


@dataclass
class PaymentStep:
    step_number: int           # 1-8
    step_id: str               # e.g. "parse_pain001"
    step_title: str            # human label
    step_subtitle: str         # short description
    message_type: str          # e.g. "pain.001.001.09"
    message_label: str         # e.g. "Customer Credit Transfer Initiation"
    tag: str                   # badge text e.g. "pain.001"
    tag_color: str             # CSS color string
    tag_text: str              # CSS color string
    flow_node: int             # which flow node is active (0-4)
    flow_edge: int             # which flow edge is active (0-4)

    # Agent output
    agent_response: str        # full raw response from the LLM
    message_content: str       # the XML or structured output extracted
    skills_activated: list     # list of skill names used
    skills_saved: list         # list of new skills that were verified and saved
    tools_called: list         # list of MCP tool names called
    tool_results: dict         # tool name -> result dict

    # Transaction state at this step
    tx_status: str
    tx_e2e_id: str
    tx_amount: str
    tx_fx_rate: str
    tx_settlement: str

    # Compliance state at this step
    ofac_screen: str
    aml_check: str
    iban_valid: str
    address_format: str
    sanctions_db: str

    # Log entries
    logs: list                 # list of {time, type, msg} dicts

    # Metadata
    timestamp: str             # ISO UTC
    duration_ms: int           # how long this step took
    skill_verified: bool       # did a new skill pass verification
    task_success: bool         # did the agent succeed at the task


class PaymentTraceWriter:

    def __init__(self):
        TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)

    def reset(self):
        """Clear the trace file for a fresh simulation run."""
        if TRACE_PATH.exists():
            TRACE_PATH.unlink()

    def write_step(self, step: PaymentStep):
        """Append a completed step to the trace file."""
        with open(TRACE_PATH, "a") as f:
            f.write(json.dumps(asdict(step)) + "\n")

    def write_summary(self, summary: dict):
        """Write a final summary entry."""
        summary["_type"] = "summary"
        summary["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(TRACE_PATH, "a") as f:
            f.write(json.dumps(summary) + "\n")


def extract_xml_from_response(response: str) -> str:
    """
    Extract XML content from an agent response.
    Looks for XML between code fences or directly in the response.
    Returns the raw XML string or a formatted version of the response.
    """
    # Try to find XML in code blocks
    code_block = re.search(r'```(?:xml)?\s*\n?(.*?)\n?```', response, re.DOTALL)
    if code_block:
        content = code_block.group(1).strip()
        if content.startswith('<'):
            return content

    # Try to find XML directly
    xml_match = re.search(r'(<Document.*?</Document>)', response, re.DOTALL)
    if xml_match:
        return xml_match.group(1)

    # Return the response formatted as a code-style output
    return response[:2000] if len(response) > 2000 else response


def extract_skills_from_log(log_content: str) -> list:
    """Extract skill names mentioned in log output."""
    skills = []
    pattern = r'skill[_\s]+(?:used|activated|called):\s*([a-z_]+)'
    matches = re.findall(pattern, log_content.lower())
    skills.extend(matches)
    return list(set(skills))


def parse_tool_calls_from_response(response: str) -> tuple:
    """
    Extract tool call names and results from an agent response.
    Returns (tool_names, results_dict).
    """
    tools = []
    results = {}

    # Look for MCP tool call patterns
    tool_pattern = re.search(r'TOOL CALL[:\s]+(\w+)', response)
    if tool_pattern:
        tool_name = tool_pattern.group(1)
        tools.append(tool_name)

    # Look for tool result patterns
    result_pattern = re.search(r'TOOL RESULT \[(\w+)\]:\s*({.*?})', response, re.DOTALL)
    if result_pattern:
        tool_name = result_pattern.group(1)
        try:
            results[tool_name] = json.loads(result_pattern.group(2))
        except Exception:
            results[tool_name] = {"raw": result_pattern.group(2)[:200]}

    return tools, results
