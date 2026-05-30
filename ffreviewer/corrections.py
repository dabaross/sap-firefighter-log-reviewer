"""Template-based suggested_correction generator (no API key required).

For NEEDS_CORRECTION sessions we draft:
    - message_to_firefighter : what extra info / justification is needed
    - suggested_reason_rewrite : a better version of the reason field

We build the message from the findings that were detected, so it always
matches what the system actually flagged. An LLM could replace this later
for richer phrasing, but templates are deterministic and free.

TODO (build together).
"""
