# Current state

Status: changes_requested; experimental candidate, PR Draft. Alice accepts the recorded bounded two-batch supervised path, but requests one pre-send owner-recovery fix in input 2622fd65ae37c122cf4d563d5758757a560e569b. No merge, installation or production adoption.

## Latest implementation and evidence — 2026-10-08

Input b8225af531d6da73f69dbd7dfc7d88a6b769f443. Default-off per-batch window lifecycle now precedes dispatch in the single watcher worker: idle reuse, busy wait, explicit owner absence only for open, delivered + correlated completion before owned-window cleanup. Unknown opens/closes remain durable; legacy lifetime claims require explicit reconciliation. Exact batch binding prevents concurrent ACK from advancing to another batch before cleanup; unresolved acceptance must acquire turn correlation before cycle ACK. Disabling loading cannot bypass an unclosed cycle.

Windows UIA backend completed one explicitly supervised loaded-target open/minimize/normal-close test, followed by a second automatic watcher batch. Actual 2 starts, 0 manual dispatch, 2 caller-verified synthetic receipts; total 204.359 seconds. Closing the created window left owner available, so batch 2 reused it. Main chat was unchanged at recorded open/close checks; app and watcher continued between batches. No cold recovery was simulated or claimed.

119 tests: 118 passed, one Windows symlink privilege skip. 42 real-evidence assertions passed. Local controlled code review found and closed ACK scheduling/correlation problems; review is not Alice acceptance. A final per-action supervision expiry check was added after the live trial and checked in isolation, with separate live/final source hashes; no additional model/window trial after that change.

## Alice review — one required recovery fix

[Review and scoped handoff](docs/ALICE_WINDOW_CYCLE_REVIEW_20261008.md): 39/39 existing focused tests passed on cloud Linux. One additional synthetic counterexample fails: an idle owner is recorded as reused, then disappears before dispatch; the ready batch has no send intent or window lease, yet the active-cycle branch waits forever instead of claiming its first open. This persists after restart and a new file. Zero extra sends/windows occurred.

Kelan should permit one durable reused-to-opening transition only for the same never-dispatched, never-opened batch after definite absence. Preserve busy/unknown, sent-intent and unknown-action protections. Bring back the regression and affected tests; no full Windows replay is required for a Python-only fix. The native two-batch result remains accepted within its reported supervision limits; source acceptance is changes_requested until F1 is resolved.

## Material limits

UIA exposes initialRoute, not independently authenticated current thread identity. Title cannot rule out same-title navigation or staleness. Backend is therefore restricted to an explicitly supervised no-navigation interval of at most 600 seconds and remains default-off. Arbitrary-navigation unattended closure is unresolved, not accepted.

New window was foreground; invoke-to-minimize sample interval 8.552924 seconds. The immediate post-minimize foreground sample still named the new HWND despite IsIconic=true. Neither zero focus nor focus restoration latency is verified. Current original owner was already loaded; cold recovery, ownership transfer, last-window behavior, long-running business, future versions/languages/DPI are unvalidated. Business ACK remains caller verification; this test does not accept real business delivery.

## Records and next review

- [Alice review and recovery counterexample](docs/ALICE_WINDOW_CYCLE_REVIEW_20261008.md)
- [Detailed local report](docs/KELAN_WINDOW_CYCLE_20261008.md)
- [Sanitized evidence and source hashes](evidence/window-cycle-20261008.json)
- [Alice input handoff](docs/ALICE_WINDOW_CYCLE_HANDOFF_20261008.md)
- [Tests](evidence/window-cycle-tests-20261008.txt) and [supervisor](evidence/window-cycle-supervisor-20261008.py)

Alice has reviewed the bounded two-batch cycle separately from unattended current-route and focus limits. Next action is the single F1 repair and focused review; these wider product limits are not additional repair gates. Original timer remains PAUSED; both historical canary STOPs and this trial STOP remain. Existing business state, Hook config and binding unchanged. No further live work is running.
