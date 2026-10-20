# Codex Condition Trigger

**Give an existing Codex conversation new work when files actually change.**

[简体中文](README.zh-CN.md) · [AI / contributor entry](AGENTS.md) · [Current status](CURRENT_STATE.md)

A small, experimental Python service for workflows where incoming files should trigger a review or analysis in an existing conversation. The local program detects changes, waits for stable bytes, deduplicates content and freezes a batch before handing it to the selected chat adapter.

For example: a research agent writes a report, the report stops changing, and the project conversation receives its exact frozen version for review. No new content and no pending work means no model turn is requested.

This is a community project, unaffiliated with OpenAI. The file watcher can be tried locally; live Desktop integration depends on a verified installation and conversation owner. It is not a general-purpose automation platform or a supported public Desktop API.

## What it does

- Watches files using `watchdog`, with startup and periodic scans to catch missed events.
- Uses a stability window and SHA-256 content hashes to avoid processing incomplete or duplicate bytes.
- Stores immutable input versions, batch manifests and delivery state in SQLite.
- Supports separate JSONL queue and experimental Windows Desktop IPC adapters.
- Tracks watcher health, execution outcomes and verified business delivery separately.
- Freezes output files in a durable upload outbox; an optional adapter uses an existing Drive Exchange Hub to recover uploads by a persistent remote ID.

An uncertain send stays uncertain until it can be reconciled. A finished model turn is not a delivery receipt. The system does not promise exactly-once execution.

## Try it without a model

Requires Python 3.10+ and `watchdog==6.0.0`. Linux/Python 3.12 was used for the latest cloud regression run; Windows-specific evidence is linked below.

### Linux

```bash
git clone https://github.com/scarlet-devil/codex-condition-trigger.git
cd codex-condition-trigger
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp example.linux.json local-test.json
.venv/bin/python -c 'import json; from pathlib import Path; p=Path("local-test.json"); c=json.loads(p.read_text()); c["settle_seconds"]=2; p.write_text(json.dumps(c, indent=2))'
mkdir -p /tmp/codex-trigger-demo/inbox /tmp/codex-trigger-demo/project
printf 'A report is ready for review.\n' > /tmp/codex-trigger-demo/inbox/report.txt
.venv/bin/python trigger.py --config local-test.json scan
.venv/bin/python trigger.py --config local-test.json status
```

### Windows PowerShell

After cloning the repository and entering its directory:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$demo = Join-Path $env:TEMP "codex-trigger-demo"
$config = Get-Content .\example.windows.json -Raw | ConvertFrom-Json
$config.input_dir = Join-Path $demo "inbox"
$config.state_dir = Join-Path $demo "state"
$config.expected_cwd = Join-Path $demo "project"
$config.settle_seconds = 2
$config | ConvertTo-Json -Depth 8 | Set-Content .\local-test.json -Encoding UTF8
New-Item -ItemType Directory -Force $config.input_dir, $config.expected_cwd
"A report is ready for review." | Set-Content (Join-Path $config.input_dir "report.txt") -Encoding UTF8
.\.venv\Scripts\python.exe .\trigger.py --config .\local-test.json scan
.\.venv\Scripts\python.exe .\trigger.py --config .\local-test.json status
```

A fresh demo produces `batch_ready`; `status` shows a `ready` batch. Repeat `scan` without changing the bytes: no second batch should appear. The all-zero thread UUID is a placeholder used only for this dry demo.

To keep watching, use `run` without `--live`. In another terminal, use `stop` to request a persistent pause:

```bash
# Windows: replace the Python executable with .\.venv\Scripts\python.exe.
.venv/bin/python trigger.py --config local-test.json run
# In another terminal:
.venv/bin/python trigger.py --config local-test.json stop
.venv/bin/python trigger.py --config local-test.json status
```

The watcher exits on STOP; Ctrl+C also exits the current watcher. After an intentional demo pause, `unpause` clears STOP unless a bound trial has expired. Already accepted model work must be handled in its own host. Keep demo state separate from real work.

## Connecting a real conversation

| Component | What you must supply |
| --- | --- |
| File input | Absolute input, state and project paths; input and state trees must not overlap. The default stability window is 120 seconds. |
| JSONL queue | A verified connection to the actual existing host. Starting a second app-server with the same UUID does not establish ownership. |
| Windows Desktop IPC | The exact thread, working directory, rollout path and verified installed Desktop build. Owner absence or ambiguity must be resolved before dispatch. |
| Native result collection | Explicit `native_result_collection: true` for the verified Desktop IPC setup. The default is off. |
| Upload recovery | An already installed, authorized Drive Exchange Hub with material-recovery support, a registered project/route and a configured `delivery_command`. This repository is not a standalone Drive client. |

Start with the [integration guide](docs/INTEGRATION.md), [Desktop IPC details](docs/IPC_ADAPTER.md) and [native collection / upload design](docs/NATIVE_DELIVERY_INTEGRATION_20261015.md). Dated reports describe their original checkpoint; [CURRENT_STATE.md](CURRENT_STATE.md) gives the latest accepted scope.

Live commands can submit work or transfer files. `run --live` and `dispatch` are separate from the dry demo. `delivery-resume` only resumes frozen uploads: it neither reruns the model nor acknowledges business delivery. The optional Hub adapter accepts files up to **8 MiB**; the generic outbox limit is **20 MiB**.

## Evidence and limits

| Area | Verified scope |
| --- | --- |
| Automatic triggering | Real Windows watcher trials dispatched two successive synthetic batches into the original conversation, with caller-verified results. |
| Login recovery | A real Windows login started an isolated dry watcher, produced a ready batch and stopped within its deadline. |
| Native outcomes | Implemented and reviewed; a loaded chat was read through real IPC. The original production target's full business workflow remains unverified. |
| Upload recovery | A real Drive canary recovered after the client discarded its receipt, using the same remote ID and byte readback. |
| Latest regression | 185 tests: **184 passed, 1 Windows-only test skipped** on cloud Linux, including the three optional outbox-to-Hub tests. See the [validation record](evidence/alice-merge-validation-20261020.json). |

These are separate experiments, not a single proof of unattended operation. Hub startup after reboot and the original target's complete business workflow remain follow-up work.

Window loading is off by default. The current Windows UI backend requires an explicitly supervised, no-navigation interval of at most **600 seconds**; arbitrary-navigation unattended window cleanup is not validated. No model, permission or sandbox overrides are sent by the chat adapter. A merge does not activate an old trial or clear its STOP/deadline.

Other limits: file conditions only (no webhook service, GUI or rule language); byte deduplication is not semantic deduplication; historical blobs have no automatic retention policy. A READY marker requires the producer to remove the old marker before writing and recreate it last.

## Development

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Use your virtual environment's Python. Some platform or optional Hub tests skip when their requirements are absent; always report the actual skip reasons. The 184-pass result above used the frozen Hub candidate on `PYTHONPATH`, not just a fresh clone. See [AGENTS.md](AGENTS.md) for the exact reproduction and code map.

For a bug report, include the commit, OS/Python version, adapter, sanitized configuration, reproduction steps and expected/actual result. Keep private conversation data and credentials out of public issues.

## References and license status

The design draws on OpenAI Codex queue semantics, Codex Triggers' separation of detection and delivery, and CodexAgentControl's documented IPC protocol. The actual file-watching dependency is watchdog. See [design references](docs/DESIGN_AND_REFERENCES.md), [pinned sources](SOURCES.json) and [third-party notices](THIRD_PARTY_NOTICES.md).

This repository does not yet contain a project LICENSE. The MIT text in `THIRD_PARTY_NOTICES.md` belongs to the referenced third-party project; it is not this project's license.

