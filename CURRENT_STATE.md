# Current state

Updated 2026-10-23 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

The three-field setup remains the product goal: folder, condition and an existing Desktop conversation. Its form and ordinary notification scheduler are not implemented. The current continuation is [section 6 of Kelan's action plan](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#6-当前接续接受副本候选核对加载改动集合).

**Alice accepts `ec2fb862050384385b66ed9dc0e0bfff7156a2e4` as a copy-only thin-state candidate. Actual protected-host loading and G0 remain blocked.** The [candidate report](docs/KELAN_THIN_STATE_COPY_CANDIDATE_20261023.md) records three patched module copies and a default-off caller. The [cloud review evidence](evidence/alice-thin-state-review-20261023.json) records 17 fully read-back/matched blobs, all 12 historical candidate-manifest entries, and Alice's direct 33 JS + 14 Python passing tests (zero failures/skips). Six patch-anchor hashes and three length deltas also match the report.

The private source-extraction checks (18), local legacy tests (36), three actual module round trips and Windows signature checks remain attributed to Kelan, not cloud reruns. The local S1 review is reported attribution; its transcript was not supplied. Alice's own planning/document changes are S0. This review does not establish full bundle imports, actual installation rollback, real original-service identity/freshness or cross-version compatibility.

Kelan reports embedded ASAR integrity and ASAR-only loading enabled in the signed chrome.dll. Alice independently checked the official fixed fuse mapping and Electron loading mechanism. These support the conditional inference that replacing app.asar alone is insufficient. The actual PE resource holding the ASAR-header baseline, its byte match and the installation's package/signature constraints have not yet been inspected. Fuse location alone does not identify that resource-bearing file. Recomputing a hash does not preserve a vendor signature on modified signed content.

**The next task is one read-only local loading inventory and a concrete change/restore table.** Locate the named integrity resource in the already identified host files, compare it with the raw ASAR header, determine the actual signing/package layer and available recovery unit, then describe the minimum loading transaction or its concrete blocker. Keep integrity validation; no live package change, re-signing, certificate/permission change or restart is authorized by this review. There is no repeated endpoint search or new general-purpose packager. A new signer/package identity or effects on user data require an explicit product/risk choice based on that concrete result.

The dedicated-conversation and busy-handling decisions remain:

- Select a dedicated conversation and bind exact thread/cwd/rollout/current owner. Titles, deep links and window handles are not delivery identity. Follow-up uses a new user turn with `isSteering:false`.
- Routine status reads are read-only. A real small message is a bounded functional test, not polling. Pre-send busy suppression is tested; atomic host busy rejection is not. An ambiguous send still requires reconciliation before retry.
- Preserve full-snapshot APIs and revision checks. The new candidate uses a single current summary and owner/connection-lifetime checks, with bounded traffic and a shared deadline; it always returns `can_send:false`. Wall-clock changes, suspend and real queue behavior remain untested. No status read makes idle/start atomic.

The historical 34,956,277-byte rejected frame body was not read, and its source/target/type remain unknown. File-path model input does not change the state-return protocol. Settings-only resumed and owner discovery still do not prove sendability. The last actual original-results owner probe was unavailable.

G0 still needs a bounded query to the genuine original service, final conversation filtering/identity handling and actual Tk GUI checks. G1/G2/G3 are not started. A copied Desktop or separate app-server does not satisfy the existing-original-host requirement. The earlier 60-minute entry investigation and first candidate implementation are completed historical tasks, not the active next step.

Historical manifests remain scoped to their fixed commits; updates do not rewrite old evidence. This review preserves the full current 121,206-byte WORK_LOG prefix and its 11 historical CRLF endings. Installation timing remains a single observation, with no cache or polling-performance claim.

Overall PR remains Draft / review_pending. This cloud review changes documentation/evidence only, dispatches no local task and performs no Windows/IPC/model/window/installation/production/ACK action. Existing continuous operation and historical STOP/expiry/PAUSED scopes are unchanged; current listener health was not inspected.

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

The current design is [SIMPLE_SETUP_DESIGN.md](docs/SIMPLE_SETUP_DESIGN.md), with proposed defaults, compatibility rules and G0–G3 stages. The copy candidate is now reviewed; the active continuation is [its read-only loading inventory](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#6-当前接续接受副本候选核对加载改动集合), before deciding an actual loading transaction. The three-field interface and ordinary notification mode are not yet available. The following earlier deployment/community choices remain separate:

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
- Actor attribution: Alice performed the 2026-10-20 cloud documentation/merge closeout and Linux checks, prepared/revised the 2026-10-23 design, and reviewed the published 9116c888, e83da55 and ec2fb862 evidence in cloud Work. Alice directly reran 47 public candidate tests and prepared the current loading-inventory scope. Kelan performed the Windows intake, installed-source investigation and partial-state probe. Alice's document/hash/code review does not constitute a Windows rerun or G0 acceptance.
