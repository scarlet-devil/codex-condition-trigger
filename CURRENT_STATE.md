# Current state

Updated 2026-10-23 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

Human requested a design for choosing only a folder, a condition and a target conversation, then said “嗯可以，开始设计吧” in the current project conversation on 2026-10-23. Alice prepared the [three-field setup design](docs/SIMPLE_SETUP_DESIGN.md): a local form, automatic conversation binding, and a new ordinary notification mode that can advance without a business ACK. These are proposed behaviors, not implemented features.

**Design retained; G0 remains incomplete.** Kelan's local intake is now supplied in a [sanitized report](docs/KELAN_PR2_G0_INTAKE_20261023.md) and [historical frame diagnostic](evidence/kelan-g0-ipc-frame-20261023.json). The original private report remains local with its hash; Alice's earlier relayed-summary review remains historical and does not count as acceptance of this new package.

The [installed-source follow-up](docs/KELAN_LIGHT_STATE_FOLLOWUP_20261023.md) confirms that following alone sends a conversation snapshot; removing complete-history is insufficient. A narrower read-model-settings request returned resumed from the loaded owner using 2,059 received IPC bytes in 0.015 seconds, but supplies no runtime status/cwd/revision. The original results target returned owner_unavailable (1,245 bytes; 0.016 seconds). Both remain unknown for sending. Total observation times including local installation verification were 0.890/0.860 seconds; archive hashing is a separate substantial setup cost.

The internal and documented thread/read(includeTurns=false) is a promising summary path, but an external route bound to the original Desktop server is unproven. No independent app-server was started. The next decision is that narrow original-host bridge investigation, with exact binding and freshness, before G1/G2. The 34,956,277-byte historical rejected frame still has unknown message/target attribution.

This branch adds documentation and isolated diagnostic evidence only; production runtime sources/configuration, frame cap, ACKs and operating tasks were not changed. This follow-up made two bounded read-only IPC observations, zero model sends and zero window actions. PR remains Draft and Alice review is pending. See the G0 follow-up in the [design](docs/SIMPLE_SETUP_DESIGN.md).

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
- Actor attribution: Alice performed the 2026-10-20 cloud documentation/merge closeout and Linux checks, and prepared/revised the 2026-10-23 design. Kelan supplied the sanitized G0 intake and performed the subsequent Windows partial-state probe; Alice's source-level review remains attributed to Alice, without claiming she reran Windows observations or accepted the new package.
