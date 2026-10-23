# Current state

Updated 2026-10-24 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

**Alice has reviewed and accepted the bounded current-state result published at `77ef0c0f2e9399338ee7e5e1939b40426347f16c`.** Kelan's one real Windows query on the same dedicated target passed the restricted cwd fix from `d55c62d204ba8193974b5434b19898dd65776a43`: idle, revision/requested_revision 6/6, unchanged final owner and verified installation/binding. See the [local report](docs/KELAN_CWD_REVALIDATION_20261024.md), [evidence](evidence/kelan-cwd-revalidation-20261024.json) and [Alice review / next scope](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#11-当前接续代表性任务后的体量与回合关联). This evidence review is complete; overall G0 and product acceptance remain incomplete.

The sample completed at 2026-10-24 00:14 Asia/Shanghai: maximum target snapshot 8,972 B, RX 29,373 B, verification/IPC/total about 0.906/0.032/0.938 seconds. Three target snapshot frames belong to one query. The 32 MiB frame / 128 MiB cumulative RX / 10-second IPC-after-verification budgets were unchanged. The sampler's can_send=false is its read-only contract. Model/initialization turns, query retries, window actions and Tk retests were zero. Section-8–10 windows are closed; the traceback observer was not used.

Alice checked all five published delivery files, four manifest entries, eight import source pins, 183 unchanged blobs and the preserved 146,038 B / 11 CRLF input-log prefix. Windows test results are attributed to Kelan: 34 experimental and 55 affected tests passed with no skips. The first affected run's 39 PermissionError events were retained; only test-runner temporary fixtures moved into the writable run directory, with candidate source unchanged. Five selected files were Ruff-clean; 11 existing test_native_state.py diagnostics remain. Private raw Windows logs/ZIP/binding were not independently re-read in cloud. No tests were rerun for this documentation-only review; Alice's earlier cloud checks remain valid within their original scope.

The cwd current-state blocker and the independent Tk chooser smoke are closed within the reported scope. This remains a full-history query on a small dedicated chat, not a thin-state endpoint, filesystem-object identity proof, long-term growth guarantee or optimized high-frequency poller.

The [next bounded plan](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#11-当前接续代表性任务后的体量与回合关联) uses the same target, at most one synthetic model task, and before/during/after measurements with no repeat merely to catch busy. Final discovery/selection evidence and post-task bounded state are the remaining G0 work. Rules/notify scheduling are G1, the complete form is G2, and two-batch live notification is G3; those implementation stages are not extra G0 prerequisites. Native idle/start remains non-atomic. The next local experiment has not been dispatched or executed by Alice.

Package/signing/recovery and endpoint investigations remain shelved. No Desktop installation, deployed copy/configuration, business ACK, continuous authorization or historical STOP/expiry/PAUSED state was changed. Listener health was not checked. PR remains Draft/unmerged; no production candidate was enabled.

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

The current design is [SIMPLE_SETUP_DESIGN.md](docs/SIMPLE_SETUP_DESIGN.md). The same-target Windows cwd revalidation and independent Tk smoke are accepted within scope. The next local task is the [section-11 representative-task experiment](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#11-当前接续代表性任务后的体量与回合关联), not another repair-only query. Overall G0 is still open; G1–G3 are not implemented or accepted. The following earlier deployment/community choices remain separate:

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
