# Current state

Status: F1 accepted by Alice on 6c2589d7d100d135c1f5deb301268929d0b375c8. Original probe independently red/green; 46/46 focused checks pass. Previously accepted supervised two-batch evidence is preserved; PR Draft, no unattended acceptance, merge or deployment.

## Latest implementation and evidence — 2026-10-08

Input b8225af531d6da73f69dbd7dfc7d88a6b769f443. Default-off per-batch window lifecycle now precedes dispatch in the single watcher worker: idle reuse, busy wait, explicit owner absence only for open, delivered + correlated completion before owned-window cleanup. Unknown opens/closes remain durable; legacy lifetime claims require explicit reconciliation. Exact batch binding prevents concurrent ACK from advancing to another batch before cleanup; unresolved acceptance must acquire turn correlation before cycle ACK. Disabling loading cannot bypass an unclosed cycle.

Windows UIA backend completed one explicitly supervised loaded-target open/minimize/normal-close test, followed by a second automatic watcher batch. Actual 2 starts, 0 manual dispatch, 2 caller-verified synthetic receipts; total 204.359 seconds. Closing the created window left owner available, so batch 2 reused it. Main chat was unchanged at recorded open/close checks; app and watcher continued between batches. No cold recovery was simulated or claimed.

119 tests: 118 passed, one Windows symlink privilege skip. 42 real-evidence assertions passed. Local controlled code review found and closed ACK scheduling/correlation problems; review is not Alice acceptance. A final per-action supervision expiry check was added after the live trial and checked in isolation, with separate live/final source hashes; no additional model/window trial after that change.

## Alice focused follow-up — F1 accepted

[Review and scoped handoff](docs/ALICE_WINDOW_CYCLE_REVIEW_20261008.md): 39/39 existing focused tests passed on cloud Linux at 2622fd6. An additional synthetic counterexample failed on that input: an idle owner is recorded as reused, then disappears before dispatch; the ready batch has no send intent or window lease, yet the active-cycle branch waits forever instead of claiming its first open. That failure persisted after restart and a new file. Zero extra sends/windows occurred.

Kelan implemented the same-batch reused-to-opening promotion with a cycle-snapshot compare-and-swap and atomic ready/no-send-intent predicate. Only never-opened reused history with no lease qualifies after fresh definite absence. Original probe changes from exit1/0 opens/0 sends to exit0/1 open/1 send. Seven new checks bring the affected modules to 46/46 pass. Python-only; Windows backend and prior native evidence unchanged. See [repair report](docs/KELAN_OWNER_REUSE_RECOVERY_20261008.md) and [red/green evidence](evidence/owner-reuse-recovery-20261008.json). Alice independently reproduced the unchanged probe red/green and passed all 46 focused checks in cloud Linux (0.180 seconds). The atomic same-batch promotion and retained protections are accepted, with no new required fixes. See [Alice follow-up and evidence](docs/ALICE_OWNER_REUSE_RECOVERY_REVIEW_20261008.md).

## Material limits

UIA exposes initialRoute, not independently authenticated current thread identity. Title cannot rule out same-title navigation or staleness. Backend is therefore restricted to an explicitly supervised no-navigation interval of at most 600 seconds and remains default-off. Arbitrary-navigation unattended closure is unresolved, not accepted.

New window was foreground; invoke-to-minimize sample interval 8.552924 seconds. The immediate post-minimize foreground sample still named the new HWND despite IsIconic=true. Neither zero focus nor focus restoration latency is verified. Current original owner was already loaded; cold recovery, ownership transfer, last-window behavior, long-running business, future versions/languages/DPI are unvalidated. Business ACK remains caller verification; this test does not accept real business delivery.

## Records and remaining scope

- [Alice review and recovery counterexample](docs/ALICE_WINDOW_CYCLE_REVIEW_20261008.md)
- [Detailed local report](docs/KELAN_WINDOW_CYCLE_20261008.md)
- [Sanitized evidence and source hashes](evidence/window-cycle-20261008.json)
- [Alice input handoff](docs/ALICE_WINDOW_CYCLE_HANDOFF_20261008.md)
- [Tests](evidence/window-cycle-tests-20261008.txt) and [supervisor](evidence/window-cycle-supervisor-20261008.py)

Alice has reviewed the bounded two-batch cycle separately from unattended current-route and focus limits. F1 repair is accepted and this scoped review is complete. Any next implementation stage has a separate scope; these wider product limits are not additional F1 repair gates. Original timer remains PAUSED; both historical canary STOPs and this trial STOP remain. Existing business state, Hook config and binding unchanged. No further live work is running.
