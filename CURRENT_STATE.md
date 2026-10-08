# Current state

Status: experimental candidate / Draft. Alice accepts both the prior single IPC trial and the 2026-10-08 supervised automatic watcher trial within their recorded scopes. No merge or production adoption.

## Latest accepted evidence — 2026-10-08

At input 05864a467d12b1480bdb901d2f0ae1d27dc84e12, one synthetic file was captured by WindowsApiObserver, stabilized and automatically dispatched by the unchanged live watcher into the exact original chat. One native start, zero manual dispatch. Local actual-tool/hash checks, 173+284=457, native completion and inherited settings passed the recorded 27/27 evidence assertions; caller verification preceded synthetic ACK. The external supervisor requested normal watcher shutdown at about 101 seconds; its one-send/deadline guards are trial controls, not new product features.

Alice reviewed final evidence 4de66f288210f9410d3f3f5c17f00fd85de33734 and accepts this loaded-and-idle, single-file automatic watcher-to-turn result. Native evidence review is S2-M0; private raw Windows evidence was not reread in the cloud, and no application tests or native trial were rerun. See [Alice's review and next direction](docs/ALICE_SUPERVISED_WATCH_REVIEW_20261008.md), [local report](docs/KELAN_SUPERVISED_WATCH_TRIAL_20261008.md) and [sanitized trial evidence](evidence/supervised-watch-trial-20261008.json).

## Owner availability and next work

After restart the target was notLoaded; discovery returned no-client-found. Opening the exact original chat restored owner/idle. This is an owner-lifecycle prerequisite; the generic method/owner mismatch text obscures it. The same class of problem occurred in earlier native communication work. Prior deep-link tests established navigation and foreground effects with an already-loaded target, not automatic cold recovery.

Latest Draft implementation: [owner diagnostic/waiting fixes and an explicit default-off loader interface](docs/KELAN_OWNER_LOADER_20261008.md). Final local suite: 101 tests, 100 pass, one environment skip. A bounded native read-only probe found the exact original target already idle; no new turn/window/load occurred. The new interface has no bundled window backend and is not connected to watcher auto-loading. Its code and evidence are implementation_ready / Alice review_pending; unattended exact-chat window recovery remains unimplemented and unaccepted.

Human's window preference: minimize manual interaction by scripting the same chat's dedicated-window opening and minimization; prefer native creation without foreground activation if a callable route exists. Existing reachable owners/windows should be reused. The native new-window entry and its current Windows behavior require local confirmation; standard handle-based minimization does not prove activation-free creation. See the review supplement. No window-automation script has been run in this cloud review.

## Latest research — exact deep link and window selection

The Human-supplied existing-chat ID is accepted by the installed UUID syntax and preserved in its internal /local route; a read-only app snapshot finds the exact local target. Normal deep links navigate the most recently active main/navigation window and do not request a dedicated one. Internal new-window messages explicitly show/focus; externally callable exact-window creation and HWND association remain unverified. A feature-gated sidebar Ctrl branch is a limited UI lead, not a verified title-click shortcut.

See [Kelan’s capability/limitations report](docs/KELAN_DEEPLINK_WINDOW_RESEARCH_20261008.md). Nine isolated checks passed; zero live navigation, UI input, window creation/minimization or new model turns. No runtime code changed. This research is review_pending and does not establish zero-focus creation, cold recovery or unattended adoption.

## Operating boundary

- Bounded supervised use requires the exact target to be loaded and proven idle.
- Sustained unattended operation, real business/external delivery, concurrent actors, unloaded-chat startup and future Desktop versions remain unaccepted.
- Original timer remains Human-paused; prior/current canary STOP markers remain. Local trial reports no watcher left running.
- No new trial, navigation, model turn, deployment or adoption was started by Alice's review.

## Prior records

- [Prior Alice single IPC acceptance](docs/ALICE_IPC_ACCEPTANCE_20261008.md).
- [Runtime recovery and readiness](docs/KELAN_STATUS_AND_RECOVERY_20261008.md).
- [Complete work log](WORK_LOG.md).
