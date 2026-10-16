# Desktop IPC adapter implementation plan

Actor: Kelan, local Windows. Class C / enhanced. Spec: [approved bounded trial](IPC_ADAPTER_TRIAL_20261003.md), handed off at `678f6366b5f56e25f98e78a699420d2a89419090`. Implementation proceeds inline under that authorization; Alice acceptance remains pending.

Goal: retain the existing file-condition/SQLite core, isolate chat contracts, and test one synthetic batch against the configured original Desktop chat. Keep the existing periodic mechanism.

Architecture: `trigger.py` owns planning, immutable snapshots, send intent, terminal ACK and retry decisions. `chat_adapters.py` owns a small inspect/observe/prepare/send/close contract and the existing JSONL queue backend. `desktop_ipc.py` owns the Windows named pipe, owner discovery, fixed protocol versions, trusted installation checks and bounded target-rollout observation. No plugin registry or service framework.

## Constraints and review focus

- One accepted or uncertain real send; no automatic replay, steering, interruption, forced resume, settings mutation, app restart or upgrade.
- IPC accepted/start/completion remain distinct; no fabricated queue submission. Busy, absent, unknown or incompatible targets leave local batches intact.
- Omit model, cwd, approval, sandbox and permission overrides. Use the installed owner's verified settings-inheritance path.
- Pin sources, preserve original Windows failure evidence, and keep private IDs/paths/chat records out of public commits.
- Tests must cover wrong target/owner, ambiguity after an acknowledgement is lost, unrelated notifications and context records, source truncation, STOP and stale ACK updates.

## Task 1: Separate the chat contract without changing queue behavior

Files: `trigger.py`, new `chat_adapters.py`, `tests/test_review_regressions.py`.

- [x] Apply only the already reproduced SQLite test-connection close fix and establish the Windows baseline (43 pass, one platform skip expected).
- [x] Move JSONL transport and queue-specific inspection/correlation behind the adapter. Preserve imported compatibility names used by existing tests.
- [x] Keep send intent and delivered-row protection in the core. Add nullable `dispatch_meta` for backend receipt context and bind each database to one adapter; old databases default to JSONL.
- [x] Verify the unchanged queue, ACK-race, deadline, scanner and watcher contracts with the existing suite.

Contract: `inspect(row)` returns `{can_send, reason}`; `observe(row)` returns a state/identifiers/detail mapping or `None`; `prepare(row)` returns serializable pre-send metadata; `send(row, text, metadata)` returns a receipt; `close()` releases only owned resources. `NotDispatched` means a provably pre-send refusal; exceptions after a write remain uncertain.

## Task 2: Add the minimum Windows IPC backend

Files: new `desktop_ipc.py`, `tests/test_desktop_ipc.py`, `tests/test_chat_adapters.py`, `example.windows-ipc.json`.

- [x] Observe failing configuration/core-boundary assertions before implementing the new behavior.
- [x] Implement bounded length-prefixed messages with absolute deadlines; inspect the named-pipe server process and its signed Desktop installation. Record package bytes/hash separately from the required method versions.
- [x] Discover only the configured conversation owner. Inspect exact rollout identity/cwd and lifecycle; unknown is not idle. Before sending, recheck the source baseline and STOP. Persist the baseline, request ID and owner with the send intent.
- [x] Send only `thread-follower-start-turn` v2 with inherited settings; an acknowledged native turn is `accepted`, with no queue ID. Observe only the same target/turn and retained fixed prompt; ambiguous history remains uncertain.
- [x] Verify busy/unloaded/unavailable behavior, no replay after uncertainty, settings omission, wrong owner/turn rejection, bounded protocol reads, unrelated events and source replacement/truncation with labeled local fixtures.

## Task 3: Bounded real trial and review handoff

- [ ] Query the current trusted installation and exact existing target read-only. Confirm idle and no active writer immediately before dispatch; the private protocol has no atomic idle compare-and-set.
- [ ] Watch an isolated input; write one synthetic file with a unique marker and known arithmetic content. Use the immutable manifest/blob, one batch and one actual submission. Ask the original chat to use its existing read tool and return the marker/result only, with no business or external writes.
- [ ] Correlate acceptance, native turn, real tool result and final answer. Verify actual settings and only naturally applicable existing Hook evidence; mark uncovered claims explicitly.
- [ ] Independently validate the synthetic result, save a private local receipt and apply a synthetic-only ACK. Reintroducing identical bytes must not create another delivery. Stop the owned watcher.
- [ ] Preserve raw evidence privately, publish minimal anonymous results and maintenance costs, run the relevant final regression, and request one controlled final review under the execution skill. Update this Draft PR with a non-force English commit and Chinese handoff. No Ready/merge or deployment.

Maintenance record: count changed production/test files and lines, list relied-upon IPC methods/versions and schema fields, record actual adaptation work and failures. Current-package success does not establish future-version compatibility.

## Execution disposition

Tasks 1 and 2 implemented and verified. Task 3 reached actual pipe/owner inspection and the single synthetic native-file capture, then stopped before dispatch: real target history contains unresolved overlapping lifecycle. Initial idle interpretation was withdrawn. No original-chat turn/tools/result/ACK is claimed. Watcher stopped, batch ready with STOP, original mechanism retained. Controlled final review found and closed three code defects; see the trial report. The real-send, result and synthetic ACK checkboxes deliberately remain incomplete.
