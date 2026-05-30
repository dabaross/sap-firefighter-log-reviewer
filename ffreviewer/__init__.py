"""AI-assisted SAP Firefighter Log Compliance Reviewer.

Pipeline:
    session JSON -> models (validate) -> rules (detect issues)
                 -> reviewer (aggregate findings -> verdict)
                 -> corrections (draft message for NEEDS_CORRECTION)
                 -> prediction JSON
"""
