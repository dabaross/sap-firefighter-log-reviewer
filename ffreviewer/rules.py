"""Deterministic rule detectors.

Each detector inspects a validated Session and returns a Finding (or None,
or a list). Keep each rule small, named, and independently testable.

Design goal: HIGH PRECISION. A false finding on a clean session flips its
verdict away from PASS and costs accuracy. When in doubt, do NOT fire.

TODO (build together, one rule at a time):
    check_r001_reason_quality(session)
    check_r002_reason_action_mismatch(session)
    check_r003_debug_replace(session)
    check_r004_direct_table_edit(session)
    check_r005_os_command(session)
    check_r006_mass_change(session)
    check_r007_out_of_hours(session)
    check_r008_self_approval(session)
    check_r009_duration(session)
    check_r010_sod_conflict(session)

    run_all_rules(session) -> list[Finding]
"""
