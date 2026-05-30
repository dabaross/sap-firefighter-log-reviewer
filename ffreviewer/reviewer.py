"""Orchestrator: turns a validated Session into a complete Prediction."""

from .models import Session, Prediction, Finding, SuggestedCorrection
from .rules import run_all_rules
from .corrections import build_correction
from .config import SEVERITY_RANK


def verdict_from_findings(findings: list[Finding]) -> str:
    """Compute verdict from the worst severity found.

    Derived from train labels (holds for all 50 cases):
      no findings              -> PASS
      worst severity == medium -> NEEDS_CORRECTION
      worst severity >= high   -> REJECT
    """
    if not findings:
        return "PASS"
    worst = max(SEVERITY_RANK[f.severity] for f in findings)
    if worst >= SEVERITY_RANK["high"]:
        return "REJECT"
    return "NEEDS_CORRECTION"


def confidence_from_verdict(verdict: str, findings: list[Finding]) -> float:
    """Simple heuristic confidence score.

    PASS with no findings = 1.0 (certain).
    REJECT with a critical rule = 0.95 (rule-based, very reliable).
    NEEDS_CORRECTION = 0.70 (borderline by definition).
    """
    if verdict == "PASS":
        return 1.0
    if verdict == "REJECT":
        has_critical = any(f.severity == "critical" for f in findings)
        return 0.95 if has_critical else 0.85
    return 0.70  # NEEDS_CORRECTION


def review(session: Session) -> Prediction:
    """Full pipeline: session -> findings -> verdict -> prediction."""
    findings = run_all_rules(session)
    verdict = verdict_from_findings(findings)
    confidence = confidence_from_verdict(verdict, findings)

    correction = None
    if verdict == "NEEDS_CORRECTION":
        correction = build_correction(session, findings)

    return Prediction(
        session_id=session.session_id,
        verdict=verdict,
        confidence=confidence,
        findings=findings,
        suggested_correction=correction,
    )