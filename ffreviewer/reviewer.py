"""Orchestrator: turn a session into a full prediction.

review(session):
    1. run_all_rules(session)        -> findings
    2. verdict_from_findings(...)    -> PASS / NEEDS_CORRECTION / REJECT
    3. if NEEDS_CORRECTION: draft a suggested_correction
    4. return a Prediction
"""

from .config import SEVERITY_RANK


def verdict_from_findings(findings):
    """Map a list of findings to a verdict.

    Rule derived from the train labels (holds for all 50 examples):
        no findings            -> PASS
        worst severity == medium -> NEEDS_CORRECTION
        worst severity >= high   -> REJECT
    """
    if not findings:
        return "PASS"
    worst = max(SEVERITY_RANK[f.severity] for f in findings)
    if worst >= SEVERITY_RANK["high"]:
        return "REJECT"
    return "NEEDS_CORRECTION"


# def review(session): ...   # we wire this once rules + models exist
