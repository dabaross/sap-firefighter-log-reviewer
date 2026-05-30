"""Unit tests for the rule detectors.

We add one focused test per rule as we implement it: a session that SHOULD
trigger it, and a near-miss that should NOT (guards against false positives).
"""


def test_placeholder():
    assert True  # replaced as we implement each rule
