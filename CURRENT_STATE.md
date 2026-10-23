# Current state

Updated 2026-10-23 · Project: `scarlet-devil/codex-condition-trigger`

## Active decision

Human requested three setup fields—folder, condition and target conversation—then asked Alice on 2026-10-23 to record the recent decisions and prepare Kelan's next-action plan: “写好work_Log以及让柯蓝下一步行动的方案”. The [three-field design](docs/SIMPLE_SETUP_DESIGN.md) remains proposed; the form and ordinary notification scheduler are not implemented.

**The original-service entry investigation is complete; G0 remains blocked. The current next step is a minimal thin-state patch candidate and isolated validation.** See [Kelan's next-action plan](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md). Do not repeat the historical 60-minute endpoint investigation in design section 11.

Alice has now read back all five changed files at `e83da5506a7b25f27ac90477926c0e4180ff6a0a` plus AGENTS/design, matched seven Git blobs, and verified all four length/SHA-256/blob entries in the [historical manifest](https://github.com/scarlet-devil/codex-condition-trigger/blob/e83da5506a7b25f27ac90477926c0e4180ff6a0a/evidence/kelan-original-service-entry-manifest-20261023.json). The [report](docs/KELAN_ORIGINAL_SERVICE_ENTRY_20261023.md) and [evidence](evidence/kelan-original-service-entry-20261023.json) support the bounded conclusion: in the inspected Windows installation/routes, no existing external summary endpoint was found. The Desktop-owned service uses stdio; the inspected IPC forwarding lacks a thin runtime query. This accepts the public evidence within its scope, not G0, Windows replication or a universal absence claim. Private installed-source observations remain attributed to Kelan. Historical reports retain their then-pending review status; this paragraph records the later cloud review.

The recent discussion establishes three directions:

- Use a dedicated, user-selected Desktop conversation for the first trial. Bind exact thread/cwd/rollout/current owner; a title, deep link or window handle is not the delivery identity. Continue with a new user turn in that same conversation, keeping `isSteering:false`.
- Use read-only status checks for routine busy/idle decisions. A real small message is a bounded functional test, not a polling mechanism. Existing busy tests suppress a send before dispatch; atomic host busy rejection is unverified. Retry after a send is allowed only with proof of non-acceptance; lost receipts remain uncertain and require reconciliation.
- Prepare a separate, read-only per-thread summary method on the existing IPC route, reusing the original service's `thread/read(includeTurns=false)` or another proven current-state projection. Preserve the full-snapshot protocol. First produce the candidate diff, isolated checks and exact loading/rollback implications; do not assume this is already a one-field fix or install it from this planning task.

The candidate must prove original-service identity, native thread/cwd, current server-side semantics and correlated bounded replies. Existing snapshot revision checks remain; a summary lacking revision needs an evidenced equivalent observation, not an invented field. Initial budgets remain 64 KiB per message, 1 MiB cumulative receive and 10 seconds shared RPC deadline with no automatic retry; installation checks are timed separately. State checking does not eliminate the non-atomic idle/start race or replace turn completion/business ACK evidence.

The historical 34,956,277-byte rejected frame has unknown message/source/target attribution; its body was not read. Moving model input to file paths does not change that return protocol. Dedicated conversations may initially have less history but do not remove the need for bounded state reads. Settings-only `resumed` and owner discovery still do not establish idle/sendability; the original results owner was unavailable in the last actual probe.

Remaining G0 work includes a genuine original-service thin query, final conversation-list filtering/identity handling and actual Tk GUI verification. Candidate logic checks, a separate service or Tcl import cannot substitute for these. G1/G2 follow G0; the scoped two-batch same-conversation trial remains G3. The direct-send/busy-response route is optional research, not an enabled fallback.

Installation verification cost remains a single observation: 0.775323 seconds, including 0.482104 for signature and 0.248328 for the 625,947,531-byte archive hash. No recurring-cost guarantee or cache implementation follows. The earlier delivery correction restored 11 historical WORK_LOG CRLF endings after be49f92; that failed intermediate manifest match remains documented. Subsequent edits must preserve the current log's full byte prefix, and historical manifests stay pinned to their own commits.

This increment updates planning documents only. Alice's document self-review is S0; the overall PR remains Draft / review_pending and G0 blocked. No task was sent to Kelan, no patch was implemented/loaded and no model, window, installation or production action occurred. Existing continuous operation, historical STOP/expiry/PAUSED, ledgers and ACKs are unchanged; current listener health was not inspected.

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

The current design is [SIMPLE_SETUP_DESIGN.md](docs/SIMPLE_SETUP_DESIGN.md), with proposed defaults, compatibility rules and G0–G3 stages. The active continuation is [the thin-state patch plan](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md); its first delivery is an isolated candidate, not live installation or a repeated endpoint survey. The three-field interface and ordinary notification mode are not yet available. The following earlier deployment/community choices remain separate:

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
- Actor attribution: Alice performed the 2026-10-20 cloud documentation/merge closeout and Linux checks, prepared/revised the 2026-10-23 design, and reviewed the published 9116c888 and e83da55 evidence in cloud Work. Alice also prepared the current thin-state continuation plan. Kelan performed the Windows intake, installed-source investigation and partial-state probe. Alice's document/hash/code review does not constitute a Windows rerun or G0 acceptance.
