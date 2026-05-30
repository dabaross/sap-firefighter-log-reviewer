"""Template-based suggested_correction generator (no API key needed).

Builds the correction message from whichever rules fired, so it always
matches what the system actually flagged.
"""

from .models import Session, Finding, SuggestedCorrection


# Maps rule_id -> one sentence asking for the missing information
RULE_CLARIFICATION = {
    "R-001": "provide a detailed justification: what broke, what you did, and why it required emergency access",
    "R-002": "clarify the discrepancy between your stated reason and the actions performed",
    "R-007": "explain why the issue required after-hours emergency access rather than waiting for business hours",
    "R-009": "explain why the session lasted so long and document what was done during the extended period",
}


def build_correction(session: Session, findings: list[Finding]) -> SuggestedCorrection:
    """Draft a clarification request based on the findings that fired."""
    points = []
    for finding in findings:
        clarification = RULE_CLARIFICATION.get(finding.rule_id)
        if clarification:
            points.append(f"({len(points)+1}) Please {clarification}.")

    if not points:
        points.append("(1) Please provide additional justification for this session.")

    numbered = " ".join(points)
    message = (
        f"Session {session.session_id} requires additional information "
        f"before it can be approved. {numbered}"
    )

    rewrite = (
        f"[Describe what broke] — [what you did to fix it] — "
        f"[outcome] — ticket: {session.ticket_reference or 'N/A'}"
    )

    return SuggestedCorrection(
        message_to_firefighter=message,
        suggested_reason_rewrite=rewrite,
    )