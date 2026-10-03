# Current state

- Goal: gate work in a specified existing Codex Desktop thread on stable, previously unseen file content.
- Status: experimental prototype / review_pending; Human approved a bounded IPC-adapter trial, not deployment or release.
- Current implementation baseline: `886755e8341e79174c4d047acca1aea86e6a35ea`; Python watcher, immutable snapshots, SQLite outbox and an existing-owner JSONL/queue backend. The IPC adapter described below is not implemented by this documentation change.
- Direct cloud validation: 44 Linux tests passed at that baseline; see evidence/test-results.txt and docs/REVIEW_FIXES_20261003.md.
- Transferred Windows evidence (Kelan, report read by Alice): original suite 42 passed / 1 cleanup error / 1 skipped; cleanup-only diagnostic copy 43 passed / 1 skipped; native watcher dry checks 14/14 passed. Original failure and skip remain, and no cloud Windows rerun is claimed.
- Review corrections retained: delivered rows and ACK evidence resist stale polling; response waits enforce one absolute deadline; history correlation requires saved send intent and unique exact submitted text.
- Selected next route: separate the file-condition core from a replaceable chat interface; trial Desktop private IPC for the original-chat backend. Keep pending batches usable when the host is unavailable.
- Compatibility goal: validate the required target/dispatch/receipt/settings behavior rather than reject every package version/hash change. Current-version success does not prove future-version compatibility.
- Unverified in this project: current Desktop-owner connection and real dispatch, native tools/Hooks, external business delivery, lifecycle branches and sustained upgrade tolerance.
- State safety: legacy pending batches without dispatch text are not guessed; accepted/uncertain attempts are not automatically replayed; completed is not delivered.
- Configuration: public examples remain synthetic, dry by default. Real chat bindings and private evidence stay local.
- Next work: local Kelan follows [IPC adapter trial instructions](docs/IPC_ADAPTER_TRIAL_20261003.md), including the known test-connection cleanup correction as needed. Preserve the existing mechanism while evaluating this candidate.
- Workflow: use the existing Draft PR #1 and non-force commits; no Ready/merge or production switch is included.

Read [WORK_LOG.md](WORK_LOG.md) for decisions, alternatives, evidence attribution and incremental progress. The new trial instructions govern the proposed IPC backend; [docs/INTEGRATION.md](docs/INTEGRATION.md) still documents the current JSONL implementation.
