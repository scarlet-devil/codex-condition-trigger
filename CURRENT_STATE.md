# Current state

- Goal: stable new file content gates work in the explicitly selected original Desktop chat.
- Workflow: implementation_ready candidate / Alice review_pending; Draft PR, no release or deployment.
- Handoff input: 678f6366b5f56e25f98e78a699420d2a89419090. This candidate splits core and chat contracts and implements an experimental Windows IPC backend.
- Current Windows tests: 69 methods, 68 pass and 1 Windows symlink condition skip. Historical original Windows failure evidence remains unchanged; see the trial report.
- Actual connection: current signed Desktop 26.930.3930.0, pipe server, initialization and exact target owner verified. The initial idle claim was withdrawn after the observer overlap counterexample.
- Real trial outcome: not_dispatched. An unresolved historical lifecycle overlap prevents a verified idle decision. No actual start-turn, native tool execution, canary result or delivery ACK occurred.
- Synthetic input: one real native-watcher capture, one immutable ready batch, stopped watcher and persistent local STOP. Original chat identifiers, input and state remain private.
- Safety corrections: reject overlap/duplicate lifecycle; host-check subprocess failures retain local processing; pending Windows I/O cancels and drains on interruption. Three controlled reviewer findings closed at code level.
- State: database bound to an adapter; nullable dispatch metadata migration; accepted distinct from queued/completed/delivered; no replay after accepted or uncertain writes; terminal ACK remains atomic.
- Next research: establish a verified read-only native owner state snapshot and concurrency contract before reconsidering the same-target single-send canary. Do not bypass history ambiguity or silently use another chat.
- Unverified: real original-chat dispatch, effective settings, native tools/Hooks, canary result, external business delivery, update tolerance and sustained operation.
- Existing periodic mechanism remains. No Ready/merge, forced resume/restart/update, permission mutation, service or autostart.

Read [Kelan's trial report](docs/KELAN_IPC_TRIAL_20261004.md), [adapter contract](docs/IPC_ADAPTER.md) and [WORK_LOG.md](WORK_LOG.md).
