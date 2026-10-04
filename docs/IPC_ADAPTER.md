# Experimental Windows IPC backend

This backend connects to the already running Desktop named pipe. It does not
start a new app-server, create/resume a chat, steer an active turn, or change
Desktop settings. It is a private protocol, not an official supported API.
The JSONL queue backend remains the default.

Copy `example.windows-ipc.json` to a private local configuration and fill the
exact original thread UUID, expected project directory, and that thread's
rollout file. Never commit that configuration or a real state database.
Keep input and state directories separate. `owner_verified` stays false until
the operator has checked the intended host and authorized the bounded task.

Run `python trigger.py --config local-ipc.json probe` for read-only host and
target inspection. This opens the pipe, checks its server process and OpenAI
signature, inspects required protocol methods, initializes a client, and asks
for the configured thread's owner. It does not start a model turn. An execution
sandbox can deny pipe access; the program does not elevate itself or weaken ACLs.

Use the normal dry watcher first. For an explicitly authorized experiment,
`dispatch` attempts at most the oldest pending batch; `run --live` additionally
watches and polls. `stop` stops local work, not an already accepted model turn.
No service, autostart or background scheduler is installed by this package.

`task_instruction` optionally replaces the default project delivery workflow in
the generated prompt. Use it to keep a synthetic read-only canary separate from
real business processing. It is operator configuration, not content inferred
from incoming filenames or files. The immutable manifest and data-only boundary
are always included.

## Contracts

- Core: stable files, immutable blobs, SQLite outbox, send intent, retry policy,
  terminal delivery ACK and one-worker lock.
- Adapter: inspect, observe, prepare, send and close. Each state database is
  bound to one adapter. Existing databases migrate nullable receipt metadata;
  they default to the old JSONL backend and cannot silently switch to IPC.
- IPC methods: `initialize` v1, `thread-owner-discovery` v1 and
  `thread-follower-start-turn` v2. Frames are 4-byte little-endian lengths plus
  UTF-8 JSON, capped at 32 MiB; response matching uses request ID, method and
  routed owner, with one absolute timeout.
  Cancelling pending Windows I/O must still drain its completion before freeing
  native storage; that cancellation latency is outside the normal RPC deadline.
- Start carries the original thread and stable client-message ID and requests
  inherited thread settings. Model, cwd, approval, sandbox and permission
  overrides are omitted, including `permissions: null`.
- Busy, interrupted, absent or unknown targets retain local work. Immediately
  before writing, the adapter rechecks the rollout baseline, owner and STOP.
  There is no verified atomic idle compare-and-set in this private protocol;
  another actor can still start work in the final race window. This limitation
  precludes a general unattended concurrency guarantee.
- A successful response records `accepted` plus a native turn ID, never a queue
  ID. Only observed lifecycle records establish running/completed/failed.
  Completed remains distinct from delivered. After an uncertain write there is
  no automatic resend; `retry-connect` only applies to pre-send blocked work.
- A persisted exact prompt can reconcile a unique post-intent turn after lost
  acceptance. That fallback is text correlation, not authenticated provenance.
  Replaced, truncated or rewritten rollout history prevents reconciliation.

## Compatibility and maintenance limits

The adapter records the pipe server image, signer, archive size/hash and the
required method-version table. It discovers the current signed installation;
it does not reject an update merely because its path or whole-package hash
changed. Matching method versions alone do not prove unchanged behavior.
The bounded trial report must separately verify target, dispatch, settings,
tools, lifecycle and result on the actual installed version.

Rollout observation reads only the exact configured file, up to 64 MiB per
inspection. That is an explicit prototype limit, not a scalable history index.
The observer retains tool/action rows instead of filtering on a brittle list
of top-level context record names. Unknown or incomplete lifecycle evidence
  does not establish idle or completion. A future format change may still require
  an adapter update. No future-version or sustained production claim is made.

Historical overlapping/duplicate lifecycle starts also fail closed. A later
apparently complete turn alone does not erase an earlier unresolved turn.
This prototype does not yet implement a native owner-state snapshot to resolve
that ambiguity. Do not edit real history or bypass the check to enable a trial.

Local state contains private paths, conversation identifiers and prompts. Keep
raw evidence local and publish only a minimal sanitized report. Synthetic
tests exercise wire and state contracts; they cannot stand in for Desktop
acceptance, native tool inheritance, Hook delivery or external business ACK.
