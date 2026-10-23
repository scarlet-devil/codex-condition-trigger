# Current state

Updated 2026-10-24 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

**Section 11 has now been executed locally once. The same dedicated target accepted one ordinary new turn; before/during/after samples were idle, busy, idle, with correct binding, fresh revisions 8/14/16 and final owner checks. Limited G0 evidence is ready for Alice review; G0 is not self-approved.** See the [Windows report](docs/KELAN_REPRESENTATIVE_TASK_20261024.md), [evidence](evidence/kelan-representative-task-20261024.json) and [manifest](evidence/kelan-representative-task-manifest-20261024.json).

The 2026-10-24 01:10:11–01:14:07 Asia/Shanghai window closed after 236.156 seconds. Exactly one start attempt/write and one model turn, three metered samples and two additional adapter state reads occurred: five full-history requests total, four protocol initialize handshakes, eight owner discoveries. No unknown request write, extra initialization model turn, new chat, Tk retest, window action or sample retry. Existing creation/catalog/rollout binding and the fixed installation passed; all 188 candidate files and six frozen wrapper files remained unchanged.

Maximum target snapshots were 8,972 / 18,018 / 53,036 B; completed RX 29,075 / 56,214 / 161,566 B. The after-minus-before changes were 44,064 and 132,491 B respectively. Installation/IPC costs are separately reported. The 32 MiB frame / 128 MiB meter cumulative RX / 10-second IPC-after-verification limits were retained. This is still the full-history path with installation hashing, not a thin endpoint or a long-term polling-cost guarantee. The adapter does not inherit the meter cumulative RX contract.

Exact native receipt turn, persisted intent and full dispatch text matched; isSteering=false and inherited settings were retained. The lifecycle reader found task_complete/ended but still reported execution_outcome=unknown. Independent output checks matched all five frozen synthetic expectations; business ACK remained false. One target tool attempt failed to launch the WindowsApps Python alias (ResourceUnavailable, exit 1); the same model turn then used PowerShell successfully. Controller Python and IPC route did not change and no second turn was sent. Section 11's tool-change boundary and this interpreter fallback are explicitly left for Alice's scope review, not hidden or retrospectively accepted. Snapshot growth includes that failed tool record.

Fifteen wrapper checks passed after preserving red cases for sequence, outer deadline/STOP and exact message correlation. An independent local S1/M0 reviewer accepted the frozen wrapper, without running real IPC or claiming Alice/S2 status. Prior accepted 34 experimental / 55 Windows checks were not rerun because product sources were unchanged. Installation hashing is not force-interrupted at the outer deadline; new IPC is denied after late return. Local STOP cannot cancel an already accepted host turn.

Alice's prior cwd-current-state and independent Tk acceptance remains. G0 concerns discovery/binding/bounded state only; G1 rules/notify, G2 full form and G3 two-batch notifications are separate future stages, not added G0 prerequisites. One observed busy state does not prove queued-batch deferral, and idle/start is still non-atomic. Package/signing/recovery and endpoint research stay shelved. Production installation/configuration, business ACK, continuous authorization and historical STOP/expiry/PAUSED are unchanged; listener health was not checked. Section-11 allowance is closed. PR #2 remains Draft/unmerged; await Alice review before the next bounded stage.

## Accepted implementation baseline

Human approved preparing the human README and AI entry files, then merging [PR #1](https://github.com/scarlet-devil/codex-condition-trigger/pull/1), on 2026-10-20 at 20:50 Asia/Shanghai. Alice's preceding assessment supports merging the implemented version while retaining its operational limits.

**Implementation accepted and merged.** PR #1 merged on 2026-10-20 as `5c1882c7b78fc023d0588953e6e43db55ebe216d`; its [final receipt](https://github.com/scarlet-devil/codex-condition-trigger/pull/1#issuecomment-6291604544) records that closeout. Deployment is a separate state. Historical Draft labels for PR #1 are not current; the new design is a separate Draft change.

Runtime/test baseline: `95a6e9f7765bea2e308a99308c7d9488e4b477e0`. The 2026-10-20 closeout changed documentation and evidence only. The deployed implementation is not changed by this Draft. The Draft now includes fixed diagnostics, primary/cleanup error separation and shared restricted cwd representation support across the IPC, rollout, collector and experimental catalog. The installed baseline is unchanged; accurate thread/owner/revision and send/ACK contracts remain in effect.

## Accepted scope

| Area | Current conclusion and source |
| --- | --- |
| File-triggered dispatch | Real Windows automatic two-batch supervised trials accepted within their recorded scope: [window review](docs/ALICE_WINDOW_CYCLE_REVIEW_20261008.md), [owner recovery acceptance](docs/ALICE_OWNER_REUSE_RECOVERY_REVIEW_20261008.md). |
| Watcher health and real login | Progress/stale/exit reporting implemented. Kelan's real dry login trial passed; Alice checked the supplied script, hashes and summary, without claiming direct Windows observation: [login report](docs/KELAN_REAL_LOGON_ACCEPTANCE_20261016.md). |
| Native execution outcome | Automatic collection implemented, exact native bindings reviewed, loaded-chat IPC read validated. Original production target business acceptance remains pending. |
| Upload recovery | Existing Hub integration installed by Kelan under separate approval. Real Drive client-receipt-loss recovery accepted; Alice independently read back the existing canary bytes. [Actual local result](docs/KELAN_HUB_LIVE_ACCEPTANCE_20261016.md). |
| Accepted baseline full regression | 185 tests: 184 passed, one Windows-only overlapped-I/O test skipped, zero failures/errors. Frozen Hub included; all three outbox-to-Hub tests ran. [Validation](evidence/alice-merge-validation-20261020.json). |

[2026-10-16 review](docs/ALICE_INTEGRATION_REVIEW_20261016.md) records the limited APPROVE and evidence attribution. Its historical 183-pass/one-fixture-failure run remains accurate for that date; the 2026-10-20 full run supersedes the old outstanding full-suite rerun.

## Operational limits

- The former production trial expired on **2026-10-10 21:11:50 Asia/Shanghai**. This merge authorization does not clear its STOP/deadline or restart its PAUSED periodic task.
- `native_result_collection` and window loading remain default-off. A new live run needs an accurately bound configuration and current authorization.
- Window actions require explicit no-navigation supervision for at most 600 seconds; unattended cleanup after arbitrary navigation is unvalidated.
- A model turn ending is not business delivery. Only verified evidence supports ACK; preserve the existing ledger and receipt.
- Hub startup after reboot was restored manually. The dry login trial does not establish automatic recovery of the complete upload chain.
- Hub upload adapter: 8 MiB per file. Generic outbox: 20 MiB.
- Separate login, synthetic-provider crash and real Drive receipt-loss experiments are not one complete unattended production run.

## Follow-up scope

The current design is [SIMPLE_SETUP_DESIGN.md](docs/SIMPLE_SETUP_DESIGN.md). Prior cwd/Tk acceptance remains; the section-11 representative experiment is now completed and closed, with new evidence awaiting Alice review for limited G0 and the target interpreter-fallback scope. Do not reuse its one-turn/three-sample allowance. If accepted, define G1 notification scheduling next; G2/G3 remain separate. The following earlier deployment/community choices also remain separate:

1. If requested, bind and validate the original target's complete business workflow.
2. If continuous unattended operation is requested, determine and validate Hub startup/recovery with the rest of the chain.
3. For community reuse, the maintainer still needs to choose a project license. No project LICENSE exists at this checkpoint.

These are follow-up choices, not hidden blockers to the authorized code merge. The withdrawn 15-minute/one-turn/one-upload proposal is not an active task or acceptance requirement.

Six unresearched input versions and two missing Library originals belong to the historical research backlog; they are not evidence that the trigger implementation is incomplete. The cloud research automation is a separate workflow and is not reconfigured here.

## Entry points and provenance

- Users: [English README](README.md) / [中文 README](README.zh-CN.md).
- AI/contributors: [AGENTS.md](AGENTS.md).
- Decisions and full incremental history: [WORK_LOG.md](WORK_LOG.md).
- The previous long status snapshot is preserved at [the exact pre-merge input](https://github.com/scarlet-devil/codex-condition-trigger/blob/95a6e9f7765bea2e308a99308c7d9488e4b477e0/CURRENT_STATE.md). Read it for provenance, not fresh execution authority.
- Actor attribution: Alice performed the cloud documentation/code reviews and candidate changes recorded in WORK_LOG, including the shared cwd implementation and earlier Linux/simulated checks. Kelan performed the Windows investigations, dedicated-chat creation, cwd diagnosis, independent Tk smoke and 2026-10-24 same-target query. This latest Alice review checked published evidence and prepared the next bounded scope; it did not repeat Windows execution, tests or live sends. Historical records retain their original authors, dates and limits.

2026-10-24 execution attribution: Kelan owns the new Windows representative-task result and wrapper checks. Alice has not yet reviewed this new round. Prior review and test attribution is preserved; no production acceptance is inferred.
