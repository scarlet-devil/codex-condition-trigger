# Work log

## 2026-10-03 — Initial prototype

Actor: Alice, cloud execution. Scope: research existing Codex event triggers and build a bounded prototype where no directly verified Windows original-thread integration was available.

Compared Codex Triggers, chokidar-cdx and gnosis-container; inspected pinned OpenAI queue/protocol source. The design separates conditions, durable batches, queue acceptance and verified business delivery. Source references are public and listed in SOURCES.json.

Implemented watchdog events, stable content snapshots, SHA-256 deduplication, SQLite state, immutable blobs, single-worker locking, and an explicit original-owner JSONL adapter. Test doubles are labeled; no real Codex thread or model was invoked.

Validation: 33 tests passed in the initial cloud Linux run, including real inotify and restart recovery. Self-review fixed worker locking so ack/status can run concurrently and bounded file capture reads. This is same-context self-review (S0), not an independent local review.

## 2026-10-03 — Prepare public repository

Authorization: the user requested a public GitHub repository containing the trigger, its purposes and its main reference ideas.

Prepared a separate public source tree. Replaced private paths and the original thread ID with synthetic examples; removed private handoff references and deployment counts. Added public-facing use cases, design attribution, integration instructions and this project entry. Generalized task messages so the trigger does not require a particular project or delivery service.

The public tree's fresh regression output is evidence/test-results.txt. Publication state is tracked by the actual remote repository and Draft PR, not inferred from this preparation record.

Remaining work: actual Windows/Desktop integration, native tool preservation, external receipt integration and business retries. This public prototype does not claim to solve those deployment-specific gaps.

## 2026-10-03 — Start static-review corrections

Actor: Alice, cloud execution. Input: the static review of head `9c658d6bffb16c53e8838f8432ac1e1319b6da6b`, reporting an ACK/poll race, an RPC deadline gap for unrelated response IDs, and history matching based only on a batch marker. The current Draft PR still has that head; all 15 local files match its Git blobs before changes.

Scope: reproduce these three paths, make bounded corrections, add regressions, and update the existing Draft PR. The source review supports the findings; runtime reproductions are still pending at this entry. No Windows installation, real owner connection, model call, automation switch, or merge is part of this round.

## 2026-10-03 — Complete correction implementation and checks

Actor: Alice, cloud execution. Reproduced all three reported paths on the unchanged baseline: seven regression methods failed, with nine failed assertions including subcases. Added atomic terminal-state protection for ACK and its evidence, a uniform absolute deadline for response consumption, and persisted exact dispatch text tied to send intent. Legacy databases add a nullable column without inventing missing send evidence.

Validation: 44 tests passed (33 original method names plus 11 new methods). Deterministic ACK/RPC barriers verify all three stale-result branches and next-batch progress. Protocol tests cover wrong-ID floods, late valid responses, ordinary user references, restart correlation, ambiguity and legacy state. A real Linux watcher subprocess with a labeled JSONL test double exits after STOP despite unrelated response traffic. One original positive history fixture now uses the actual submitted text.

Evidence: docs/REVIEW_FIXES_20261003.md, evidence/review-20261003-before.txt and evidence/test-results.txt. Source and evidence hashes are refreshed together. This remains S0 self-verification; the external input was a static report, not a runtime acceptance. Next action is review of the correction head in the same Draft PR before any local integration trial. No merge or deployment is performed.

Artifact clarification: checked the author's original 29,661-byte ZIP (CRC passed, all 15 Git blobs match the initial head); saved evidence/initial-archive-verification.json. This does not establish recipient access to that archive. It is the initial version, not the corrected implementation; the correction PR head is the next review input.

## 2026-10-03 — Record Windows evidence and select an isolated IPC trial

Actor: Alice (cloud author/reviewer). Recipient: local Kelan responsible for this project's Windows checks. Human decision: record the alternatives and proceed with a bounded Desktop IPC experiment through a separate chat adapter. The implementation input remains `886755e8341e79174c4d047acca1aea86e6a35ea`; this entry changes documentation only.

Evidence carried forward from Kelan's `KELAN_TRIGGER_WINDOWS_ACCEPTANCE_20261003.md`, read by Alice: the unchanged Windows suite recorded 42 passes, one SQLite cleanup error and one skip; a cleanup-only diagnostic copy recorded 43 passes and one skip. The unchanged watcher passed 14/14 Windows native dry checks. These are transferred local results, not Alice reruns. Original Desktop dispatch, tools/Hooks and external delivery remain unverified in this project. Raw local paths, chat IDs and private reports stay in their existing private evidence location.

### Routes discussed and disposition

| Direction | Decision and reason |
| --- | --- |
| Periodic model checks | Retain the existing mechanism during the trial. The new core should avoid model calls when no new material exists; no production replacement yet. |
| OS file events + stable snapshots + durable batches | Keep the working core and its deduplication/ACK/recovery boundaries; Windows dry evidence is now recorded. |
| Official queue / original app-server / proxy | Keep as an explicit backend option where an original-owner endpoint is genuinely available. The inspected machine had no verified endpoint; a byte proxy alone does not supply the required handshake/framing. |
| Independent SDK with a paired CLI | A separate execution option with controllable runtime versions, but it does not meet this trial's original Desktop-chat requirement. No silent fallback. |
| Desktop private IPC | Selected for a bounded experiment behind the chat interface, using existing transport/owner-routing experience plus public protocol references. |
| Whole community remote-control packages or UI automation | Reference material, not an installation or replacement plan. A different wrapper does not by itself remove dependency on Desktop internals. |

Correction to the earlier investigation: Desktop IPC is not a newly discovered possibility. An earlier private integration had an accepted same-chat continuation result. Alice initially omitted that existing work; the current task is to evaluate reuse for this trigger/current installation, not prove that the path has never existed.

Historical update burden involved exact package-path/hash coupling, loaded-owner lifecycle, permission-state interpretation and an observer schema defect. Inspected updates sometimes left the used IPC contracts unchanged. The current record does not quantify what fraction of past effort was caused by updates or claim that all failures were protocol breakage.

### Chosen interface and evidence boundary

The trigger owns files, batches, local persistence and business ACK. A replaceable chat adapter owns target inspection, dispatch and correlated observation. Target absence or incompatibility pauses dispatch only; local observation and pending material remain usable.

Version/package hashes identify the environment and trusted installation; changes alone do not determine protocol failure. Compatibility is judged against the specific behavior relied upon: the correct original target, agreed dispatch semantics, retained settings, and identifiable acceptance/start/completion. Model/business failure is not automatically an IPC failure, and a plausible final answer alone is insufficient evidence.

The current queue-shaped calls and an IPC start-turn are different contracts. Map them explicitly; if IPC has no verified native queue, retain the batch locally while the target is busy. Do not invent a queue receipt, replay an uncertain send, or import legacy permission overrides. Ordinary updates must not automatically reopen unrelated completed work; actual incompatible behavior is handled within the adapter.

Next action: Kelan implements and tests [the bounded IPC trial](docs/IPC_ADAPTER_TRIAL_20261003.md), including a synthetic-file real-host check and necessary regressions. One-version success is not cross-version durability or production adoption. Existing scheduled work and real delivery records remain in place.

Publication/receipt: the exact documentation commit and handoff are recorded by the PR delivery comment after publication. This entry does not claim that Kelan has read it or begun execution.


## 2026-10-04 — Kelan implements adapter and reports pre-dispatch block

Actor: Kelan, local Windows; Human transferred the 678f636 handoff and approved bounded verification. Class C / enhanced. Takeover receipt was posted and read back on Draft PR #1. Work used an isolated clone; no existing development checkout was taken over.

Separated core from QueueAdapter and added experimental DesktopAdapter, immutable pre-send metadata and adapter-bound state migration. Preserved queue semantics and ACK/deadline/exact-text protections. Added explicit canary task configuration, local examples and public protocol licensing. No private integration code, raw chat, target identifier or secret is published.

Fresh Windows baseline after the already reproduced test-connection cleanup: 43 pass / 1 skip. Final candidate: 68 pass / 1 skip in 69 methods. One controlled local S1-M1 reviewer found three Important issues: overlapping lifecycle could falsely imply idle, subprocess host-check errors escaped the watcher, and interrupted overlapped I/O did not drain before releasing storage. Each was reproduced before correction; the same reviewer independently closed the three targeted regressions. A later watcher test additionally confirms subsequent input remains captured after a synthetic host-check failure. This is not Alice/S2 acceptance.

Actual named pipe/server signature/current method table, initialize and exact target owner query succeeded on Desktop 26.930.3930.0. Sandbox Access Denied and native PowerShell module-loading failures were recorded and diagnosed within the authorized read-only probe. The first probe's idle conclusion was invalidated by the overlap counterexample; it is explicitly withdrawn.

One synthetic file formed one immutable ready batch via native Windows watcher in about 1.219 seconds (60-second fallback interval). Watcher exited normally. The exact real target contains a historical unresolved overlapping start; fixed observer refuses to prove idle. No start-turn request was sent, no canary tool/result or business ACK was produced, and the synthetic state retains STOP. Existing periodic work remains. Limited source inspection shows the complete-history call returns revision and broadcasts a snapshot; that alone is not an established native idle contract, so no expanded stream adapter was attempted.

Report: docs/KELAN_IPC_TRIAL_20261004.md. Evidence: evidence/windows-ipc-tests-20261004.txt and windows-ipc-trial-20261004.json. Raw source/probe/rollout evidence remains private. Next recipient Alice should evaluate whether a narrow native snapshot contract resolves this observed ambiguity and warrants another bounded trial. Candidate implementation_ready; overall review_pending, Draft. No merge, production switch or forced lifecycle/settings action.

## 2026-10-04 — Alice reviews the IPC candidate and narrows follow-up

Actor: Alice, cloud reviewer. Exact implementation input: `93d84fdd4be5d6ed7b9ea9317a3326489a12a41b`; task ALICE_IPC_REVIEW_20261004. Read the shared entries, adapter/core sources, tests and Kelan's report. The supplied Drive report matches the public report. Local Windows connection and zero-dispatch facts remain transferred evidence; raw native state and local review traces were not independently inspected.

Ran the two adapter modules' bounded subset on cloud Linux/Python 3.12: 24 methods, 23 pass and one Windows-only skip. One watcher test was excluded because watchdog is unavailable here. Added synthetic review probes without changing candidate source. For Kelan's adapter changes this is a separate-subject, bounded-input S2-M1 review; native claims receive M0 evidence review. Alice's prior core authorship and S0 checks of her own probes are not relabeled as independent acceptance.

REQUEST CHANGES for a reproduced protocol-shape isolation gap: a null JSON frame raises AttributeError, and a malformed native success reply raises TypeError outside dispatch_one's controlled exception path. The latter leaves sending; restart correctly preserves uncertain and reconciliation does not resend. Live watcher termination is a source-control-flow inference, not a rerun in this environment. A second probe shows the pinned reference's turn_interrupted event is not recognized; whether it explains the real historical overlap is unverified.

Next: fix response-boundary validation and its affected isolation tests; check the actual minimal lifecycle slice before treating the missing event as the local root cause. If ambiguity remains, establish only the necessary original-owner current-state snapshot contract, separating current send eligibility from historical receipt correlation. No new global queue/stream framework or atomic-CAS gate is required for the already authorized isolated one-send trial. Retain unknown-state pause and no replay after an uncertain send.

See [the review and executable probes](docs/ALICE_IPC_REVIEW_20261004.md). This increment changes review documents/evidence only. No real IPC/model call, native setting/history change, merge or production switch. Draft remains review_pending; publication does not establish Kelan receipt.


## 2026-10-04 — Kelan fixes protocol isolation and verifies native current-state query

Actor: Kelan, local Windows. Human transferred Alice's exact 20a4fa1 review and same-batch trial scope. Complete review and takeover comment were read back. Class C / enhanced; no new authorization inferred from source contents.

Reproduced F1 at the JSON/object/identifier boundaries and after a simulated written request. Converted malformed replies to controlled errors; actual Windows watcher plus synthetic malformed IPC still captures subsequent files. Checked the exact target's minimal lifecycle evidence: zero turn_interrupted, so F2 does not explain its old overlap. No history edit or speculative terminal-event support was added.

Implemented only an exact-owner, exact-target temporary snapshot query correlated with a native history-query reply revision and verified cwd/resumed/runtime status. Installation source supports the fields and wire versions; real read-only probes at 02:00:31Z and 02:07:27Z returned busy with matching revisions 2 and 4. Receipt observation verifies immutable prefix and parses only post-baseline lifecycle; it does not need a live IPC connection. Current eligibility and historical correlation are separate.

Self-check fixed a second read-only query failure being classified uncertain despite no start write. A controlled S1-M1 local reviewer found one new nested runtime-type container escaping as TypeError; both list/dict cases were reproduced, fixed to unknown and independently closed. Final full Windows suite: 80 methods, 79 pass / 1 symlink privilege skip, 7.834 seconds. This is not Alice/S2 acceptance or end-to-end Desktop acceptance.

Same one ready synthetic batch, no persisted send intent, no actual start, no tool/result/ACK; STOP retained because current owner is busy. Original timer, target binding, permissions and installation remain. Added three private IPC method versions, no runtime dependency/service/autostart; bounded snapshot/history cost and final idle-to-write race disclosed. Report: docs/KELAN_IPC_REVIEW_FIXES_20261004.md, evidence/windows-ipc-r2-20261004.json and its test output. Candidate implementation_ready; Draft / review_pending; continue the authorized same-batch trial only with fresh verified idle. No merge or production switch.


## 2026-10-06 — Kelan completes the existing one-batch native IPC canary

Human explicitly resumed the bounded trial after stopping the target's previous work. Read and reconciled shared sources, confirmed the Human-paused timer, rechecked governance 17/17, unchanged implementation 087c228 and exact original input/batch with no prior intent. No production or test code changed; R2's source-bound 80-method result is reused, not relabeled as a rerun.

Real native state was idle at revisions 6/8/10. At 08:01:32 Asia/Shanghai, one start-turn was written and accepted by the exact original owner/chat. Its native turn completed at 08:06:35 (302607 ms), with three functions.exec calls containing six successful exec_command outputs. Actual read/hash evidence, marker and 137+209=346 result match the unique 89-byte blob. The 493-byte manifest matches pre-send database bytes. Prior/current model, effort, cwd, approval and sandbox settings match; no overrides were sent.

Same-turn UserPromptSubmit and developer continuity prompt were observed and read by the target. This proves delivery/response for this canary only, not general Hook effectiveness or a natural-budget sample. Target kept its paused actions and performed no source ACK. Caller validated the scoped native/rollout/tool/result evidence before synthetic delivered ACK; a same-byte rescan leaves one batch, no duplicate send. The prior Oct 4 watcher capture and this resumed dispatch are separate stages of the same durable batch, not a continuous latency result.

Private raw evidence and databases remain local; docs/KELAN_IPC_CANARY_20261006.md and evidence/windows-ipc-canary-20261006.json carry the sanitized result. The candidate stays Draft / Alice review_pending. Canary STOP and Human-paused original timer remain; no live watcher/service/autostart, production switch, settings/history rewrite or merge. The real trial is implementation_ready; business delivery, sustained operation, future-version compatibility and atomic idle-CAS remain outside acceptance.

## 2026-10-08 — Alice accepts the scoped single-run IPC trial

Actor: Alice, cloud reviewer; task ALICE_IPC_ACCEPTANCE_20261008. Exact evidence input 5159d4f9ca395b90ee5c7f23e1a4b657024ff042, unchanged implementation 087c228c791ff494b4c15ae9eeeabedf4e344cb2 (production c06bf0b). Read the shared entries and both local follow-up reports. Verified the documentation-only commit delta and equality of the Drive/public canary report. Seven test inputs match Git blobs and the candidate SHA-256 manifest; three R2 focus files also match its recorded source hashes.

Ran 14 focused contract tests on cloud Linux/Python 3.12.14; all passed. Close F1 for the originally reproduced reply-shape and uncertain-write cases. F2 was excluded as the local history cause by Kelan's target inspection, so it is no longer a follow-up gate. Reviewed native current-state correlation and baseline-relative receipt observation. Windows watcher/full-suite evidence remains transferred; no watchdog installation, Desktop call or model run occurred here.

Accept the bounded same-target, same-batch, single-dispatch synthetic trial based on Kelan's source-bound local report: actual tools/input/result/settings, same-turn completion, caller-verified synthetic ACK and no second dispatch. Private raw dispatch/turn/completion/database files were not supplied to this cloud review; their hashes were not independently recomputed. Code/contract review is scoped S2-M1, native report review S2-M0, own record checks S0.

This closes the one-run feasibility experiment, not the whole production project. The staged Oct 4 capture / Oct 6 dispatch is not continuous unattended operation. Preserve the reported Human-paused timer and canary STOP. A short supervised live watcher-to-dispatch run is an optional next-stage proposal, not launched or delegated by this review. No merge/Ready, deployment, business adoption, permission/history change or cross-version guarantee.

See [the scoped acceptance record](docs/ALICE_IPC_ACCEPTANCE_20261008.md) and its focused test output. Only review records/evidence change; publication does not establish Kelan receipt.
