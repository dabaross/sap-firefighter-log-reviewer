"""Basic rule detector tests.

One positive case (should fire) and one negative case (should NOT fire)
per rule — guards against false positives on clean sessions.
"""

import pytest
from ffreviewer.models import Session, Finding
from ffreviewer.rules import (
    check_r001_reason_quality,
    check_r005_os_command,
    check_r010_sod_conflict,
)
from ffreviewer.reviewer import verdict_from_findings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_session(**kwargs):
    """Build a minimal valid session, overriding fields via kwargs."""
    base = {
        "session_id": "FF-TEST-000",
        "firefighter_id": "FF_FI_01",
        "firefighter_user": "TESTUSER",
        "controller": "CONTROLLER",
        "system": "PRD-S4",
        "client": "TEST",
        "start_time": "2026-04-15T10:00:00Z",
        "end_time": "2026-04-15T11:00:00Z",
        "reason_code": "Resolved failed payment run F110 for Company Code 1000 per INC0012345",
        "ticket_reference": "INC0012345",
        "transaction_log": [],
        "change_log": [],
        "system_log": [],
        "os_command_log": [],
    }
    base.update(kwargs)
    return Session.model_validate(base)


# ---------------------------------------------------------------------------
# R-001  Reason quality
# ---------------------------------------------------------------------------

def test_r001_fires_on_short_reason():
    s = make_session(reason_code="fix")
    assert check_r001_reason_quality(s) is not None

def test_r001_does_not_fire_on_long_reason():
    s = make_session(reason_code="Resolved failed payment run F110 for Company Code 1000 per INC0012345")
    assert check_r001_reason_quality(s) is None


# ---------------------------------------------------------------------------
# R-005  OS command
# ---------------------------------------------------------------------------

def test_r005_fires_when_os_command_present():
    s = make_session(os_command_log=[{
        "timestamp": "2026-04-15T10:05:00Z",
        "command": "ZBR_BACKUP_CLEAR",
        "parameters": "/oracle/PRD",
        "executed_by": "TESTUSER",
    }])
    assert check_r005_os_command(s) is not None

def test_r005_does_not_fire_on_empty_os_log():
    s = make_session(os_command_log=[])
    assert check_r005_os_command(s) is None


# ---------------------------------------------------------------------------
# R-010  SoD conflict
# ---------------------------------------------------------------------------

def test_r010_fires_on_vendor_master_plus_payment():
    s = make_session(transaction_log=[
        {"timestamp": "2026-04-15T10:01:00Z", "tcode": "XK02", "description": "Change vendor"},
        {"timestamp": "2026-04-15T10:02:00Z", "tcode": "F110", "description": "Payment run"},
    ])
    assert check_r010_sod_conflict(s) is not None

def test_r010_does_not_fire_on_vendor_master_alone():
    s = make_session(transaction_log=[
        {"timestamp": "2026-04-15T10:01:00Z", "tcode": "XK02", "description": "Change vendor"},
    ])
    assert check_r010_sod_conflict(s) is None

def test_r010_does_not_fire_on_xk05_plus_payment():
    """XK05 (block/unblock) was explicitly removed from the SoD pair
    because unblocking a vendor before a payment run is a legitimate
    emergency fix pattern."""
    s = make_session(transaction_log=[
        {"timestamp": "2026-04-15T10:01:00Z", "tcode": "XK05", "description": "Block vendor"},
        {"timestamp": "2026-04-15T10:02:00Z", "tcode": "F110", "description": "Payment run"},
    ])
    assert check_r010_sod_conflict(s) is None


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

def test_verdict_no_findings_is_pass():
    assert verdict_from_findings([]) == "PASS"

def test_verdict_medium_only_is_needs_correction():
    class F:
        severity = "medium"
    assert verdict_from_findings([F()]) == "NEEDS_CORRECTION"

def test_verdict_critical_is_reject():
    class F:
        severity = "critical"
    assert verdict_from_findings([F()]) == "REJECT"

def test_verdict_mixed_medium_and_high_is_reject():
    class F:
        def __init__(self, s): self.severity = s
    assert verdict_from_findings([F("medium"), F("high")]) == "REJECT"