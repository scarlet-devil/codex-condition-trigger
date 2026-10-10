# Current state

Status: listener restored, but original task failed in platform remote compact/network at 07:20:09Z; business delivery blocked and repair Drive upload pending. Bounded real trial restored 2026-10-10T07:06:37Z; automatic 14-version batch accepted in the original chat. Prior material batch retained waiting_materials. Current-user logon recovery installed under Human 2026-10-10 repair request; original expiry 2026-10-10T13:11:50Z unchanged. Draft / Alice review_pending.


## Recovery update — 2026-10-10

See [repair report](docs/KELAN_RECOVERY_REPAIR_20261010.md) and [timestamped evidence](evidence/recovery-repair-20261010.json). Final tests154:153pass/1skip. Material-wait release is explicit and does not ACK; old delivered rows remain unchanged. Native bounded exception recovery and expiry observed; Windows OS failure retry was ineffective. Actual reboot/logon chain and same-session external kill recovery remain unaccepted. No window actions or periodic automation change. New model work is not yet business delivery.

## Current authorization — 2026-10-08

Human explicitly approved a two-day production-environment trial after the supervised limits were explained. See [exact authorization and Kelan execution brief](docs/ALICE_PRODUCTION_TRIAL_AUTHORIZATION_20261008.md). This supersedes the prior no-production-activation restriction only for the existing project directory, exact original chat and established task scope during the fixed 48-hour window. Delayed start/restart does not extend the deadline. Merge, permanent enablement and expanded permissions are not approved. The later Human 2026-10-10 repair request separately authorizes current-user logon recovery for this same fixed trial only; historical no-autostart statements describe the earlier deployment.

Local Kelan has started one bounded real-file watcher after verifying the local fixed expiry; startup evidence is saved. Runtime 2c38055 now binds and enforces the fixed UTC/monotonic deadline; 114 tests (113 pass, 1 skip), five write probes and a real dry-watch expiry check are recorded. Expiry must block fresh sends/window actions even after wake/restart; cloud reminders are not the enforcement mechanism. The legacy periodic timer remains PAUSED to avoid duplicate execution. Only the specifically bound trial instance may be unpaused; historical canary STOPs remain.

The existing window backend still requires an explicit no-navigation supervision interval of at most 600 seconds. Do not change that to 48 hours or renew it automatically. Loaded-owner processing may proceed; missing supervision or unresolved cleanup must wait/pause, not bypass protections. This does not require Human to avoid using the computer for two days. Startup must state any loaded-owner-only mode. At expiry pause the trial, retain in-flight turns and undelivered state, and report actual stop evidence; no automatic renewal.

## Latest implementation and evidence — 2026-10-08

Input b8225af531d6da73f69dbd7dfc7d88a6b769f443. Default-off per-batch window lifecycle now precedes dispatch in the single watcher worker: idle reuse, busy wait, explicit owner absence only for open, delivered + correlated completion before owned-window cleanup. Unknown opens/closes remain durable; legacy lifetime claims require explicit reconciliation. Exact batch binding prevents concurrent ACK from advancing to another batch before cleanup; unresolved acceptance must acquire turn correlation before cycle ACK. Disabling loading cannot bypass an unclosed cycle.

Windows UIA backend completed one explicitly supervised loaded-target open/minimize/normal-close test, followed by a second automatic watcher batch. Actual 2 starts, 0 manual dispatch, 2 caller-verified synthetic receipts; total 204.359 seconds. Closing the created window left owner available, so batch 2 reused it. Main chat was unchanged at recorded open/close checks; app and watcher continued between batches. No cold recovery was simulated or claimed.

119 tests: 118 passed, one Windows symlink privilege skip. 42 real-evidence assertions passed. Local controlled code review found and closed ACK scheduling/correlation problems; review is not Alice acceptance. A final per-action supervision expiry check was added after the live trial and checked in isolation, with separate live/final source hashes; no additional model/window trial after that change.

## Alice focused follow-up — F1 accepted

[Review and scoped handoff](docs/ALICE_WINDOW_CYCLE_REVIEW_20261008.md): 39/39 existing focused tests passed on cloud Linux at 2622fd6. An additional synthetic counterexample failed on that input: an idle owner is recorded as reused, then disappears before dispatch; the ready batch has no send intent or window lease, yet the active-cycle branch waits forever instead of claiming its first open. That failure persisted after restart and a new file. Zero extra sends/windows occurred.

Kelan implemented the same-batch reused-to-opening promotion with a cycle-snapshot compare-and-swap and atomic ready/no-send-intent predicate. Only never-opened reused history with no lease qualifies after fresh definite absence. Original probe changes from exit1/0 opens/0 sends to exit0/1 open/1 send. Seven new checks bring the affected modules to 46/46 pass. Python-only; Windows backend and prior native evidence unchanged. See [repair report](docs/KELAN_OWNER_REUSE_RECOVERY_20261008.md) and [red/green evidence](evidence/owner-reuse-recovery-20261008.json). Alice independently reproduced the unchanged probe red/green and passed all 46 focused checks in cloud Linux (0.180 seconds). The atomic same-batch promotion and retained protections are accepted, with no new required fixes. See [Alice follow-up and evidence](docs/ALICE_OWNER_REUSE_RECOVERY_REVIEW_20261008.md).

## Material limits

UIA exposes initialRoute, not independently authenticated current thread identity. Title cannot rule out same-title navigation or staleness. Backend is therefore restricted to an explicitly supervised no-navigation interval of at most 600 seconds and remains default-off. Arbitrary-navigation unattended closure is unresolved, not accepted.

New window was foreground; invoke-to-minimize sample interval 8.552924 seconds. The immediate post-minimize foreground sample still named the new HWND despite IsIconic=true. Neither zero focus nor focus restoration latency is verified. Current original owner was already loaded; cold recovery, ownership transfer, last-window behavior, long-running business, future versions/languages/DPI are unvalidated. Business ACK remains caller verification; this test does not accept real business delivery.

## Records and remaining scope

- [Alice review and recovery counterexample](docs/ALICE_WINDOW_CYCLE_REVIEW_20261008.md)
- [Detailed local report](docs/KELAN_WINDOW_CYCLE_20261008.md)
- [Sanitized evidence and source hashes](evidence/window-cycle-20261008.json)
- [Alice input handoff](docs/ALICE_WINDOW_CYCLE_HANDOFF_20261008.md)
- [Tests](evidence/window-cycle-tests-20261008.txt) and [supervisor](evidence/window-cycle-supervisor-20261008.py)

Alice has reviewed the bounded two-batch cycle separately from unattended current-route and focus limits. F1 repair is accepted and that scoped review is complete; the new two-day trial scope is above. Wider product limits are not reopened as F1 repair gates. Local Kelan has started one temporary Windows live watcher; legacy timer PAUSED and historical canary STOPs remain. See [startup report](docs/KELAN_PRODUCTION_TRIAL_STARTUP_20261008.md) and its evidence. Backlog report/package and R3 addendum/package are all Drive readback verified. 1269 historical byte versions seeded; four new versions at launch scan remain for automatic intake. Alice trial review_pending. Existing business history, Hook config and exact binding must be preserved.

启动后观察（2026-10-08T14:22:13.144911+00:00）：自动IPC接受事件1、当前批次状态['running']、关联turn1、业务核验交付0；人工dispatch0、窗口动作0。发现/接受不代替交付，继续由原任务按真实结果核验。

## Alice cloud Dot results analysis — first bounded analysis delivered

The service now reports enabled (updated 2026-10-08T15:13:55.519255Z). Actual model/reasoning metadata remains unknown; prompt text is not configuration evidence. Alice did not change the task switch or model.

Alice has read and hashed four report/evidence groups plus Day5/Day7 supporting originals. Four ZIPs: 91/91 manifest entries and CRC passed. Saved Day5 expectations yield4/6 with two false negatives; Day7 snapshots yield15 observations/9IDs and32/30 budget. Fixed upstream Humanizer and Trackio source paths corroborate structural-check limits and a possible lost-batch path. No candidate execution or installation. See [bounded analysis](docs/ALICE_DOT_RESULTS_ANALYSIS_20261008.md) and [exact versions/gaps](evidence/alice-dot-results-ledger.json).

All four families remain partial for underlying source/experiment gaps; new R3 freeze supersedes old missing-freeze claims, not the absence of real runtime evidence. Unchanged delivery sets/gaps do not cause repeated notifications. This analysis does not accept or alter the local trial, deadline code, production ACK or timer. Fixed expiry remains2026-10-10T13:11:50Z; PR Draft and prior F1 acceptance unchanged.
