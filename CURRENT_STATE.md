# Current state

Status: implementation_ready / review_pending; experimental candidate, PR Draft. No merge, installation or production adoption. Alice accepted earlier single IPC/watcher and supervised open/minimize stages only; the new window cycle awaits her review.

## Latest implementation and evidence — 2026-10-08

Input b8225af531d6da73f69dbd7dfc7d88a6b769f443. Default-off per-batch window lifecycle now precedes dispatch in the single watcher worker: idle reuse, busy wait, explicit owner absence only for open, delivered + correlated completion before owned-window cleanup. Unknown opens/closes remain durable; legacy lifetime claims require explicit reconciliation. Exact batch binding prevents concurrent ACK from advancing to another batch before cleanup; unresolved acceptance must acquire turn correlation before cycle ACK. Disabling loading cannot bypass an unclosed cycle.

Windows UIA backend completed one explicitly supervised loaded-target open/minimize/normal-close test, followed by a second automatic watcher batch. Actual 2 starts, 0 manual dispatch, 2 caller-verified synthetic receipts; total 204.359 seconds. Closing the created window left owner available, so batch 2 reused it. Main chat was unchanged at recorded open/close checks; app and watcher continued between batches. No cold recovery was simulated or claimed.

119 tests: 118 passed, one Windows symlink privilege skip. 42 real-evidence assertions passed. Local controlled code review found and closed ACK scheduling/correlation problems; review is not Alice acceptance. A final per-action supervision expiry check was added after the live trial and checked in isolation, with separate live/final source hashes; no additional model/window trial after that change.

## Material limits

UIA exposes initialRoute, not independently authenticated current thread identity. Title cannot rule out same-title navigation or staleness. Backend is therefore restricted to an explicitly supervised no-navigation interval of at most 600 seconds and remains default-off. Arbitrary-navigation unattended closure is unresolved, not accepted.

New window was foreground; invoke-to-minimize sample interval 8.552924 seconds. The immediate post-minimize foreground sample still named the new HWND despite IsIconic=true. Neither zero focus nor focus restoration latency is verified. Current original owner was already loaded; cold recovery, ownership transfer, last-window behavior, long-running business, future versions/languages/DPI are unvalidated. Business ACK remains caller verification; this test does not accept real business delivery.

## Records and next review

- [Detailed report](docs/KELAN_WINDOW_CYCLE_20261008.md)
- [Sanitized evidence and source hashes](evidence/window-cycle-20261008.json)
- [Alice input handoff](docs/ALICE_WINDOW_CYCLE_HANDOFF_20261008.md)
- [Tests](evidence/window-cycle-tests-20261008.txt) and [supervisor](evidence/window-cycle-supervisor-20261008.py)

Alice should judge the bounded two-batch supervised cycle separately from unresolved unattended current-route and focus requirements. Original timer remains PAUSED; both historical canary STOPs and this trial STOP remain. Existing business state, Hook config and binding unchanged. No further live work is running.
