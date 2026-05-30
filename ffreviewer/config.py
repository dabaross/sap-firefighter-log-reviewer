"""Tunable knobs and lookup tables for the rule engine.

Everything that is a *threshold* or a *list* lives here, separated from the
detection logic in rules.py. This makes the rules readable and lets us
calibrate against the train set without touching code logic.

NOTE: the seed values below are starting points. We refine them by looking
at the train sessions + labels (NEVER at the test set).
"""

# --- Severity model -----------------------------------------------------
# Numeric rank lets us compute "the most severe finding in a session".
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}

# --- Verdict thresholds (derived from train labels) ---------------------
# 0 findings            -> PASS
# max severity == medium -> NEEDS_CORRECTION
# max severity >= high   -> REJECT
# (See reviewer.verdict_from_findings.)

# --- Business hours (for R-007) ----------------------------------------
# Sessions outside this window AND without a genuine-emergency signal are
# suspicious. UTC hours. TODO: confirm window against train data.
BUSINESS_HOURS_START = 7   # 07:00 UTC
BUSINESS_HOURS_END = 19    # 19:00 UTC

# --- R-001: generic / weak reason terms --------------------------------
# TODO: build this list from real weak reasons in the train set.
GENERIC_REASON_TERMS = {"test", "fix", "asap", "production issue"}
MIN_REASON_LENGTH = 20

# --- tcode -> SAP module (for R-002 reason/action mismatch) -------------
# TODO: fill from tcodes actually seen in the data.
TCODE_MODULE = {
    # "F110": "FI", "FB01": "FI", "SU01": "BASIS", ...
}

# --- Sensitive tables (for R-004 direct table edits) -------------------
# TODO: confirm which tables appear in the data and matter.
SENSITIVE_TABLES = {
    # "T001", "LFA1", "LFBK", "USR02", ...
}

# --- Segregation-of-Duties conflicting tcode pairs (for R-010) ----------
# TODO: confirm from data; the brief gives vendor-maintenance + payment.
SOD_CONFLICT_PAIRS = [
    # ("XK02", "F110"), ("FK02", "F110"), ...
]

# --- R-006: mass-change threshold --------------------------------------
MASS_CHANGE_THRESHOLD = 50  # TODO: calibrate on train

# --- R-009: session duration limit -------------------------------------
MAX_SESSION_MINUTES = 120   # TODO: calibrate on train
