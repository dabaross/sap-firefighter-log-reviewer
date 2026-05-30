"""Data models for input sessions and output predictions.

We use Pydantic so that malformed input fails loudly and predictably
instead of crashing somewhere deep in the rule logic.

TODO (build together):
    - Session            : one firefighter session (the input file, section 4)
    - LogEntry sub-models : transaction_log / change_log / system_log / os_command_log
    - Finding            : one detected compliance issue (rule_id, severity, ...)
    - Prediction         : our output record (session_id, verdict, findings, ...)
"""

# from pydantic import BaseModel, Field
# ... we implement these in the next step.
