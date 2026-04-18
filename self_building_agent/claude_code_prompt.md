# Claude Code Build Prompt: PaymentRail — Self-Constructing Financial Protocol Agent

---

## CONTEXT: WHAT ALREADY EXISTS

You are extending an existing, working project called `self-constructing-agents`. The repo is
already cloned and functional. Before writing a single line of code, read the following files
in full so you understand the existing architecture completely:

```
self_building_agent/run.py          # core agent loop (~1300 lines) — read every line
eval/run_experiment.py              # experiment orchestrator
eval/score.py                       # scoring logic
eval/report.py                      # report generator
eval/benchmark_tasks.txt            # existing fastapi benchmark tasks
eval/exploration_tasks.txt          # existing warm-up tasks
skills_py/index.json                # skill manifest
dashboard/index.html                # existing dashboard
```

Do not modify any existing functionality. Every change you make is additive. The existing
fastapi experiment must still run unchanged with `--queue eval/benchmark_tasks.txt
--target-repo eval/target_repo/fastapi`.

---

## WHAT YOU ARE BUILDING

A two-week MVP that proves one hypothesis:

> A self-constructing agent that has accumulated a library of payment protocol skills performs
> measurably better on financial integration tasks than one starting cold.

This is a focused experiment, not a full product. You are adding:

1. A payment protocol skill taxonomy (new subdirectories + metadata fields)
2. A payment-specific target repo (python-iso20022 library)
3. A 15-task cold/warm benchmark (three tiers of increasing difficulty)
4. A 20-task exploration set (builds the skill library before the warm run)
5. A lightweight ComplianceShield verification stage
6. A second experiment harness that runs the payment version of cold/warm

The existing dashboard, scoring, and report logic require only minor extensions — do not
rewrite them.

---

## STEP 1: INSTALL DEPENDENCIES

```bash
cd self_building_agent
source venv/bin/activate   # or activate the existing venv however it is set up

pip install python-iso20022 schwifty faker
```

If `python-iso20022` is not available on PyPI under that name, install `isoxml` and
`prettyprint` instead and note this in a comment. Also confirm `sentence-transformers` and
`groq` are already installed — do not reinstall them, just verify.

---

## STEP 2: CLONE THE TARGET REPO

```bash
mkdir -p eval/target_repo
cd eval/target_repo
git clone --depth=1 https://github.com/ietf-tools/python-iso20022.git
```

If that repo does not exist or clone fails, fall back to:
```bash
git clone --depth=1 https://github.com/fxcoudert/python-iso20022.git
```

If neither works, create a synthetic target repo instead:

```bash
mkdir -p eval/target_repo/iso20022_synthetic
```

Then create the following synthetic files that the agent can index and reference. These must
be real, working Python that exercises the payment domain — not placeholder stubs:

**`eval/target_repo/iso20022_synthetic/messages.py`**
```python
"""
ISO 20022 message type registry.
Covers pacs (payments clearing), camt (cash management), pain (payment initiation).
"""

PACS_008 = "pacs.008.001.08"   # FI to FI customer credit transfer
PACS_009 = "pacs.009.001.08"   # FI to FI financial institution credit transfer
PACS_002 = "pacs.002.001.10"   # FI to FI payment status report
CAMT_053 = "camt.053.001.08"   # bank to customer statement
CAMT_054 = "camt.054.001.08"   # bank to customer debit credit notification
PAIN_001 = "pain.001.001.09"   # customer credit transfer initiation
PAIN_002 = "pain.002.001.10"   # customer payment status report

MESSAGE_FAMILIES = {
    "pacs": "Payments Clearing and Settlement",
    "camt": "Cash Management",
    "pain": "Payment Initiation",
}

def get_family(msg_type: str) -> str:
    prefix = msg_type.split(".")[0]
    return MESSAGE_FAMILIES.get(prefix, "Unknown")

def is_credit_transfer(msg_type: str) -> bool:
    return msg_type in (PACS_008, PACS_009, PAIN_001)

def is_status_report(msg_type: str) -> bool:
    return msg_type in (PACS_002, PAIN_002)
```

**`eval/target_repo/iso20022_synthetic/parser.py`**
```python
"""
Minimal ISO 20022 XML parser.
Extracts structured fields from MX message envelopes.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

NS = {
    "pacs008": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08",
    "camt053": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08",
    "pain001": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09",
}

@dataclass
class CreditTransfer:
    msg_id: str
    end_to_end_id: str
    amount: float
    currency: str
    debtor_name: Optional[str]
    creditor_name: Optional[str]
    creditor_iban: Optional[str]
    remittance_info: Optional[str]

def parse_pacs008(xml_string: str) -> Optional[CreditTransfer]:
    """Parse a pacs.008 FI-to-FI credit transfer message."""
    try:
        root = ET.fromstring(xml_string)
        ns = NS["pacs008"]
        def find(path):
            el = root.find(f".//{{{ns}}}{path}")
            return el.text.strip() if el is not None and el.text else None
        return CreditTransfer(
            msg_id=find("MsgId") or "",
            end_to_end_id=find("EndToEndId") or "",
            amount=float(find("IntrBkSttlmAmt") or 0),
            currency=root.findtext(f".//{{{ns}}}IntrBkSttlmAmt/[@Ccy]") or "USD",
            debtor_name=find("Dbtr/Nm"),
            creditor_name=find("Cdtr/Nm"),
            creditor_iban=find("CdtrAcct/Id/IBAN"),
            remittance_info=find("Ustrd"),
        )
    except ET.ParseError:
        return None

def extract_statement_entries(xml_string: str) -> list[dict]:
    """Extract entries from a camt.053 bank statement."""
    try:
        root = ET.fromstring(xml_string)
        ns = NS["camt053"]
        entries = []
        for ntry in root.findall(f".//{{{ns}}}Ntry"):
            def fv(tag):
                el = ntry.find(f".//{{{ns}}}{tag}")
                return el.text.strip() if el is not None and el.text else None
            entries.append({
                "amount": fv("Amt"),
                "credit_debit": fv("CdtDbtInd"),
                "booking_date": fv("BookgDt/Dt"),
                "end_to_end_id": fv("EndToEndId"),
                "remittance": fv("Ustrd"),
            })
        return entries
    except ET.ParseError:
        return []
```

**`eval/target_repo/iso20022_synthetic/address.py`**
```python
"""
ISO 20022 hybrid address handling.
Mandatory from November 2026: town name + country code must be structured.
"""

from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class HybridAddress:
    """
    ISO 20022 hybrid address format (mandatory post-Nov 2026).
    Town name and country are structured. Up to 2 free-form lines allowed.
    """
    town_name: str
    country: str                      # ISO 3166-1 alpha-2
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    post_code: Optional[str] = None
    street_name: Optional[str] = None
    building_number: Optional[str] = None

    def is_fully_structured(self) -> bool:
        return all([self.street_name, self.building_number, self.post_code])

    def is_hybrid(self) -> bool:
        return bool(self.town_name and self.country and
                    (self.address_line_1 or not self.is_fully_structured()))

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

def parse_unstructured_address(raw: str, country_hint: str = "US") -> HybridAddress:
    """
    Convert a free-text address to hybrid format.
    Extracts town and country at minimum — required for SWIFT compliance post-Nov 2026.
    """
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    town = ""
    post_code = ""
    if lines:
        last = lines[-1]
        country_match = re.search(r'\b([A-Z]{2})\b', last)
        if country_match:
            country_hint = country_match.group(1)
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', last)
        if zip_match:
            post_code = zip_match.group(1)
            town = last[:zip_match.start()].strip().rstrip(",").strip()
    return HybridAddress(
        town_name=town or "Unknown",
        country=country_hint,
        post_code=post_code or None,
        address_line_1=lines[0] if len(lines) > 1 else None,
        address_line_2=lines[1] if len(lines) > 2 else None,
    )

def validate_hybrid_address(addr: HybridAddress) -> list[str]:
    """Returns list of validation errors. Empty = valid."""
    errors = []
    if not addr.town_name or addr.town_name == "Unknown":
        errors.append("town_name is required and must not be 'Unknown'")
    if not addr.country or len(addr.country) != 2:
        errors.append("country must be a valid ISO 3166-1 alpha-2 code")
    if addr.address_line_1 and len(addr.address_line_1) > 70:
        errors.append("address_line_1 must not exceed 70 characters")
    if addr.address_line_2 and len(addr.address_line_2) > 70:
        errors.append("address_line_2 must not exceed 70 characters")
    return errors
```

**`eval/target_repo/iso20022_synthetic/ach.py`**
```python
"""
NACHA ACH file format utilities.
ACH is the primary US domestic batch payment rail.
"""

from dataclasses import dataclass, field
from typing import List
from datetime import date
import random, string

@dataclass
class ACHEntry:
    routing_number: str      # 9 digits
    account_number: str
    amount_cents: int        # in cents
    individual_name: str
    trace_number: str = ""
    transaction_code: int = 22   # 22=checking credit, 27=checking debit

    def __post_init__(self):
        if not self.trace_number:
            self.trace_number = "".join(random.choices(string.digits, k=15))
        if len(self.routing_number) != 9:
            raise ValueError("routing_number must be exactly 9 digits")

@dataclass
class ACHBatch:
    company_name: str
    company_id: str
    entries: List[ACHEntry] = field(default_factory=list)
    sec_code: str = "PPD"   # PPD, CCD, CTX, WEB

    @property
    def total_debit_cents(self) -> int:
        return sum(e.amount_cents for e in self.entries
                   if e.transaction_code in (27, 37, 47))

    @property
    def total_credit_cents(self) -> int:
        return sum(e.amount_cents for e in self.entries
                   if e.transaction_code in (22, 32, 42))

def format_ach_amount(cents: int) -> str:
    """Format cents as NACHA 10-digit zero-padded amount string."""
    return str(cents).zfill(10)

def validate_routing_number(routing: str) -> bool:
    """Validate ABA routing number using checksum algorithm."""
    if not routing.isdigit() or len(routing) != 9:
        return False
    d = [int(c) for c in routing]
    checksum = (3*(d[0]+d[3]+d[6]) + 7*(d[1]+d[4]+d[7]) + (d[2]+d[5]+d[8])) % 10
    return checksum == 0

def build_ach_file(batch: ACHBatch, effective_date: date) -> str:
    """Build a minimal NACHA-formatted ACH file string."""
    lines = []
    lines.append(f"101 {batch.company_id[:9].ljust(9)}{'DEST'.ljust(23)}{date.today().strftime('%y%m%d')}")
    lines.append(f"5220{batch.company_name[:16].ljust(16)}{batch.company_id[:10].ljust(10)}{batch.sec_code}{effective_date.strftime('%y%m%d')}")
    for i, entry in enumerate(batch.entries, 1):
        lines.append(f"6{entry.transaction_code:02d}{entry.routing_number}{entry.account_number[:17].ljust(17)}{format_ach_amount(entry.amount_cents)}{entry.individual_name[:22].ljust(22)}{entry.trace_number[:15]}")
    lines.append(f"8220{len(batch.entries):06d}{batch.total_debit_cents:012d}{batch.total_credit_cents:012d}")
    lines.append(f"9{'':23}{len(batch.entries):06d}")
    return "\n".join(lines)
```

**`eval/target_repo/iso20022_synthetic/reconciliation.py`**
```python
"""
Cross-rail transaction reconciliation utilities.
Matches payments across ISO 20022 MX, ACH, and internal ledger records.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

@dataclass
class LedgerEntry:
    entry_id: str
    amount: Decimal
    currency: str
    counterparty: Optional[str]
    reference: Optional[str]
    rail: str   # "iso20022", "ach", "fedwire", "internal"

@dataclass
class MatchResult:
    status: str     # "matched", "unmatched", "partial", "duplicate"
    entry_a: LedgerEntry
    entry_b: Optional[LedgerEntry]
    confidence: float   # 0.0 to 1.0
    reason: str

def match_by_reference(entries_a: list[LedgerEntry],
                        entries_b: list[LedgerEntry]) -> list[MatchResult]:
    """
    Attempt to reconcile two sets of ledger entries by reference field.
    Returns a MatchResult for every entry in entries_a.
    """
    index_b = {e.reference: e for e in entries_b if e.reference}
    results = []
    for a in entries_a:
        b = index_b.get(a.reference)
        if b is None:
            results.append(MatchResult("unmatched", a, None, 0.0, "no reference match"))
        elif a.amount == b.amount and a.currency == b.currency:
            results.append(MatchResult("matched", a, b, 1.0, "exact reference + amount"))
        elif a.currency == b.currency:
            diff_pct = abs(a.amount - b.amount) / max(a.amount, b.amount)
            results.append(MatchResult(
                "partial", a, b,
                float(1.0 - diff_pct),
                f"reference match, amount differs by {diff_pct:.1%}"
            ))
        else:
            results.append(MatchResult("unmatched", a, b, 0.3, "reference match but currency mismatch"))
    return results

def surface_exceptions(results: list[MatchResult]) -> list[MatchResult]:
    """Return only unmatched and partial results, sorted by confidence ascending."""
    return sorted(
        [r for r in results if r.status != "matched"],
        key=lambda r: r.confidence
    )
```

---

## STEP 3: EXTEND THE SKILL METADATA FORMAT

Open `self_building_agent/run.py`. Find the section that writes skill metadata header
comments when persisting a new verified Python skill (search for `# skill:` or
`skill_header` or wherever the header block is assembled).

Add three new optional metadata fields to the header format:

```python
# protocol: <iso20022|ach|fedwire|sepa|internal|general>
# rail: <swift_mx|fednow|rtp|nacha|sepa_ct|on_chain|general>
# audit_required: <true|false>
```

These fields must be:
- Written when the LLM emits them inside a `---PY SKILL---` block
- Stored in `skills_py/index.json` alongside the existing fields
- Read back and injected into the system prompt skill index (so the agent knows which
  skills are protocol-specific when selecting for a new task)

The LLM will emit these naturally if the system prompt tells it to. Add the following
sentence to the system prompt skill-writing instruction block (find the block that says
something like "emit a ---PY SKILL--- block"):

```
For payment-domain skills, include these header fields:
# protocol: one of iso20022|ach|fedwire|sepa|internal|general
# rail: one of swift_mx|fednow|rtp|nacha|sepa_ct|on_chain|general
# audit_required: true if the skill reads or writes party PII or financial amounts
```

Do not change any other part of the skill writing or verification pipeline.

---

## STEP 4: ADD THE COMPLIANCESHIELD

Create a new file: `self_building_agent/compliance.py`

```python
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
    (re.compile(r'\b\d{9}\b'),                          "potential hardcoded routing number"),
    (re.compile(r'\bIBAN\s*=\s*["\'][A-Z]{2}\d+'),      "hardcoded IBAN literal"),
    (re.compile(r'password\s*=\s*["\'].+["\']', re.I),  "hardcoded password"),
    (re.compile(r'api_key\s*=\s*["\'].+["\']', re.I),   "hardcoded API key"),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),              "SSN-pattern literal"),
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
    # 1. Syntax check (should already be done upstream, but be defensive)
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
                "remove literal values and use parameters or environment variables"
            )

    # 3. Check if skill touches PII/financial data
    touches_sensitive = any(ind in code_lower for ind in _AUDIT_INDICATORS)
    audit_required = metadata.get("audit_required", "false").lower() == "true"

    if touches_sensitive or audit_required:
        # Check whether any audit hook is present
        has_hook = any(hook in code_lower for hook in _AUDIT_HOOK_PATTERNS)
        if not has_hook:
            return ShieldResult(
                ShieldOutcome.WARN,
                "skill accesses financial/PII data without an audit hook",
                "consider adding a logging.info() call noting access; skill will persist with warn flag"
            )

    return ShieldResult(ShieldOutcome.PASS, "no issues detected")
```

Now integrate this into `run.py`. Find the point where a verified skill is about to be
written to disk (after `TEST PASSED` is confirmed). Before the `open(...).write()` call,
add:

```python
from compliance import check as shield_check, ShieldOutcome

shield_result = shield_check(skill_code, skill_metadata)
if shield_result.outcome == ShieldOutcome.BLOCK:
    log_event("skill_blocked", {
        "skill": skill_name,
        "reason": shield_result.reason,
        "detail": shield_result.detail,
    })
    # treat as skill_verify_failed — do not persist
    return  # or continue, depending on surrounding control flow
elif shield_result.outcome == ShieldOutcome.WARN:
    skill_metadata["compliance_warn"] = shield_result.reason
    log_event("skill_compliance_warn", {
        "skill": skill_name,
        "reason": shield_result.reason,
    })
# PASS falls through to normal persist
```

The `log_event` call must write to `logs/log.jsonl` using the same mechanism already in
`run.py` — do not add a new logging path.

---

## STEP 5: CREATE THE BENCHMARK TASK FILE

Create `eval/payment_benchmark_tasks.txt`.

This file must follow the exact same format as the existing `eval/benchmark_tasks.txt`.
Read that file first and match its format precisely.

The fifteen tasks must be real, specific, and grounded in the target repo files you
created in Step 2. Every task must be answerable by reading actual code in
`eval/target_repo/iso20022_synthetic/`. Do not write vague tasks.

```
# TIER 1: STRUCTURAL (5 tasks)
# These test whether the agent can read the target repo and extract correct information.
# A cold agent with no skills should be able to answer these by reading the files.

What function in parser.py is used to extract entries from a camt.053 bank statement? Show its signature and return type.

List all message type constants defined in messages.py. For each one, state the family it belongs to (pacs, camt, or pain) and a one-sentence description of its purpose.

In address.py, what are the two conditions that make a HybridAddress valid according to validate_hybrid_address()? Write a short test that creates both a valid and an invalid HybridAddress and asserts the correct validation output.

In ach.py, what algorithm does validate_routing_number() use? Re-implement it as a standalone function called check_aba_routing(routing: str) -> bool with a docstring and a unit test that passes at least three known valid ABA routing numbers.

In reconciliation.py, what is the difference between a "matched", "partial", and "unmatched" MatchResult? Write a test that exercises all three outcomes using synthetic LedgerEntry objects.

# TIER 2: TRANSLATION (5 tasks)
# These test whether the agent can write new code that bridges between formats.
# A warm agent with parsing skills should outperform a cold agent here.

Write a function convert_pacs008_to_ledger_entry(xml_string: str) -> LedgerEntry that
uses parse_pacs008() from parser.py and returns a LedgerEntry from reconciliation.py.
The rail field should be set to "iso20022". Include a unit test with a minimal but valid
pacs.008 XML string.

Write a function ach_entry_to_ledger_entry(entry: ACHEntry) -> LedgerEntry that converts
an ACH entry from ach.py into a LedgerEntry from reconciliation.py. Map transaction_code
22 or 32 to a credit, 27 or 37 to a debit, represented as positive or negative amounts.
Include a unit test.

Write a function normalize_address(raw: str) -> dict that calls parse_unstructured_address()
from address.py and returns a plain dict with keys town, country, post_code, and lines
(a list of at most 2 strings). If validate_hybrid_address() returns errors, include them
under an "errors" key. Include a unit test with a multi-line US address string.

Write a function reconcile_iso_vs_ach(iso_xml_list: list[str], ach_entries: list[ACHEntry]) -> list[MatchResult]
that parses each ISO 20022 pacs.008 string into a LedgerEntry, converts each ACHEntry
into a LedgerEntry, then calls match_by_reference() from reconciliation.py to produce
MatchResults. Include a test with at least one matched pair and one unmatched entry.

Write a batch_convert function that accepts a list of raw unstructured address strings
and returns a list of HybridAddress objects, filtering out any that fail validation.
Log a warning (using Python's logging module) for each address that is filtered. This
skill should set audit_required: true in its header. Include a unit test.

# TIER 3: SYNTHESIS (5 tasks)
# These test whether the agent can abstract reusable patterns from what it has learned.
# This is where warm agents with a skill library should show the largest delta over cold.

You have seen parse_pacs008 and extract_statement_entries. Both parse ISO 20022 XML and
return structured Python objects. Abstract a reusable function called parse_iso20022_message(xml_string: str, msg_type: str) -> dict
that dispatches to the correct parser based on msg_type (using the constants in messages.py),
and returns a normalised dict with keys: msg_type, family, payload (the parsed dataclass
as a dict), and parse_error (None or an error string). Write a unit test that exercises
at least three message types.

You have seen validate_routing_number in ach.py and validate_hybrid_address in address.py.
Both follow a pattern: accept a data structure, return a list of string errors (empty = valid).
Abstract a generic validate(obj, rules: list[callable]) -> list[str] function where each
rule is a callable that takes the object and returns either None (pass) or a string (error
message). Rewrite validate_routing_number and validate_hybrid_address as thin wrappers
that compose rules using this function. Include a unit test.

You have seen LedgerEntry used in reconciliation.py and as the output of conversion
functions. Write a LedgerEntryBuilder class with a fluent interface: builder.from_iso20022(xml)
.from_ach(entry).with_rail("iso20022").build() -> LedgerEntry. The builder should raise
ValueError with a descriptive message if required fields (amount, currency, rail) are
missing at build time. Include a unit test.

Across the codebase you have seen several functions that accept raw strings (XML, address
text, ACH file content) and either return a parsed object or None/empty on failure.
Abstract a safe_parse(parser_fn, raw_input, fallback=None) utility that wraps any such
function, catches all exceptions, logs them at WARNING level, and returns fallback.
Demonstrate it wrapping parse_pacs008, parse_unstructured_address, and validate_routing_number.
Include a unit test.

You have seen match_by_reference produce MatchResults and surface_exceptions filter them.
Write a full reconciliation_report(results: list[MatchResult]) -> str function that produces
a human-readable plain-text summary: total count, matched count, unmatched count, partial
count, and for each exception the entry_id, status, confidence score, and reason.
This function should have audit_required: true in its skill header because it surfaces
financial discrepancies. Include a unit test that asserts the report contains key substrings.
```

---

## STEP 6: CREATE THE EXPLORATION TASK FILE

Create `eval/payment_exploration_tasks.txt`.

These twenty tasks are the warm-up run. Their purpose is to build a skill library of
reusable payment-domain functions before the benchmark runs. They must exercise the same
target repo but at lower difficulty than Tier 2/3 benchmark tasks, so the agent can
accumulate skills quickly without hitting the hard tasks cold.

```
Write a function get_message_family(msg_type: str) -> str that wraps get_family() from messages.py and returns "Unknown" instead of raising on unrecognised types. Include a unit test.

Write a function is_payment_instruction(msg_type: str) -> bool that returns True for pacs.008, pacs.009, and pain.001. Include a unit test with all three positive cases and one negative case.

Write a function format_currency_amount(amount: float, currency: str) -> str that returns a string like "USD 1,234.56". Include a unit test with at least three amounts including zero and negative.

Write a function make_trace_number(routing_number: str, sequence: int) -> str that returns a 15-digit NACHA trace number: the first 8 digits of the routing number plus a 7-digit zero-padded sequence. Include a unit test.

Write a function cents_to_dollars(cents: int) -> float. Include edge case tests for zero and large values.

Write a function dollars_to_cents(amount: float) -> int using round-half-up semantics. Include a unit test that confirms 1.005 rounds to 101 cents.

Write a function extract_iban_country(iban: str) -> str that returns the 2-letter country code from the start of an IBAN string, or raises ValueError if the string is shorter than 2 characters. Include a unit test.

Write a function is_sepa_country(country_code: str) -> bool. Hard-code a set of at least 10 real SEPA member country codes. Include a unit test.

Write a function build_end_to_end_id(sender_ref: str, date_str: str) -> str that returns a string in the format SENDER-YYYYMMDD-UUID4[:8]. Include a unit test.

Write a function mask_account_number(account: str) -> str that replaces all but the last 4 characters with asterisks. Include a unit test. This skill should have audit_required: true.

Write a function parse_booking_date(date_str: str) -> date that handles both YYYY-MM-DD and YYYYMMDD formats. Include a unit test covering both formats and an invalid input.

Write a function amount_in_range(amount: float, minimum: float, maximum: float) -> bool. Include boundary tests.

Write a function build_pacs008_stub(msg_id: str, amount: float, currency: str, debtor: str, creditor: str) -> str that returns a minimal valid pacs.008 XML string suitable for use with parse_pacs008() in parser.py. Include a round-trip unit test: build then parse, assert fields match.

Write a function count_by_status(results: list) -> dict that counts items in a list by their .status attribute. Include a unit test using MatchResult objects from reconciliation.py.

Write a function filter_by_rail(entries: list, rail: str) -> list that filters LedgerEntry objects from reconciliation.py by their rail field. Include a unit test.

Write a function sum_amounts(entries: list) -> Decimal that sums the amount field of a list of LedgerEntry objects from reconciliation.py. Include a unit test.

Write a function validate_iso_country(code: str) -> bool that returns True for any uppercase 2-letter string. Include a unit test with valid, lowercase, and 3-letter inputs.

Write a function truncate_name(name: str, max_len: int = 70) -> str that truncates a name to max_len characters and appends "..." if truncated. Include a unit test.

Write a function detect_rail_from_message_type(msg_type: str) -> str that returns "swift_mx" for pacs/camt/pain types, "nacha" for any string starting with "ACH", and "unknown" otherwise. Include a unit test.

Write a function group_by_currency(entries: list) -> dict[str, list] that groups LedgerEntry objects from reconciliation.py by their currency field. Include a unit test with at least two currencies.
```

---

## STEP 7: CREATE THE PAYMENT EXPERIMENT HARNESS

Create `eval/run_payment_experiment.py`.

This file mirrors the structure of `eval/run_experiment.py` but points at the payment
target repo and task files. Read `eval/run_experiment.py` in full before writing this —
copy its structure exactly, changing only the paths and descriptions.

```python
#!/usr/bin/env python3
"""
Payment Rail Experiment Harness
================================
Runs the cold/warm experiment for the payment protocol domain.

Usage:
    python eval/run_payment_experiment.py [--max-bench N] [--max-explore N]

This script:
  1. Resets the skill library (archives existing skills_py/ contents)
  2. Runs --max-bench benchmark tasks cold (no prior skills)
  3. Resets again
  4. Runs --max-explore exploration tasks to build the skill library
  5. Runs --max-bench benchmark tasks warm (with accumulated skills)
  6. Scores both runs and writes scores_payment.json

The hypothesis: warm > cold on Tier 2 and especially Tier 3 tasks.
"""

import argparse
import subprocess
import shutil
import json
import os
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
AGENT = ROOT / "self_building_agent"
SKILLS_PY = AGENT / "skills_py"
ARCHIVE = AGENT / "skills_py" / "archive"
LOGS = AGENT / "logs"
TARGET_REPO = ROOT / "eval" / "target_repo" / "iso20022_synthetic"
BENCH_TASKS = ROOT / "eval" / "payment_benchmark_tasks.txt"
EXPLORE_TASKS = ROOT / "eval" / "payment_exploration_tasks.txt"
SCORES_OUT = ROOT / "eval" / "scores_payment.json"

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def reset_skills():
    """Archive all current skills_py/*.py files. Preserve index.json structure."""
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for f in SKILLS_PY.glob("*.py"):
        dest = ARCHIVE / f"{f.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy(f, dest)
        f.unlink()
    # Reset index.json to empty skills array
    index_path = SKILLS_PY / "index.json"
    if index_path.exists():
        with open(index_path) as fh:
            index = json.load(fh)
        index["skills"] = []
        with open(index_path, "w") as fh:
            json.dump(index, fh, indent=2)
    log("Skills reset. Archive updated.")

def run_agent(task_file: Path, max_tasks: int, label: str) -> Path:
    """Run the agent on a task file. Returns path to the log file for this run."""
    run_log = LOGS / f"run_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    cmd = [
        sys.executable, str(AGENT / "run.py"),
        "--queue", str(task_file),
        "--target-repo", str(TARGET_REPO),
        "--max-tasks", str(max_tasks),
    ]
    log(f"Starting {label} run: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(AGENT))
    if result.returncode != 0:
        log(f"WARNING: agent exited with code {result.returncode} during {label} run")
    # Copy the main log to a labelled copy for scoring
    main_log = LOGS / "log.jsonl"
    if main_log.exists():
        shutil.copy(main_log, run_log)
    log(f"{label} run complete. Log: {run_log}")
    return run_log

def score_run(run_log: Path, task_file: Path, label: str) -> list[dict]:
    """Score a run log using eval/score.py. Returns list of score dicts."""
    score_script = ROOT / "eval" / "score.py"
    out_file = ROOT / "eval" / f"scores_{label}.json"
    cmd = [
        sys.executable, str(score_script),
        "--log", str(run_log),
        "--tasks", str(task_file),
        "--out", str(out_file),
        "--target-repo", str(TARGET_REPO),
    ]
    log(f"Scoring {label} run...")
    result = subprocess.run(cmd, cwd=str(ROOT / "eval"))
    if result.returncode != 0:
        log(f"WARNING: scorer exited with code {result.returncode} for {label}")
    if out_file.exists():
        with open(out_file) as fh:
            return json.load(fh)
    return []

def main():
    parser = argparse.ArgumentParser(description="Payment Rail Cold/Warm Experiment")
    parser.add_argument("--max-bench",   type=int, default=15,
                        help="Number of benchmark tasks per run (default: 15)")
    parser.add_argument("--max-explore", type=int, default=20,
                        help="Number of exploration tasks for warm-up (default: 20)")
    args = parser.parse_args()

    log("=== PAYMENT RAIL EXPERIMENT START ===")
    log(f"Benchmark tasks: {args.max_bench}, Exploration tasks: {args.max_explore}")

    # --- COLD RUN ---
    log("--- Phase 1: COLD run (no prior skills) ---")
    reset_skills()
    cold_log = run_agent(BENCH_TASKS, args.max_bench, "cold")
    cold_scores = score_run(cold_log, BENCH_TASKS, "cold")

    # --- WARM RUN ---
    log("--- Phase 2: Exploration (building skill library) ---")
    reset_skills()
    run_agent(EXPLORE_TASKS, args.max_explore, "explore")

    log("--- Phase 3: WARM run (with accumulated skills) ---")
    warm_log = run_agent(BENCH_TASKS, args.max_bench, "warm")
    warm_scores = score_run(warm_log, BENCH_TASKS, "warm")

    # --- SAVE COMBINED RESULTS ---
    results = {
        "experiment": "payment_rail",
        "timestamp": datetime.now().isoformat(),
        "config": {"max_bench": args.max_bench, "max_explore": args.max_explore},
        "cold": cold_scores,
        "warm": warm_scores,
    }
    with open(SCORES_OUT, "w") as fh:
        json.dump(results, fh, indent=2)
    log(f"Results written to {SCORES_OUT}")

    # --- QUICK SUMMARY ---
    if cold_scores and warm_scores:
        cold_avg = sum(s.get("total", 0) for s in cold_scores) / len(cold_scores)
        warm_avg = sum(s.get("total", 0) for s in warm_scores) / len(warm_scores)
        log(f"Cold avg score: {cold_avg:.2f}")
        log(f"Warm avg score: {warm_avg:.2f}")
        log(f"Delta: {warm_avg - cold_avg:+.2f}")
        if warm_avg > cold_avg:
            log("HYPOTHESIS SUPPORTED: warm > cold")
        else:
            log("HYPOTHESIS NOT SUPPORTED: warm <= cold")

    log("=== EXPERIMENT COMPLETE ===")

if __name__ == "__main__":
    main()
```

---

## STEP 8: EXTEND score.py FOR PAYMENT TASKS

Read `eval/score.py` in full. The existing scorer awards points for:
- LLM judge quality (0 or 2 points)
- Code executes (+1)
- Real file references (+1)
- Verified skill used (+1)

Add one new optional scoring criterion that only activates for payment benchmark tasks.
Add a CLI flag `--payment-domain` to `score.py`. When this flag is set, award +1 bonus
point if the response correctly identifies at least one ISO 20022 message type constant
by name (PACS_008, CAMT_053, etc.) or references a function from the synthetic target
repo by its exact name (parse_pacs008, extract_statement_entries, validate_routing_number,
etc.). This tests whether the agent actually read and used the target repo.

The check is a simple string match against the response text — no LLM call needed.

Also extend the scoring output to tag each task with its tier (1, 2, or 3) based on the
section comments in the task file. Parse the task file for `# TIER N:` comment markers
and assign the tier to each task by position. Include `tier` in each score dict so
`report.py` can show per-tier deltas.

---

## STEP 9: EXTEND report.py FOR PAYMENT RESULTS

Read `eval/report.py` in full. Add a new report mode that reads `eval/scores_payment.json`
and produces a payment-specific report. Add a CLI flag `--payment` that switches to this
mode.

The payment report must show:
- Overall cold avg vs warm avg and delta
- Per-tier breakdown: Tier 1 (structural), Tier 2 (translation), Tier 3 (synthesis)
- Which skills were most used in the warm run (from the log)
- How many skills survived the ComplianceShield (PASS vs WARN vs BLOCK counts from log)
- An LLM-generated one-paragraph verdict on whether the hypothesis holds, same as the
  existing report but using payment-domain framing

The LLM verdict prompt should be:
```
You are reviewing the results of a cold/warm experiment testing whether a self-constructing
agent performs better on financial protocol integration tasks when it has a pre-built skill
library. Cold avg score: {cold_avg:.2f}. Warm avg score: {warm_avg:.2f}. Delta: {delta:+.2f}.
Tier 1 delta (structural): {t1_delta:+.2f}. Tier 2 delta (translation): {t2_delta:+.2f}.
Tier 3 delta (synthesis): {t3_delta:+.2f}. Total skills verified in warm run: {skill_count}.
Skills that hit ComplianceShield WARN: {warn_count}.
Write a two-sentence verdict: does accumulated protocol knowledge help, and which tier
shows the strongest signal?
```

---

## STEP 10: SMOKE TEST

After all files are written, run the smoke test:

```bash
cd self_building_agent
set -a && . ./.env && set +a

python eval/run_payment_experiment.py --max-bench 3 --max-explore 3
python eval/report.py --payment
```

Fix any import errors, path errors, or key errors that appear. Do not change the
experiment logic to paper over real failures — fix the actual bugs.

If the Groq API key is not set or rate-limited, the agent will still run but tasks will
fail with LLM errors. That is acceptable for the smoke test — what you are verifying is
that the harness runs end-to-end without crashing, that the scorer produces output, and
that the report reads it. The scores themselves will be low or zero; that is fine.

---

## STEP 11: UPDATE THE README

Append a new section to the existing `README.md` (do not replace existing content):

```markdown
## Payment Rail Experiment

Tests the core hypothesis against financial protocol integration tasks.

### Setup

```bash
pip install python-iso20022 schwifty faker
```

### Quick smoke test (3 tasks each)

```bash
set -a && . ./.env && set +a
python eval/run_payment_experiment.py --max-bench 3 --max-explore 3
python eval/report.py --payment
```

### Full experiment (15 benchmark + 20 exploration tasks)

```bash
python eval/run_payment_experiment.py
python eval/report.py --payment
```

### What it tests

Three task tiers against an ISO 20022 / ACH target codebase:
- **Tier 1 — Structural**: read the target repo, extract correct information
- **Tier 2 — Translation**: write code bridging between payment formats
- **Tier 3 — Synthesis**: abstract reusable patterns from accumulated knowledge

The hypothesis is that a warm agent (one that has built a skill library during the
exploration phase) will score measurably higher on Tier 2 and Tier 3 tasks than a cold
agent starting from zero. The Tier 3 delta is the headline signal.

### New skill metadata fields

Payment-domain skills carry additional header fields:
- `# protocol:` — iso20022 | ach | fedwire | sepa | general
- `# rail:` — swift_mx | fednow | rtp | nacha | sepa_ct | on_chain | general
- `# audit_required:` — true | false

### ComplianceShield

Every payment skill passes through a static analysis check before persisting.
Skills with hardcoded credentials or routing numbers are blocked. Skills that
access financial data without a logging hook are flagged with a WARN.
```

---

## CONSTRAINTS AND GUARDRAILS

These are hard rules. Do not violate them:

1. Do not modify `eval/run_experiment.py`, `eval/benchmark_tasks.txt`, or
   `eval/exploration_tasks.txt`. The original fastapi experiment must still work.

2. Do not change the core skill verification pipeline (ast.parse + subprocess +
   TEST PASSED check). The ComplianceShield runs after that pipeline, not instead of it.

3. Do not add new LLM calls to the scoring or compliance logic. The ComplianceShield
   is static analysis only. New scoring criteria are string-match only.

4. Do not change the dashboard. It reads `skills_py/index.json` — as long as that file
   keeps its existing structure (with the new fields added alongside existing ones), the
   dashboard works as-is.

5. Every new Python file must pass `python -m py_compile <file>` with no errors before
   you consider the step complete.

6. Every function you write in the synthetic target repo must have a working unit test
   embedded in the file or in a companion `test_*.py` file. The agent needs to be able
   to run these tests to verify its own skills.

7. Do not use placeholder comments like `# TODO` or `# implement this`. Every function
   must be complete and working.

---

## DEFINITION OF DONE

The project is complete when:

- [ ] `python eval/run_payment_experiment.py --max-bench 3 --max-explore 3` runs end-to-end
      without crashing
- [ ] `python eval/report.py --payment` produces readable output
- [ ] `eval/scores_payment.json` exists and contains cold and warm score arrays
- [ ] At least one skill file appears in `skills_py/` after the explore run
- [ ] `compliance.py` exists and `check()` returns PASS for a clean skill and BLOCK for
      a skill containing a hardcoded 9-digit number
- [ ] The original fastapi experiment still runs:
      `python eval/run_experiment.py --max-bench 3 --max-explore 3`
- [ ] `README.md` contains the new Payment Rail Experiment section
