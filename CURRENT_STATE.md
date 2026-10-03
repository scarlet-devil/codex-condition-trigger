# Current state

- Goal: gate Codex work on stable, previously unseen file content.
- Status: experimental prototype, review_pending; no deployment or release claim.
- Implementation: Python watcher, immutable file snapshots, SQLite outbox, explicit existing-owner JSONL adapter.
- Validated: 44 tests pass on Linux, including the original 33 test methods and 11 static-review regressions; see evidence/test-results.txt and docs/REVIEW_FIXES_20261003.md.
- Review corrections: delivered rows and ACK evidence resist stale polling; response waits enforce one absolute deadline; history correlation requires persisted send intent and unique exact submitted text.
- Compatibility: legacy pending batches without saved dispatch text are not backfilled or guessed; they require queue evidence or checked business receipts. Text correlation is not authenticated message provenance.
- Unverified: Windows native watcher, actual Desktop owner connection, native tools, real model runs, external delivery and business retry integration.
- Configuration: synthetic examples only, dry mode by default; no real thread identifiers or private project paths.
- Next review: review the correction commit and its before/after evidence, then verify the actual owner's supported connection in a local test environment without changing model or permission settings.
- Workflow: implementation stays on the Draft branch/PR until separately reviewed and authorized for advancement.

Read README.md for purpose and examples, docs/DESIGN_AND_REFERENCES.md for provenance, and docs/INTEGRATION.md for the connection and receipt contract. Material changes belong in WORK_LOG.md with their actual evidence and executor.
