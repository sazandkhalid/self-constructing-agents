"""
ComplianceShield: lightweight pre-persist verification for payment skills.

Runs AFTER the existing ast.parse + subprocess test verification,
BEFORE writing the skill to disk.

Returns one of three outcomes:
  PASS  — skill is clean, persist normally
  WARN  — skill touches sensitive data but has audit hooks; persist with flag
  BLOCK — skill hardcodes credentials or PII; reject, do not persist

This is intentionally minimal for the two-week MVP. It is a static analysis
pass only — no execution, no LLM calls.
"""

import re
import ast
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ShieldOutcome(Enum):
    PASS  = "pass"
    WARN  = "warn"
    BLOCK = "block"


@dataclass
class ShieldResult:
    outcome: ShieldOutcome
    reason: str
    detail: Optional[str] = None


# Patterns that indicate hardcoded credentials or real PII
_BLOCK_PATTERNS = [
    (re.compile(r'(?<!\d)\d{9}(?!\d)'),               "potential hardcoded routing number"),
    (re.compile(r'\bIBAN\s*=\s*["\'][A-Z]{2}\d+'),    "hardcoded IBAN literal"),
    (re.compile(r'password\s*=\s*["\'].+["\']', re.I), "hardcoded password"),
    (re.compile(r'api_key\s*=\s*["\'].+["\']', re.I),  "hardcoded API key"),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),             "SSN-pattern literal"),
]

# Patterns indicating the skill touches PII/financial data
_AUDIT_INDICATORS = [
    "account_number", "iban", "routing_number", "amount",
    "debtor", "creditor", "beneficiary", "remittance",
    "parse_pacs", "parse_camt", "parse_pain", "extract_statement",
]

# Patterns that satisfy the audit requirement
_AUDIT_HOOK_PATTERNS = [
    "audit_trail", "log_access", "compliance_log",
    "audit_required", "logging.info", "logger.info",
    "logging.warning", "logger.warning",
]


def check(skill_code: str, metadata: dict) -> ShieldResult:
    """
    Run ComplianceShield on a skill before persisting.

    Args:
        skill_code: full Python source of the skill
        metadata: dict of parsed header fields (protocol, rail, audit_required, etc.)

    Returns:
        ShieldResult with outcome PASS, WARN, or BLOCK
    """
    # 1. Syntax check (defensive — should already be done upstream)
    try:
        ast.parse(skill_code)
    except SyntaxError as e:
        return ShieldResult(ShieldOutcome.BLOCK, "syntax error", str(e))

    code_lower = skill_code.lower()

    # 2. Block on hardcoded credentials or real PII patterns
    for pattern, label in _BLOCK_PATTERNS:
        if pattern.search(skill_code):
            return ShieldResult(
                ShieldOutcome.BLOCK,
                f"hardcoded sensitive value detected: {label}",
                "remove literal values and use parameters or environment variables",
            )

    # 3. Check if skill touches PII/financial data
    touches_sensitive = any(ind in code_lower for ind in _AUDIT_INDICATORS)
    audit_required = metadata.get("audit_required") in (True, "true", "True")

    if touches_sensitive or audit_required:
        has_hook = any(hook in code_lower for hook in _AUDIT_HOOK_PATTERNS)
        if not has_hook:
            return ShieldResult(
                ShieldOutcome.WARN,
                "skill accesses financial/PII data without an audit hook",
                "consider adding a logging.info() call noting access; skill will persist with warn flag",
            )

    return ShieldResult(ShieldOutcome.PASS, "no issues detected")


if __name__ == "__main__":
    # Clean skill — should PASS
    clean = """
def add(a, b):
    return a + b

if __name__ == "__main__":
    assert add(1, 2) == 3
    print("TEST PASSED")
"""
    r = check(clean, {})
    assert r.outcome == ShieldOutcome.PASS, r

    # Hardcoded routing number — should BLOCK
    blocked = """
def get_routing():
    return "021000021"
"""
    r = check(blocked, {})
    assert r.outcome == ShieldOutcome.BLOCK, r

    # Touches financial data, no audit hook — should WARN
    warned = """
def process(account_number, amount):
    return amount * 2
"""
    r = check(warned, {})
    assert r.outcome == ShieldOutcome.WARN, r

    # Touches financial data WITH audit hook — should PASS
    audited = """
import logging
def process(account_number, amount):
    logging.info("accessing account data")
    return amount * 2
"""
    r = check(audited, {})
    assert r.outcome == ShieldOutcome.PASS, r

    print("TEST PASSED")
