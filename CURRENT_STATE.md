# Current state

Updated 2026-10-23 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

Human requested a design for choosing only a folder, a condition and a target conversation, then said “嗯可以，开始设计吧” in the current project conversation on 2026-10-23. Alice prepared the [three-field setup design](docs/SIMPLE_SETUP_DESIGN.md): a local form, automatic conversation binding, and a new ordinary notification mode that can advance without a business ACK. These are proposed behaviors, not implemented features.

**Alice reviewed Kelan's published evidence at `9116c88881d5fb1d04270de3fd63fc34aefe6bf6`; G0 remains incomplete.** The [sanitized intake](docs/KELAN_PR2_G0_INTAKE_20261023.md), [follow-up](docs/KELAN_LIGHT_STATE_FOLLOWUP_20261023.md) and probe support the reported limitation. Ten changed files were read in full and matched their Git blobs; nine hash-manifest entries matched length/SHA-256/blob. The manifest is scoped to that fixed historical commit, not later revisions of this file or WORK_LOG. See [the current review and next scope](docs/SIMPLE_SETUP_DESIGN.md#11-补交材料审阅与原宿主入口取舍).

Kelan's Windows observations found a small settings response (2,059 received bytes, 0.015 seconds IPC; resumed) and an unavailable original owner (1,245 bytes, 0.016 seconds IPC). Neither proves sendability. Full observations including local installation checks took 0.890/0.860 seconds; each check hashed a 625,947,531-byte archive. Alice verified the frame arithmetic and probe source, not the Windows execution. Installed-source findings and seven synthetic checks/Ruff remain attributed to Kelan. The 34,956,277-byte historical rejected frame still has unknown message/target attribution.

Kelan completed the authorized original-service entry investigation in 12 minutes 24 seconds on 2026-10-23. The [local report](docs/KELAN_ORIGINAL_SERVICE_ENTRY_20261023.md) and [sanitized evidence](evidence/kelan-original-service-entry-20261023.json) trace the installed Windows default to a Desktop-owned stdio child; no reusable summary endpoint was found in the reviewed routes. The known IPC follower bridge lacks a verified thin runtime query, the original processes had no observed TCP listener, and the reviewed local daemon branch excludes Windows. This is a version-scoped investigation result, not proof that no future route can exist. Both target state queries were not attempted because the endpoint prerequisite failed. G0 remains blocked. Alice has not yet reviewed this new increment.

Freshness must be proved according to the actual protocol. Keep revision checks for the existing snapshot adapter; a candidate protocol without revision requires verified original-service identity, exact thread/cwd and a correlated current response with validated server-side semantics. A request ID alone does not establish freshness. Any future send still rechecks state and retains the known non-atomic idle/start limitation.

Installation cost was measured separately: one successful check took 0.775323 seconds, including 0.482104 seconds for signature verification and 0.248328 seconds for the 625,947,531-byte archive SHA-256. This is one warm-machine observation, not a recurring or cold-cache benchmark. An initial signature subprocess/decoding failure is preserved; two metadata-only pipe opens occurred, with zero protocol messages or model/window actions. No cache was implemented. The next step is an explicit product-boundary choice: retain limited experimental integration, seek a supported original-service bridge, or separately consider tool-owned service/chats. No change of that boundary is implied.

Final byte verification caught an initial delivery-preparation newline error in be49f92: 11 historical WORK_LOG CRLF endings were normalized to LF. The corrective delivery restores the original bytes and validates Git blobs/lengths/SHA-256; see the log correction and final receipt. The intermediate commit is not a valid match for its WORK_LOG manifest entry.

The three-field design remains proposed. This evidence review is complete within its documented scope; overall PR remains Draft / review_pending, with G0 blocked and G1/G2 not started. The current increment adds the bounded entry report/evidence and updates current-state/log documents. Production sources, probe artifacts, configuration and operating tasks are unchanged. Current listener health was not inspected.

## Accepted implementation baseline

Human approved preparing the human README and AI entry files, then merging [PR #1](https://github.com/scarlet-devil/codex-condition-trigger/pull/1), on 2026-10-20 at 20:50 Asia/Shanghai. Alice's preceding assessment supports merging the implemented version while retaining its operational limits.

**Implementation accepted and merged.** PR #1 merged on 2026-10-20 as `5c1882c7b78fc023d0588953e6e43db55ebe216d`; its [final receipt](https://github.com/scarlet-devil/codex-condition-trigger/pull/1#issuecomment-6291604544) records that closeout. Deployment is a separate state. Historical Draft labels for PR #1 are not current; the new design is a separate Draft change.

Runtime/test baseline: `95a6e9f7765bea2e308a99308c7d9488e4b477e0`. The 2026-10-20 closeout changed documentation and evidence only. Runtime files remain unchanged from the reviewed integration implementation; the later test fixture repair is included. The present design branch changes documentation and isolated diagnostic evidence; production runtime sources are unchanged.

## Accepted scope

| Area | Current conclusion and source |
| --- | --- |
| File-triggered dispatch | Real Windows automatic two-batch supervised trials accepted within their recorded scope: [window review](docs/ALICE_WINDOW_CYCLE_REVIEW_20261008.md), [owner recovery acceptance](docs/ALICE_OWNER_REUSE_RECOVERY_REVIEW_20261008.md). |
| Watcher health and real login | Progress/stale/exit reporting implemented. Kelan's real dry login trial passed; Alice checked the supplied script, hashes and summary, without claiming direct Windows observation: [login report](docs/KELAN_REAL_LOGON_ACCEPTANCE_20261016.md). |
| Native execution outcome | Automatic collection implemented, exact native bindings reviewed, loaded-chat IPC read validated. Original production target business acceptance remains pending. |
| Upload recovery | Existing Hub integration installed by Kelan under separate approval. Real Drive client-receipt-loss recovery accepted; Alice independently read back the existing canary bytes. [Actual local result](docs/KELAN_HUB_LIVE_ACCEPTANCE_20261016.md). |
| Latest cloud regression | 185 tests: 184 passed, one Windows-only overlapped-I/O test skipped, zero failures/errors. Frozen Hub included; all three outbox-to-Hub tests ran. [Validation](evidence/alice-merge-validation-20261020.json). |

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

The current authorized design is [SIMPLE_SETUP_DESIGN.md](docs/SIMPLE_SETUP_DESIGN.md), with proposed defaults, compatibility rules, acceptance cases and G0–G3 stages. The three-field interface and ordinary notification mode are not yet available. The following earlier deployment/community choices remain separate:

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
- Actor attribution: Alice performed the 2026-10-20 cloud documentation/merge closeout and Linux checks, prepared/revised the 2026-10-23 design, and reviewed the published 9116c888 evidence in cloud Work. Kelan performed the Windows intake, installed-source investigation and partial-state probe. Alice's document/hash/code review does not constitute a Windows rerun or G0 acceptance.
