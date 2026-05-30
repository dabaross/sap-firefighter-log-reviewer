"""Data models for input sessions and output predictions.

Pydantic validates every field type and required/optional status at load
time, so rule logic never has to guard against missing keys or wrong types.
"""

from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Input sub-models  (the four log lists inside a session)
# ---------------------------------------------------------------------------

class TransactionEntry(BaseModel):
    """One tcode executed during the session (what the user opened/ran)."""
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    tcode: str
    description: str


class ChangeEntry(BaseModel):
    """One record-level change written to the database."""
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    table: str
    key: str
    field: str
    old_value: str
    new_value: str


class SystemLogEntry(BaseModel):
    """One SM21 system-log message (debug events live here)."""
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    message: str
    type: str


class OsCommandEntry(BaseModel):
    """One OS-level command executed via SM49."""
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    command: str
    parameters: str
    executed_by: str


# ---------------------------------------------------------------------------
# Top-level input model
# ---------------------------------------------------------------------------

class Session(BaseModel):
    """A complete firefighter session log (one input JSON file)."""
    model_config = ConfigDict(extra="ignore")

    session_id: str
    firefighter_id: str
    firefighter_user: str
    controller: str
    system: str
    client: str
    start_time: datetime
    end_time: datetime
    reason_code: str
    ticket_reference: str

    # Optional — only some sessions have this field
    ticket_requester: Optional[str] = None   # used by R-008 (self-approval)

    transaction_log: list[TransactionEntry] = []
    change_log: list[ChangeEntry] = []
    system_log: list[SystemLogEntry] = []
    os_command_log: list[OsCommandEntry] = []

    @property
    def duration_minutes(self) -> float:
        """How long the session lasted, in minutes."""
        return (self.end_time - self.start_time).total_seconds() / 60

    @property
    def tcodes(self) -> list[str]:
        """All transaction codes executed, in order."""
        return [t.tcode for t in self.transaction_log]


# ---------------------------------------------------------------------------
# Output models  (what we write to predictions JSONL)
# ---------------------------------------------------------------------------

Severity = Literal["low", "medium", "high", "critical"]
Verdict  = Literal["PASS", "REJECT", "NEEDS_CORRECTION"]


class Finding(BaseModel):
    """One detected compliance issue."""
    rule_id: str
    severity: Severity
    location: str
    description: str
    evidence: str


class SuggestedCorrection(BaseModel):
    """Draft message back to the firefighter (NEEDS_CORRECTION only)."""
    message_to_firefighter: str
    suggested_reason_rewrite: Optional[str] = None


class Prediction(BaseModel):
    """Our full output for one session — matches the labels.jsonl schema."""
    session_id: str
    verdict: Verdict
    confidence: float
    findings: list[Finding] = []
    suggested_correction: Optional[SuggestedCorrection] = None