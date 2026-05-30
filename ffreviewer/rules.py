"""Deterministic compliance rule detectors.

Each function takes a Session and returns either:
  - None           → rule does not apply, no finding
  - Finding(...)   → rule fired, issue found

Design goal: HIGH PRECISION.
A false finding on a clean session flips it from PASS to NEEDS_CORRECTION/REJECT.
When in doubt, do NOT fire.

run_all_rules(session) collects all findings into a list.
"""

from .models import Session, Finding
from .config import (
    MIN_REASON_LENGTH,
    BUSINESS_HOURS_START, BUSINESS_HOURS_END, EMERGENCY_KEYWORDS,
    READ_ONLY_INTENT_WORDS, BASIS_CONTEXT_WORDS, FINANCIAL_TCODES,
    FI_CONTEXT_WORDS, MM_TCODES,
    DIRECT_TABLE_TCODES,
    MASS_CHANGE_THRESHOLD, BULK_SCOPE_KEYWORDS,
    MAX_SESSION_MINUTES,
    SOD_CONFLICT_PAIRS,
    BANK_DATA_TABLES, BANK_DATA_FIELDS,
)


def check_r001_reason_quality(session: Session) -> Finding | None:
    """R-001: Reason is too short or generic to justify the session."""
    reason = session.reason_code.strip()
    if len(reason) >= MIN_REASON_LENGTH:
        return None  # long enough — pass
    return Finding(
        rule_id="R-001",
        severity="medium",
        location="reason_code",
        description=(
            f"Reason is too short ({len(reason)} chars) to adequately justify "
            "the firefighter session. A compliant reason should specify what "
            "broke, what was done, and reference the ticket."
        ),
        evidence=reason,
    )


def check_r002_reason_action_mismatch(session: Session) -> Finding | None:
    """R-002: Reason describes one scope of work, but actions performed another."""
    reason_lower = session.reason_code.lower()
    tcodes = set(session.tcodes)

    # Pattern 1: reason explicitly combines SoD-dangerous activities
    # e.g. "Updated vendor bank details and triggered payment"
    if "bank" in reason_lower and "payment" in reason_lower:
        return Finding(
            rule_id="R-002",
            severity="high",
            location="reason_code",
            description=(
                "Reason explicitly admits combining vendor master modification "
                "with payment activity — a SoD-dangerous combination that should "
                "never be documented as intentional in a firefighter session."
            ),
            evidence=session.reason_code,
        )

    # Pattern 2: reason claims read-only intent, but changes were actually made
    is_read_only_reason = any(w in reason_lower for w in READ_ONLY_INTENT_WORDS)
    if is_read_only_reason and len(session.change_log) > 0:
        return Finding(
            rule_id="R-002",
            severity="high",
            location="reason_code",
            description=(
                "Reason implies read-only / inspection activity, "
                f"but {len(session.change_log)} change(s) were recorded."
            ),
            evidence=(
                f"Reason: '{session.reason_code}' — "
                f"but change_log has {len(session.change_log)} entries."
            ),
        )

    # Pattern 3: reason says "user admin / lock reset" but financial tcodes were used
    is_basis_reason = any(w in reason_lower for w in BASIS_CONTEXT_WORDS)
    financial_used = tcodes & FINANCIAL_TCODES
    if is_basis_reason and financial_used:
        return Finding(
            rule_id="R-002",
            severity="high",
            location="reason_code",
            description=(
                "Reason indicates Basis/user-admin work, but financial "
                f"transaction(s) were executed: {sorted(financial_used)}."
            ),
            evidence=(
                f"Reason: '{session.reason_code}' | "
                f"Financial tcodes used: {sorted(financial_used)}"
            ),
        )

    # Pattern 4: reason states FI-only scope, but MM tcode (MIRO etc.) was used
    is_fi_reason = any(w in reason_lower for w in FI_CONTEXT_WORDS)
    mm_used = tcodes & MM_TCODES
    if is_fi_reason and mm_used:
        return Finding(
            rule_id="R-002",
            severity="medium",
            location="reason_code",
            description=(
                "Reason specifies FI scope only, but MM transaction(s) "
                f"were executed: {sorted(mm_used)}."
            ),
            evidence=(
                f"Reason: '{session.reason_code}' | "
                f"MM tcodes used: {sorted(mm_used)}"
            ),
        )

    return None


def check_r003_debug_replace(session: Session) -> Finding | None:
    """R-003: A value was modified via the ABAP debugger (/h replace)."""
    for i, entry in enumerate(session.system_log):
        msg_lower = entry.message.lower()
        # The tell-tale sign is "variable value changed" in the SM21 log
        if "variable value changed" in msg_lower and "debug" in msg_lower:
            return Finding(
                rule_id="R-003",
                severity="critical",
                location=f"system_log[{i}]",
                description=(
                    "A variable was modified via the ABAP debugger (/h replace). "
                    "This bypasses all normal authorization and change-document controls "
                    "and is a critical audit finding."
                ),
                evidence=entry.message,
            )
    return None


def check_r004_direct_table_edit(session: Session) -> Finding | None:
    """R-004: SE16N or SM30 used — direct table modification without change request."""
    dangerous_used = [t for t in session.tcodes if t in DIRECT_TABLE_TCODES]
    if not dangerous_used:
        return None
    return Finding(
        rule_id="R-004",
        severity="high",
        location="transaction_log",
        description=(
            f"{dangerous_used} used in firefighter session. "
            "These tcodes allow direct table editing, bypassing normal "
            "authorization objects and change management. "
            "Requires a documented data-fix request to be compliant."
        ),
        evidence=f"Tcodes executed: {dangerous_used}",
    )


def check_r005_os_command(session: Session) -> Finding | None:
    """R-005: OS-level commands executed via SM49."""
    if not session.os_command_log:
        return None
    first = session.os_command_log[0]
    return Finding(
        rule_id="R-005",
        severity="critical",
        location="os_command_log",
        description=(
            "OS-level commands were executed during the firefighter session. "
            "This grants the ability to read/modify any file on the server and "
            "is almost never justified in an emergency access scenario."
        ),
        evidence=(
            f"Command: '{first.command}' | "
            f"Parameters: '{first.parameters}' | "
            f"Executed by: {first.executed_by} | "
            f"Total OS commands: {len(session.os_command_log)}"
        ),
    )


def check_r006_mass_change(session: Session) -> Finding | None:
    """R-006: Change count far exceeds what the reason claims to justify."""
    n = len(session.change_log)
    if n < MASS_CHANGE_THRESHOLD:
        return None
    reason_lower = session.reason_code.lower()
    # If the reason already documents mass / bulk work, the volume is expected
    if any(kw in reason_lower for kw in BULK_SCOPE_KEYWORDS):
        return None
    return Finding(
        rule_id="R-006",
        severity="high",
        location="change_log",
        description=(
            f"{n} change-log entries recorded, but the stated reason does not "
            "indicate a mass update was planned. This volume suggests the "
            "firefighter performed work beyond the stated scope."
        ),
        evidence=f"{n} changes in change_log | Reason: '{session.reason_code}'",
    )


def check_r007_out_of_hours(session: Session) -> Finding | None:
    """R-007: Session outside business hours without a genuine emergency signal."""
    hour = session.start_time.hour  # UTC hour (0-23)
    in_business_hours = BUSINESS_HOURS_START <= hour < BUSINESS_HOURS_END
    if in_business_hours:
        return None

    reason_lower = session.reason_code.lower()
    if any(kw in reason_lower for kw in EMERGENCY_KEYWORDS):
        return None  # reason explains why after-hours access was necessary

    return Finding(
        rule_id="R-007",
        severity="medium",
        location="start_time",
        description=(
            f"Session started at {session.start_time.strftime('%H:%M')} UTC, "
            "outside business hours, and the reason does not clearly establish "
            "an emergency that required immediate after-hours access."
        ),
        evidence=f"start_time: {session.start_time.isoformat()} | reason: '{session.reason_code}'",
    )


def check_r008_self_approval(session: Session) -> Finding | None:
    """R-008: Firefighter user and ticket requester are the same person."""
    if session.ticket_requester is None:
        return None  # field not present — can't check
    if session.ticket_requester != session.firefighter_user:
        return None
    return Finding(
        rule_id="R-008",
        severity="high",
        location="ticket_requester",
        description=(
            "The firefighter user and the ticket requester are the same person "
            f"({session.firefighter_user}). This is a self-approval pattern: "
            "the person who requested emergency access also performed the work, "
            "with no independent oversight."
        ),
        evidence=(
            f"firefighter_user={session.firefighter_user} == "
            f"ticket_requester={session.ticket_requester}"
        ),
    )


def check_r009_duration(session: Session) -> Finding | None:
    """R-009: Session far exceeded the expected duration without re-justification."""
    duration = session.duration_minutes
    if duration <= MAX_SESSION_MINUTES:
        return None
    hours = duration / 60
    return Finding(
        rule_id="R-009",
        severity="medium",
        location="session_duration",
        description=(
            f"Session lasted {hours:.1f} hours ({duration:.0f} minutes), "
            f"exceeding the {MAX_SESSION_MINUTES}-minute limit. "
            "Extended sessions require documented re-justification."
        ),
        evidence=(
            f"start={session.start_time.isoformat()} | "
            f"end={session.end_time.isoformat()} | "
            f"duration={duration:.0f} min"
        ),
    )


def check_r010_sod_conflict(session: Session) -> Finding | None:
    """R-010: Tcodes from two SoD-conflicting groups used in the same session."""
    tcode_set = set(session.tcodes)
    for group_a, group_b in SOD_CONFLICT_PAIRS:
        a_used = tcode_set & group_a
        b_used = tcode_set & group_b
        if a_used and b_used:
            return Finding(
                rule_id="R-010",
                severity="critical",
                location="transaction_log",
                description=(
                    "Segregation of Duties (SoD) violation: "
                    "vendor master maintenance and payment execution combined in one session. "
                    "This allows a single person to change vendor bank details "
                    "and immediately trigger a payment to the new account."
                ),
                evidence=(
                    f"Vendor master tcodes: {sorted(a_used)} | "
                    f"Payment tcodes: {sorted(b_used)}"
                ),
            )
    return None


def check_r011_bank_data_change(session: Session) -> Finding | None:
    """R-011 (additional): Direct modification of vendor bank account or IBAN data.

    Rationale: BEC (Business Email Compromise) fraud frequently involves secretly
    changing a vendor's bank account number so payments are redirected. A firefighter
    modifying LFBK.BANKN or LFBK.IBAN directly is one of the highest-risk change
    patterns possible. In the training data, ALL LFBK changes occur on REJECT sessions.
    This rule adds an explicit, named finding for this scenario.
    """
    for i, entry in enumerate(session.change_log):
        if entry.table in BANK_DATA_TABLES and entry.field in BANK_DATA_FIELDS:
            return Finding(
                rule_id="R-011",
                severity="critical",
                location=f"change_log[{i}]",
                description=(
                    f"Direct modification of vendor bank data "
                    f"(table {entry.table}, field {entry.field}). "
                    "This is a critical fraud-risk change: altering bank account "
                    "details can redirect payments. Must be approved by AP management."
                ),
                evidence=(
                    f"table={entry.table} | key={entry.key} | "
                    f"field={entry.field} | "
                    f"{entry.old_value} -> {entry.new_value}"
                ),
            )
    return None


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_all_rules(session: Session) -> list[Finding]:
    """Run all rule detectors and return the list of findings (no Nones)."""
    checkers = [
        check_r001_reason_quality,
        check_r002_reason_action_mismatch,
        check_r003_debug_replace,
        check_r004_direct_table_edit,
        check_r005_os_command,
        check_r006_mass_change,
        check_r007_out_of_hours,
        check_r008_self_approval,
        check_r009_duration,
        check_r010_sod_conflict,
        check_r011_bank_data_change,
    ]
    findings = []
    for checker in checkers:
        result = checker(session)
        if result is not None:
            findings.append(result)
    return findings