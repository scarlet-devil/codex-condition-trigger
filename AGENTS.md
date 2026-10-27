# AI and contributor entry

This file describes this repository. It does not establish an agent's identity, change platform instructions or grant permission to operate a user's local environment.

## Read only what the task needs

1. Read [CURRENT_STATE.md](CURRENT_STATE.md) for current acceptance, limits and follow-up scope.
2. Read [README.md](README.md) or [README.zh-CN.md](README.zh-CN.md) for user behavior and the dry demo.
   For the three-field Windows flow, read the [usage guide](docs/SIMPLE_SETUP_G2.md). G0–G3 reached their scoped acceptance; [section 19](docs/KELAN_THIN_STATE_NEXT_STEPS_20261023.md#19-当前接续说明已验收等待合并决定) records accepted documentation and the pending merge decision. Earlier trial windows are closed, not reusable work orders.
3. Use the code map below and the relevant tests. Consult the latest [integration review](docs/ALICE_INTEGRATION_REVIEW_20261016.md) when touching Desktop or Hub behavior.
4. Use [WORK_LOG.md](WORK_LOG.md) for decisions and provenance, starting from the newest entries. Older dated reports are historical, not fresh authorization.

Read the current user's request before continuing any old task. A clone, merge or prior trial record does not authorize deployment, live sends, uploads or clearing STOP. No historical acceptance plan should be revived just because it appears in an old document.

## Code map

| Area | Files |
| --- | --- |
| Configuration, file scanning, immutable batches, SQLite, CLI | `trigger.py`, `tests/test_trigger.py`, `tests/test_review_regressions.py` |
| Three-field form, exact catalog selection, rule lifecycle | `simple_setup.py`, `simple_catalog.py`, `simple_controller.py`, `rule_service.py`, `tests/test_simple_catalog.py`, `tests/test_simple_controller.py`, `tests/test_rule_service.py` |
| Ordinary notification sequencing and strict compatibility | `notify_state.py`, `trigger.py`, `tests/test_notify.py`, `tests/test_notify_boundaries.py` |
| Bounded experiment tools (not the ordinary setup entry) | `experimental/g3_launch.py`, `experimental/g3_trial.py`, `tests/test_g3_launch.py`, `tests/test_g3_admission.py` |
| Chat adapters, cwd comparison and native IPC | `chat_adapters.py`, `desktop_ipc.py`, `cwd_paths.py`, `tests/test_chat_adapters.py`, `tests/test_desktop_ipc.py`, `tests/test_native_state.py`, `tests/test_cwd_paths.py` |
| Batch/window lifecycle | `owner_loading.py`, `windows_window_backend.ps1`, `tests/test_owner_loading.py`, `tests/test_window_cycle.py` |
| Trial deadline, bounded worker, login entry, health | `trial_limits.py`, `trial_worker.py`, `install_trial_task.ps1`, `worker_health.py`, `tests/test_trial_deadline.py`, `tests/test_recovery_worker.py` |
| Native execution outcome | `execution_result.py`, `native_collector.py`, `tests/test_native_collector.py`, `tests/test_followup_fixes.py` |
| Output freeze and upload recovery | `delivery_outbox.py`, `hub_delivery_driver.py`, `tests/test_hub_delivery_driver.py`, `tests/test_followup_fixes.py` |
| Incomplete materials and explicit continuation | `tests/test_material_wait.py`, [recovery semantics](docs/RECOVERY_AND_MATERIAL_WAIT.md) |

## Behavioral contracts to preserve

- Input and state are separate, absolute, non-nested trees. Never overwrite input versions or seed unverified material as delivered.
- Persist send intent before the external action. Reconcile ambiguous acceptance; do not retry uncertain sends as if nothing happened.
- Keep transport acceptance, lifecycle end, native execution outcome and business ACK distinct. `task_complete` alone does not establish successful execution or delivery.
- Ordinary `notify` rules release only after exact acceptance, the matching terminal record and a fresh target-idle observation. They do not require or fabricate business ACK; legacy configurations retain strict delivery behavior. An uncertain send blocks blind retransmission.
- Previewing a catalog selection does not query/load a Desktop owner or enable a rule. The current form requires an explicitly opened exact dedicated chat and performs the initial fresh capability/idle check when enabled. Minimizing keeps its worker alive; pause/close stop the rule without cancelling already accepted host work. Reading a saved rule does not auto-resume it.
- The G3 480-second/two-start/180-second-reserve contract belongs to its bounded experiment. It is not a universal deadline or start policy for every ordinary rule. No new G3 run is required solely to edit documentation.
- Preserve the first verified ACK. Polling, collection, retries and concurrent updates must not overwrite delivered evidence.
- Native collection binds exact thread, cwd, revision, turn, batch and manifest. Missing/conflicting evidence remains unknown. `native_result_collection` is off by default.
- Preserve STOP, the absolute trial deadline and the monotonic budget. Restart/unpause cannot renew an expired trial. Local STOP does not cancel work already accepted by the host.
- Window loading is off by default. The present Windows backend needs explicit no-navigation supervision for at most 600 seconds. Reused user windows do not acquire close permission.
- Upload recovery acts on frozen bytes and a persistent remote identity; lookup/readback precede any safe creation or retry. It does not call a model or automatically ACK. Hub adapter limit: 8 MiB; generic outbox: 20 MiB.
- Keep private configs, credentials, conversation history and production databases out of commits. Use isolated synthetic inputs for tests.

## Verification

Baseline:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The suite contains 185 tests at runtime baseline `95a6e9f7765bea2e308a99308c7d9488e4b477e0`. The 2026-10-20 Linux run passed 184 and skipped one Windows overlapped-I/O test. Three Hub tests require the optional `drive_exchange_local_hub` package; without it they also skip.

To reproduce that Linux run without a production Hub installation, extract the checked-in `evidence/hub-material-recovery-candidate-20261016.zip` into a disposable directory. Its SHA-256 is `21f736228e18f430e537e4845e69ae9a2f0727145587d5d3642746b3417de14d`; verify the archive and its manifest. Add its `src` directory and this repository to `PYTHONPATH`:

```bash
PYTHONPATH="/absolute/path/to/extracted-hub/src:$PWD" python -m unittest discover -s tests -v
```

Those tests use synthetic providers. The frozen package is an integration/testing subset, not a standalone Hub installer. Real Desktop, Windows login, Drive upload and business delivery need their own evidence; a Linux pass cannot establish them.

For documentation-only changes, verify the described commands, relative links and current-state claims. Do not add tests that merely duplicate prose. For behavioral changes, run the affected checks and only broaden testing to address a concrete risk or required gate.

## Changes and handoff

Use the user's authorized branch/PR. Keep commits scoped and write commit subjects in English. Merge, release, deployment and production enablement are separate actions; use the actual current authorization.

Update the existing current-state summary and append a concise WORK_LOG increment after substantive progress. Include the request source, exact input/output commit when known, actual executor/environment, checks and skips, remaining limitations, and the next actionable step. Report self-review as self-review; do not claim another agent ran your commands.

The current public tree has no project LICENSE. Third-party notices do not assign this project's license. Do not add a license or claim official OpenAI support without the maintainer's decision.
