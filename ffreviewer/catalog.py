"""The rule catalog: metadata for every rule we can emit.

This is reference data (not logic). Each rule has a stable id, a default
severity, and a short description. Severities below were read off the train
labels and match how the gold standard scores each rule.

R-002 is the only rule whose severity varies (usually high, sometimes
medium); its detector decides the severity case by case.
"""

RULE_CATALOG = {
    "R-001": {"severity": "medium",   "title": "Reason code empty / generic / too short"},
    "R-002": {"severity": "high",     "title": "Reason mentions one area but actions touch another"},
    "R-003": {"severity": "critical", "title": "Debug & replace (value modified in debugger)"},
    "R-004": {"severity": "high",     "title": "Direct table modification without documented data fix"},
    "R-005": {"severity": "critical", "title": "OS-level command executed (SM49)"},
    "R-006": {"severity": "high",     "title": "Change/transaction count exceeds reason scope"},
    "R-007": {"severity": "medium",   "title": "Out-of-hours session without genuine emergency"},
    "R-008": {"severity": "high",     "title": "Firefighter == ticket requester (self-approval)"},
    "R-009": {"severity": "medium",   "title": "Session exceeds duration limit, no re-justification"},
    "R-010": {"severity": "critical", "title": "Segregation-of-duties conflicting transactions"},
    # --- Additional rules we justify from data go here (R-011+) ---
}
