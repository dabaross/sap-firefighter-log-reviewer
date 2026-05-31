"""Correction generator — two modes.

use_llm=False (default): template-based, free, deterministic.
use_llm=True:            calls Anthropic API for richer phrasing.

Switch via ANTHROPIC_API_KEY env var or explicit parameter.
"""

import os
from .models import Session, Finding, SuggestedCorrection

RULE_CLARIFICATION = {
    "R-001": "provide a detailed justification: what broke, what you did, and why it required emergency access",
    "R-002": "clarify the discrepancy between your stated reason and the actions performed",
    "R-007": "explain why the issue required after-hours emergency access rather than waiting for business hours",
    "R-009": "explain why the session lasted so long and document what was done during the extended period",
}


def build_correction_template(session: Session, findings: list[Finding]) -> SuggestedCorrection:
    """Template-based correction — no API key needed."""
    points = []
    for finding in findings:
        clarification = RULE_CLARIFICATION.get(finding.rule_id)
        if clarification:
            points.append(f"({len(points)+1}) Please {clarification}.")

    if not points:
        points.append("(1) Please provide additional justification for this session.")

    message = (
        f"Session {session.session_id} requires additional information "
        f"before it can be approved. {' '.join(points)}"
    )
    rewrite = (
        f"[Describe what broke] — [what you did to fix it] — "
        f"[outcome] — ticket: {session.ticket_reference or 'N/A'}"
    )
    return SuggestedCorrection(
        message_to_firefighter=message,
        suggested_reason_rewrite=rewrite,
    )


def build_correction_llm(session: Session, findings: list[Finding]) -> SuggestedCorrection:
    """LLM-based correction — requires ANTHROPIC_API_KEY in environment."""
    try:
        import anthropic
    except ImportError:
        return build_correction_template(session, findings)

    findings_text = "\n".join(
        f"- {f.rule_id} ({f.severity}): {f.description} | evidence: {f.evidence}"
        for f in findings
    )

    prompt = f"""You are a SAP compliance officer reviewing a firefighter session.
The session was classified as NEEDS_CORRECTION based on these findings:

{findings_text}

Session details:
- Session ID: {session.session_id}
- Firefighter user: {session.firefighter_user}
- Original reason: "{session.reason_code}"
- Ticket reference: {session.ticket_reference or "none"}
- Transactions executed: {session.tcodes}

Write two things:
1. A professional but direct message to the firefighter explaining what 
   additional information is needed and why. Be specific — reference the 
   actual transactions and the original reason. Max 4 sentences.
2. A suggested rewrite of the reason field that would make this session 
   compliant — specific, with ticket reference, what broke, what was done.

Respond in this exact format:
MESSAGE: <your message here>
REWRITE: <your suggested reason rewrite here>"""

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text
    message = ""
    rewrite = ""

    for line in text.splitlines():
        if line.startswith("MESSAGE:"):
            message = line[len("MESSAGE:"):].strip()
        elif line.startswith("REWRITE:"):
            rewrite = line[len("REWRITE:"):].strip()

    if not message:
        return build_correction_template(session, findings)

    return SuggestedCorrection(
        message_to_firefighter=message,
        suggested_reason_rewrite=rewrite or None,
    )


def build_correction(
    session: Session,
    findings: list[Finding],
    use_llm: bool | None = None,
) -> SuggestedCorrection:
    """Main entry point.
    
    use_llm=None  -> auto: use LLM if ANTHROPIC_API_KEY is set, else template
    use_llm=True  -> force LLM
    use_llm=False -> force template
    """
    if use_llm is None:
        use_llm = bool(os.environ.get("ANTHROPIC_API_KEY"))

    if use_llm:
        return build_correction_llm(session, findings)
    return build_correction_template(session, findings)