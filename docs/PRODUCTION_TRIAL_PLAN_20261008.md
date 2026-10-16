# Two-day bounded production trial implementation plan

Goal: start the Human-approved real-input trial with a non-renewing deadline at 2026-10-10T13:11:50Z, after delivering the requested backlog catch-up.
Spec: ALICE_PRODUCTION_TRIAL_AUTHORIZATION_20261008.md at74965cd; accepted runtime6c2589d. Local execution, Class C/enhanced. No merge/autostart or wider task authority.
Architecture: preserve the existing worker/Store and ledger. Bind an optional UTC deadline immutably in that Store, guard work/actions and exit the existing watcher loop on expiry. Start this trial in loaded-owner-only mode with no window backend. Reuse verified business delivery hashes; never seed an observed but undelivered snapshot.

## Tasks

- [ ] Test then implement trigger.py fixed deadline parsing/binding, STOP-on-expiry and pre-scan/pre-plan/pre-send checks; preserve pending rows. Reject changed/removed deadline on restart, check wall time after sleep and cap this process with a monotonic remaining budget.
- [ ] Verify expired run cannot start Observer, expired unpause cannot clear STOP, and final Desktop send is bounded by the same deadline. Existing cycle guards remain; no Windows backend changes or new UI test.
- [ ] Independently collect stable real inputs since the last actual business scan, deduplicate against verified historical deliveries, inspect ZIP CRC and reports. Deliver initial analysis and a sanitized evidence package to the established Drive folder; only then advance exact processed versions and seed those delivered hashes.
- [ ] Review the final deadline diff with a controlled reviewer. Verify unique runtime, original target/cwd, retained old states/STOPs and paused legacy timer. Prepare a new bound real-input trial state, not replacement canary state; retain all original ledgers.
- [ ] Launch one hidden bounded worker with fixed config/deadline, record actual watching event/PID/start time and stop entry. Retain accepted/in-flight business; after verified Drive delivery the original task's caller may attest an ACK. No synthetic business answers.
- [ ] Publish sanitized startup report/evidence and updated WORK_LOG/current state to same Draft; reconcile own Hook source snapshot explicitly. Expiry performs no new dispatch/window action, writes STOP/expiry evidence, exits listener; no forced model termination.

## Review focus

Malformed/removed/extended deadline fails closed; expired restart or cleared STOP cannot revive the instance; clock rollback cannot extend the current process; expiry between planning and final send stops the action; accepted/uncertain rows and owned-cycle protections survive expiry. Tests cover these boundaries. Real missing-owner/UI recovery is outside this loaded-owner-only run mode.

Execution: local inline using executing-plans and TDD. Independent catch-up read/analysis is delegated with separate output ownership; parent integrates shared records and delivery. One controlled final deadline review, not Alice acceptance.
