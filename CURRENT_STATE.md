# Current state

Updated 2026-10-23 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

The human has selected **a dedicated new conversation on the unmodified Desktop, short chat/tool output and file-based detailed results**. This replaces the pending route choice at b6638bae. The three-field setup remains the goal; G0 is still unverified, and the form/ordinary notification scheduler are not implemented.

The active handoff is [section 8: dedicated-conversation measurement](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#8-当前执行专用新对话减量验证). First measure a newly initialized conversation, then the same conversation after one representative synthetic task; optionally observe busy during that task. At most three read-only samples and two model turns including initialization, within one 10-minute experiment. Model task execution remains separate from the read-only sampler and depends on an accurately selected local target and the existing task/window authorization. No local-agent message or execution has occurred from cloud Work.

Alice prepared [snapshot_measure.py](experimental/snapshot_measure.py) and [13 synthetic checks](experimental/tests/test_snapshot_measure.py). The sampler uses the unchanged original full-snapshot/revision implementation, verifies the fixed installation, rechecks owner, exports only aggregate sizes/timings and a state projection, and always returns can_send:false. It has no CLI, live pipe discovery or production integration. Limits are 32 MiB per frame body, 128 MiB cumulative reads including unrelated frames/headers, and a shared 10-second IPC deadline after installation verification. It does not claim a small response, a strict end-to-end process timeout or exact wire totals for incomplete low-level I/O.

The selected mode requires actual bounded state observations before G0 can pass. Short output is a usage convention, not a snapshot-type switch. Growing histories may still exceed the budget; preserve pending batches and stop automatic dispatch, then require explicit target selection and revalidation. No automatic history deletion, target rotation or frame-limit increase. Original thread/cwd/owner/revision and uncertain-send handling remain; ordinary follow-up is isSteering:false, and idle/start is not atomic.

The other two discussion items remain partially evidenced: catalog/rollout identity was matched for two local targets, but final filtering/name/path selection and the new target binding need verification; busy suppression and ordinary follow-up exist in the old implementation, but this target's busy/idle/turn behavior and the new ordinary-notification scheduler are not accepted. Tk was importable; an actual small GUI/chooser test is still outstanding. These fit the next local experiment without reopening endpoint/package research.

Alice's prior copy-only acceptance of ec2fb862 and bounded inventory acceptance of 9a863af5 remain historical. The patch stays default-off. Protected-host loading, experimental signing and package recovery are **not prerequisites for the currently selected route**. No further package changes or recovery search is in scope; the accepted reports and their original delivery-time status fields remain fixed.

This increment adds an isolated diagnostic/test and updates current documents only. Production source/configuration, Desktop installation, business ACKs and historical evidence are unchanged. The incoming WORK_LOG's exact 130,487-byte prefix and 11 CRLFs are preserved. Current listener health was not inspected; existing continuous authority and historical STOP/expiry/PAUSED scopes remain. PR stays Draft/unmerged; cloud preparation and synthetic tests do not establish Windows success or G0 acceptance.

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

The current design is [SIMPLE_SETUP_DESIGN.md](docs/SIMPLE_SETUP_DESIGN.md), with proposed defaults, compatibility rules and G0–G3 stages. The copy candidate and loading inventory are reviewed; the human selected the unmodified-Desktop route. The next work is [its bounded local validation](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#8-当前执行专用新对话减量验证), using the prepared sampler, not another route decision or inventory. The three-field interface and ordinary notification mode are not yet available. The following earlier deployment/community choices remain separate:

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
- Actor attribution: Alice performed the 2026-10-20 cloud documentation/merge closeout and Linux checks, prepared/revised the 2026-10-23 design, and reviewed the published 9116c888, e83da55, ec2fb862 and 9a863af5 evidence in cloud Work. Alice directly reran 47 public candidate tests in the prior review, reviewed the completed loading inventory, and now prepared the snapshot sampler with 13 direct synthetic tests. Kelan performed the Windows intake, installed-source/resource/signature investigation and partial-state probe. Alice's document/hash/code review does not constitute a Windows rerun or G0 acceptance.
