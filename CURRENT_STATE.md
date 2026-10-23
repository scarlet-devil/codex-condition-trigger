# Current state

Updated 2026-10-23 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

The three-field setup remains the product goal. Alice accepts ec2fb862 as a copy-only thin-state candidate (33 JS + 14 Python direct cloud tests) and accepts the bounded read-only loading inventory at 9a863af5. Protected-host loading and G0 remain blocked. The form and ordinary notification scheduler are not implemented.

**The section-6 inventory and Alice's cloud review are complete.** See [the review and route recommendation](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#7-清点审阅与接入路线选择), [the concrete change/restore table](docs/KELAN_PROTECTED_LOAD_INVENTORY_20261023.md) and [local evidence](evidence/kelan-load-inventory-20261023.json). Kelan's static parsing and Windows data-only resource access agree that ChatGPT.exe holds the unique 122-byte INTEGRITY/ELECTRONASAR resource, matching the original raw ASAR JSON header; chrome.dll has no such resource. Alice checked the public evidence and checker sources, not the private Windows installation.

The minimal content change set is app.asar plus ChatGPT.exe's signed resource. chrome.dll and its enabled fuses remain unchanged. Current PE signatures and CodeIntegrity.cat report Valid, Windows package registration is Store/Ok, and all 14658 relevant blocks plus three whole-file FileHash entries match. CMS signature-only verification is not full package/container trust validation. A package-based experiment also needs consistent blockmap/signature/catalog, a viable signer/identity/deployment choice, and proven restoration. No verified same-version reinstallable recovery unit was found within the bounded readable scope; one old temporary directory was inaccessible. Current installed originals and module copies alone do not prove package rollback.

**Current recommendation: do not make Store-package modification a default requirement for the three-field product.** Prefer evaluating a dedicated conversation with the existing, unmodified Desktop and bounded full-snapshot channel as a limited compatibility mode. This is a route proposal, not an adopted design change, G0 acceptance or dispatched experiment. It cannot promise support for growing/large histories; it retains exact identity/revision checks and the existing 32 MiB frame limit. A selected experiment must specify cumulative/time budgets. No automatic fallback is added to the thin-state caller.

Keep the accepted patch candidate available if the human instead chooses a package experiment with an explicit signer/identity/data/update strategy and verified restoration. A local signer cannot preserve vendor provenance. No further endpoint discovery, broad recovery search, package change, re-signing, certificate/permission/registration change, restart or replacement host follows automatically. A supported original-host summary interface remains a longer-term route, but none has been obtained. A copied Desktop or self-managed service cannot substitute for original-host acceptance.

The candidate stays default-off, without a live pipe factory and with can_send:false. Existing full-snapshot/revision APIs are unchanged. G0 still requires actual original-service identity/freshness, directory/filter/rollout binding and Tk checks; G1–G3 have not started. A dedicated target must retain exact thread/cwd/owner; ordinary follow-up remains isSteering:false. Unknown/busy states cannot grant send permission; idle/start is not atomic. The historical rejected 34956277-byte body was never read and its source/type remain unknown. Wall-clock/suspend/queue behavior and cross-version compatibility remain unaccepted.

Prior Alice cloud acceptance and historical local extraction/roundtrip results retain their recorded scopes. Kelan's inventory was delivered as self-review/S0, review_pending; Alice now accepts that bounded deliverable, without claiming a Windows rerun or loading acceptance. Historical reports/manifests remain fixed. Alice verified 12 input/related Git blobs, all 6 manifest entries, the prior log prefix, both helper ASTs and evidence arithmetic; the 47 unchanged candidate tests were not rerun. This documentation increment preserves the exact incoming 127,292-byte WORK_LOG prefix and 11 CRLFs. No candidate/production code, IPC/model/window action, package deployment or ACK changed; current listener health was not inspected. Existing continuous authority and historical STOP/expiry/PAUSED scopes remain. PR stays Draft/unmerged; overall design acceptance remains pending.

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

The current design is [SIMPLE_SETUP_DESIGN.md](docs/SIMPLE_SETUP_DESIGN.md), with proposed defaults, compatibility rules and G0–G3 stages. The copy candidate and loading inventory are reviewed; the next decision is [the access route and its minimum validation](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#7-清点审阅与接入路线选择), not another inventory. The three-field interface and ordinary notification mode are not yet available. The following earlier deployment/community choices remain separate:

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
- Actor attribution: Alice performed the 2026-10-20 cloud documentation/merge closeout and Linux checks, prepared/revised the 2026-10-23 design, and reviewed the published 9116c888, e83da55, ec2fb862 and 9a863af5 evidence in cloud Work. Alice directly reran 47 public candidate tests in the prior review and now reviewed the completed loading inventory. Kelan performed the Windows intake, installed-source/resource/signature investigation and partial-state probe. Alice's document/hash/code review does not constitute a Windows rerun or G0 acceptance.
