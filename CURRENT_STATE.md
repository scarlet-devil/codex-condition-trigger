# Current state

Status: experimental candidate / Draft. The prior single IPC trial has bounded Alice acceptance; the new supervised automatic watcher trial is implementation_ready / Alice review_pending. No merge or production adoption.

## Latest supervised evidence — 2026-10-08

At input commit 05864a467d12b1480bdb901d2f0ae1d27dc84e12, one synthetic file was captured by WindowsApiObserver, stabilized and automatically dispatched by the unchanged live watcher into the exact original chat. One native start, zero manual dispatch calls. Actual tool reads and hashes, 173+284=457, native completion and inherited settings passed 27/27 evidence assertions. Synthetic ACK followed caller verification; post-stop duplicate-byte scans retained one batch. Watcher exited at 101.188 seconds and STOP was retained.

Opening the exact original chat was a prerequisite: after restart it was notLoaded and owner discovery returned no-client-found. The generic method/owner mismatch exception did not accurately name this condition. The operator opened the chat using native UI; current idle was then proven. No autonomous unloaded-chat recovery was added or accepted.

[Trial report](docs/KELAN_SUPERVISED_WATCH_TRIAL_20261008.md) and [sanitized evidence](evidence/supervised-watch-trial-20261008.json) record the limits and provenance. Product/test source is unchanged; historical test counts are not new runs.

## Boundaries and next decision

- Suitable candidate for bounded supervised use with the target already loaded and idle; not an unattended business monitor.
- Original timer remains Human-paused; previous and current canary STOP markers remain. No watcher is left running.
- Sustained operation, real business/external delivery, concurrent actors, unloaded-chat startup and future Desktop versions remain unaccepted.
- Alice should review this specific automatic watcher-to-turn evidence. No further trial, model turn or adoption begins automatically.

## Prior records

- [Alice acceptance of prior single IPC stage](docs/ALICE_IPC_ACCEPTANCE_20261008.md).
- [Prior native IPC canary](docs/KELAN_IPC_CANARY_20261006.md).
- [Runtime recovery and readiness](docs/KELAN_STATUS_AND_RECOVERY_20261008.md).
- [Complete work log](WORK_LOG.md).
