# Bounded restart recovery and missing-material continuation

The recovery entry point is `trial_worker.py --config <absolute config>`. It
requires a fixed `trial_expires_at_utc`. Every invocation keeps a separate
`state/worker-runs/<id>/start.json`, `stdout.jsonl`, `stderr.txt`, and `exit.json`.
The latest worker pointer is an observation: verify its PID and command before
calling it alive. A forcibly terminated process may have no exit receipt.

On Windows, an explicitly authorized operator can run `install_trial_task.ps1`
with `-Config`, `-Pythonw`, `-TaskName Codex-ConditionTrigger-<name>`, and
`-EvidenceDirectory`. Registration does not start the task. It uses the current
user's interactive logon, Limited privileges, `pythonw.exe`, and IgnoreNew.
The trigger expires at the fixed deadline; the worker independently enforces the
same immutable database deadline and STOP. A task record expires after one day.
No password, SYSTEM account, periodic model wakeup, or deadline renewal is used.
The entry point retries a recorded worker exception at most three times, thirty
seconds apart, within the same original UTC/monotonic budget. STOP prevents
retry. Two native smoke probes did not demonstrate Windows RestartOnFailure,
so the task does not rely on that setting. External process termination while
remaining logged on is not automatically recovered; the next logon or explicit
restart uses the same state. This is a bounded trial, not a permanent service.

No reboot is necessary merely to test the registered action: use a synthetic
config and `-Dry`, inspect task readback and worker receipts, then remove only
that synthetic task. An actual reboot/logon trial is a distinct acceptance item.
The production task must retain its input, exact chat, state directory and
deadline. Automatic window loading remains subject to its original supervision
constraints; a logon task does not authorize extra window actions.

## Explicit material waiting

`completed` means the model turn finished, not that research was delivered. It
continues to block until the caller either verifies business delivery and ACKs,
or explicitly requests missing-material waiting. Never use delivery ACK to skip
incomplete work.

For a batch that has a known accepted turn, write a local JSON receipt:

```json
{
  "schema": 1,
  "batch_id": "<exact batch>",
  "turn_id": "<exact correlated turn>",
  "manifest_sha256": "<SHA256 of the actual manifest file including its final newline>",
  "status": "waiting_materials",
  "reason": "<specific missing source evidence>",
  "delivery_verified": false
}
```

Run `python trigger.py --config <config> defer-materials <batch_id> --evidence
<receipt>`. During an accepted/running turn this only registers a durable request.
The normal receipt observer must first correlate completion; then the worker
changes that exact batch to `waiting_materials`. Uncertain/failed/unrelated turns
and mismatched receipts cannot use this transition. A caller-owned window lease
or unknown window action also blocks it; the current production mode has none.

A reused, lease-free cycle is closed without a window action. This releases the
serial dispatch position, not delivery responsibility: the original immutable
manifest, blobs, turn and request evidence remain. No new bytes means no replay.
The next new batch's prompt includes all undelivered waiting-material manifests
and their actual file-byte hashes. The receiver continues related material work,
keeps unrelated gaps pending, and ACKs each covered batch only after checking its
real delivery evidence. Merely receiving the continuation is not an ACK.

Old observations cannot overwrite waiting or delivered states. A later legitimate
business ACK may turn `waiting_materials` into `delivered`. Historical delivered
rows and the dedup baseline are never cleared or recreated during recovery.

The material-wait receipt is a caller attestation, not independent proof of
research completeness; receipt integrity and native completion protect the
transition, while the existing business-delivery workflow remains authoritative.

Windows references: [logon triggers](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasktrigger),
[task settings](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset),
[interactive principals](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskprincipal).
