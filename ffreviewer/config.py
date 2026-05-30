"""Tunable values for the rule engine — thresholds, lookup sets, mappings.

Everything that is a *number* or a *list of things* lives here, separated
from the detection logic in rules.py. When a rule misbehaves we tweak here,
not in the rule code.

Values are calibrated against the 50 training sessions + gold labels.
"""

# ---------------------------------------------------------------------------
# Severity ranking (used to find the "worst" finding and compute the verdict)
# ---------------------------------------------------------------------------
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}

# ---------------------------------------------------------------------------
# R-001  Reason quality
# ---------------------------------------------------------------------------
# Calibration: all 14 R-001 training cases have reason length <= 42 chars.
# All 20 PASS training cases have reason length >= 123 chars.
# Threshold of 50 perfectly separates them with a safe margin.
MIN_REASON_LENGTH = 50  

#I calculated the 50-character threshold based on the training data. 
# The longest case that should be flagged was 42 characters, 
# while the shortest case that should not be flagged was 64 characters. I chose 50 as a safe middle ground.

# ---------------------------------------------------------------------------
# R-007  Out-of-hours session
# ---------------------------------------------------------------------------
# UTC. Sessions starting outside [6, 20) are "after hours".
BUSINESS_HOURS_START = 6   # 06:00 UTC
BUSINESS_HOURS_END   = 20  # 20:00 UTC

# If ANY of these appear in the reason, R-007 does NOT fire.
# These signal the firefighter had a legitimate, time-sensitive reason.
# Calibrated from PASS sessions that started after midnight:
#   "Resolved failed payment run F110 run ID ..."  -> "payment run"
#   "System maintenance per INC..."                -> "maintenance"
EMERGENCY_KEYWORDS = {"payment run", "maintenance", "monitoring", "alert"}

# ---------------------------------------------------------------------------
# R-002  Reason / action mismatch
# ---------------------------------------------------------------------------
# Words in reason suggesting read-only intent (no changes expected)
READ_ONLY_INTENT_WORDS = {"check", "display", "view", "inspect", "verification", "verify"}

# Words suggesting the reason scope is user/basis administration
BASIS_CONTEXT_WORDS    = {"user lock", "user reset", "locked user", "user account"}

# Financial/payment tcodes: if these appear when reason says "user admin", it's a mismatch
FINANCIAL_TCODES = {"FB02", "FB01", "XK02", "XK05", "FK02", "F110", "F-53", "F-58"}

# Words suggesting reason scope is FI-only
FI_CONTEXT_WORDS = {"posting issue", "g/l account", "fi investigation", "general ledger"}

# MM tcodes: if reason says "FI only" but one of these runs, it's a partial mismatch (medium)
MM_TCODES = {"MIRO", "MIGO", "ME23N", "ME21N"}

# ---------------------------------------------------------------------------
# R-004  Direct table modification
# ---------------------------------------------------------------------------
# SE16N = table browser edit mode, SM30 = view maintenance, both bypass normal FI controls
DIRECT_TABLE_TCODES = {"SE16N", "SM30"}

# ---------------------------------------------------------------------------
# R-006  Mass change
# ---------------------------------------------------------------------------
# Threshold: 99/98/114/124 changes on PASS sessions; 204/265 on REJECT.
# Using 150 leaves a clear gap above all PASS cases (max 124).
MASS_CHANGE_THRESHOLD = 150

# If reason contains any of these, the large volume is expected / documented
BULK_SCOPE_KEYWORDS = {
    "cleanup", "mass", "bulk", "batch", "multiple", "several",
    "all vendors", "eu vendors",
}

# ---------------------------------------------------------------------------
# R-009  Session duration
# ---------------------------------------------------------------------------
# Threshold: 99/105/114 min on non-R009 sessions; 281/317/353 on R009 sessions.
# Using 240 (4 hours) sits cleanly between the two groups.
MAX_SESSION_MINUTES = 240

# ---------------------------------------------------------------------------
# R-010  Segregation of Duties (SoD) conflict
# ---------------------------------------------------------------------------
# Each tuple = (set A, set B). If tcodes touch both sets in one session = SoD violation.
# Pattern from data: changing vendor bank details + running payment in same session.
SOD_CONFLICT_PAIRS = [
    ({"XK02", "FK02"}, {"F110", "F-53", "F-58"}),
]

# ---------------------------------------------------------------------------
# R-011  High-risk bank data modification (additional rule — see README)
# ---------------------------------------------------------------------------
# LFBK table holds vendor bank accounts. BANKN = account number, IBAN = IBAN.
# Changing these directly during a firefighter session is a prime BEC fraud vector.
# In training data: LFBK changes appear ONLY on REJECT sessions — zero in PASS.
BANK_DATA_TABLES = {"LFBK"}
BANK_DATA_FIELDS = {"BANKN", "IBAN", "SWIFT", "BANKA"}