# Current state

- Goal: stable new file content gates work in the explicitly selected original Desktop chat.
- Workflow: Alice code review REQUEST CHANGES on implementation `93d84fdd4be5d6ed7b9ea9317a3326489a12a41b`; Draft / review_pending, no release or deployment.
- Handoff input: 678f6366b5f56e25f98e78a699420d2a89419090. This candidate splits core and chat contracts and implements an experimental Windows IPC backend.
- Current Windows tests: 69 methods, 68 pass and 1 Windows symlink condition skip. Historical original Windows failure evidence remains unchanged; see the trial report.
- Actual connection: current signed Desktop 26.930.3930.0, pipe server, initialization and exact target owner verified. The initial idle claim was withdrawn after the observer overlap counterexample.
- Real trial outcome: not_dispatched. An unresolved historical lifecycle overlap prevents a verified idle decision. No actual start-turn, native tool execution, canary result or delivery ACK occurred.
- Synthetic input: one real native-watcher capture, one immutable ready batch, stopped watcher and persistent local STOP. Original chat identifiers, input and state remain private.
- Safety corrections: reject overlap/duplicate lifecycle; host-check subprocess failures retain local processing; pending Windows I/O cancels and drains on interruption. Three controlled reviewer findings closed at code level.
- State: database bound to an adapter; nullable dispatch metadata migration; accepted distinct from queued/completed/delivered; no replay after accepted or uncertain writes; terminal ACK remains atomic.
- Next: fix malformed-reply fault isolation; first check whether an unrecognized terminal event explains the local history overlap. If ambiguity remains, verify a minimal native current-state snapshot, then continue the same authorized one-send canary when the target is demonstrably idle. Preserve history and the intended original target.
- Unverified: real original-chat dispatch, effective settings, native tools/Hooks, canary result, external business delivery, update tolerance and sustained operation.
- Existing periodic mechanism remains. No Ready/merge, forced resume/restart/update, permission mutation, service or autostart.

- Alice's cloud subset: 23 pass / 1 Windows skip, plus one watcher test excluded (watchdog unavailable); synthetic probes reproduce the reply-shape gap and reference-event coverage discrepancy. Neither proves the Windows root cause or native end-to-end success. See [Alice's review](docs/ALICE_IPC_REVIEW_20261004.md).

Read [Kelan's trial report](docs/KELAN_IPC_TRIAL_20261004.md), [adapter contract](docs/IPC_ADAPTER.md) and [WORK_LOG.md](WORK_LOG.md).
