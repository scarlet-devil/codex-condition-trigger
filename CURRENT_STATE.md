# Current state

Updated 2026-10-27 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

**G1 accepted by Alice (implementation and synthetic verification, 2026-10-24).** Exact reviewed input: `88dc1756d08a9f8a353628816a72ec7169f7718a`. Alice checked all 17 delivery files (376,659 B), their manifest/blob bindings and source/test contracts; independently ran the 36 new tests in Linux (all passed, no skips), the fake two-batch demo and critical Ruff rules. Notify sends B once after exact acceptance/terminal/fresh idle; strict still waits, and neither fabricates ACK. Kelan's Windows full suite remains attributed to him: 229 passed / 1 symlink-permission skip, plus 34 experimental passes; Alice did not rerun that full suite or the private Windows logs. Default Ruff findings remain disclosed. See [acceptance and G2 plan](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#13-当前接续g1-验收与-g2-表单测试设计) and [review evidence](evidence/alice-g1-review-20261024.json).

**G2 accepted by Alice (implementation and simulated transport workflow, 2026-10-24).** Exact reviewed input: `6c92f873c714697b423e5dcb8036f2fa57737a01`. Alice checked the 16 delivery files (342,418 B), 15 manifest payloads, ten source pins and the catalog/controller/Tk/shared-interface changes. In Linux / Python 3.12.14, Alice independently ran 27 G2 tests plus 36 affected G1 tests: all 63 passed with no skips; critical Ruff rules passed for ten files. Kelan's Windows full suite (256 passed / one symlink-permission skip) and final real Tk/fake two-batch smoke remain attributed to him. The first GUI failure and its uncertain batch are preserved. See [G2 acceptance](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#14-当前接续g2-验收与-g3-准备边界), [Alice evidence](evidence/alice-g2-review-20261024.json), [Kelan report](docs/KELAN_G2_FORM_20261024.md) and [usage](docs/SIMPLE_SETUP_G2.md). The first G3 attempt stopped before dispatch; the later batch-only run is now limited_accepted below.

**G0 is limited_accepted by Alice as of 2026-10-24.** The reviewed input is `92ecba6bb16899ac3e1cc71948997d5b7895874e`; Kelan executed the representative task from `09e36beafeb293b3b6263b7b856cb841ff3cc605`, with runtime source unchanged from `d55c62d204ba8193974b5434b19898dd65776a43`. Acceptance covers the fixed Windows Desktop installation, same accurately bound dedicated target and this workload: discovery/binding, bounded fresh state before/after work, observed busy state, ordinary new-turn receipt and exact terminal association. See the [local report](docs/KELAN_REPRESENTATIVE_TASK_20261024.md), [evidence](evidence/kelan-representative-task-20261024.json) and [Alice decision / G1 brief](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#12-当前接续g0-限定接受与-g1-实现).

The closed 01:10:11–01:14:07 Asia/Shanghai experiment lasted 236.156 seconds: one start/model turn, three meter samples plus two adapter state reads, five complete-history requests total. Samples were idle/busy/idle with revision/requested_revision 8/8, 14/14, 16/16 and unchanged final owners. Maximum target snapshots were 8,972 / 18,018 / 53,036 B; completed RX 29,075 / 56,214 / 161,566 B. Meter budgets remained 32 MiB frame / 128 MiB cumulative RX / 10-second IPC after installation verification. Adapter reads do not inherit the meter cumulative budget. No extra model initialization, new chat, Tk/window action or sample retry occurred.

The native receipt turn matched the persisted intent and exact terminal record, with isSteering=false and inherited settings. Lifecycle ended / execution_outcome=unknown remains accurate; Kelan's separate output checks matched all five expectations and business ACK stayed false. Alice accepts the disclosed target-task interpreter fallback: the WindowsApps Python alias failed to start, then the same turn used PowerShell for the same synthetic result. Controller Python, IPC, target, budget and start count did not change. The failed record stays in the evidence and measured growth. This closes the scope review; no machine repair or clean rerun is required.

Alice checked five public delivery files (188,865 B), four manifest entries, seven execution-module source pins, the 186 unchanged blobs and the preserved 150,413 B / 11 CRLF log prefix. Fifteen helper checks and local S1/M0 review remain Kelan-attributed results. Private helper sources, Windows logs and conversation evidence were not independently rerun/read in cloud. At that G0 review, prior 34 experimental / 55 Windows tests were reused within their unchanged-source scope without rerunning runtime tests. The separate G1 direct checks are listed above.

**Current handoff: G3 limited_accepted by Alice on 2026-10-27.** The fixed candidate is `018f7f8c2367aefb758ea001db78b589b76b5b6c`. Kelan's new batch-only Windows run completed in 113.969898 seconds, exit 0: A ran while B waited; exact A terminal plus fresh idle preceded B; each batch was sent once, received, ended and released. A/B outputs independently match all expected fields, including sums 311/2911. Start intents retained 466.730207/406.388740 seconds. Closed=true, enabled=false, backlog=0; no business ACK. GUI evidence is reused from the accepted R2 subset.

Alice verified the 116,414 B package, CRC and 62 payload hashes; nine code/test files match the fixed public candidate, 16 public source pins match its tree, and the 223-file snapshot path set matches. Alice independently recomputed A/B outputs, timeline ordering and the 62-frame/2,092,551 B receive accounting, and ran eight continuous-entry synthetic tests in Linux (all passed). Native private rollout/DB/owner evidence and Windows execution remain attributed to Kelan; they were not replayed in cloud. Existing code regressions are reused within unchanged scope. See [G3 acceptance and current next steps](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#18-当前结论g3-双批专测限定接受进入交付收尾) and [review evidence](evidence/alice-g3-acceptance-20261027.json).

**G0–G3 stage goals and the human/AI documentation closeout are accepted within their stated limits.** Alice reviewed the four candidates based on `c703a599`, corrected candidate checkout instructions and two small usage descriptions, and completed the scoped documentation checks. See [documentation acceptance](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#19-当前接续说明已验收等待合并决定) and [evidence](evidence/alice-doc-closeout-20261027.json). The next action is the maintainer’s merge decision; recheck the exact Head and repository requirements immediately before any authorized merge. No further G3 run or new stage is currently required. PR remains Draft; this review does not merge, install or enable production. The real trial is closed, and old STOP/expiry/PAUSED and the previous R2 uncertain B are preserved. The 180-second admission reserve was not reached in this successful run; its rejection/partial-write boundaries retain their offline evidence. Current installation, loaded dedicated target and synthetic workload are the acceptance scope, not unattended or cross-version guarantees.

Historical owner-precheck acceptance and R2 time-budget repair are preserved in plan sections 16–17 and their evidence. Their old next-action text is superseded by sections 18–19; old trial budgets cannot be rearmed.

**Drive source requirement recorded, not implemented.** Desired behavior: files arriving in a selected Drive folder become complete local inputs and trigger the selected Kelan conversation under the chosen condition. API receiver vs desktop synchronization and access/setup details remain design choices, not approved implementations. See [requirement](docs/SIMPLE_SETUP_DESIGN.md#13-新增需求drive-文件夹触发本地对话).

The independent Tk and cwd-current-state subchecks remain accepted. Section-8–11 operation windows are closed. Package/signing/recovery and endpoint investigations stay shelved. Production installation/configuration, business ACK, continuous authorization and historical STOP/expiry/PAUSED remain unchanged; listener health was not checked. PR stays Draft/unmerged; no local task was dispatched by Alice.

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

The current design is [SIMPLE_SETUP_DESIGN.md](docs/SIMPLE_SETUP_DESIGN.md). G0 is limited_accepted, including the disclosed target-task interpreter fallback; its one-turn/three-sample allowance is closed. G1 implementation and synthetic verification are now accepted. G2 implementation and its simulated transport workflow are now accepted at `6c92f873`. G3 is now limited_accepted for the fixed candidate's loaded-target two-batch workflow. The [current handoff](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#19-当前接续说明已验收等待合并决定) records completed documentation/final scoped review and the pending merge decision; no repeat G3 is required without a new relevant change or finding. The following earlier deployment/community choices remain separate:

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
- Actor attribution: Alice owns the cloud candidate/code reviews, G0/G1/G2 acceptance within their stated scopes, the direct 36-test G1 and 63-test G2 Linux checks, and the current follow-up boundaries. Kelan owns the Windows representative task, real Tk/fake observations, Windows full-suite runs and local reviewer results (including G2 S1/M1). Alice checked public evidence/source bindings and the delivered owner-precheck helper, including the 16 affected tests and two deadline cases in Linux. Private native artifacts and Windows execution remain Kelan-attributed. Historical records retain their original authors and limits.
