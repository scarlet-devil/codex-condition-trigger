# Current state

- Goal: gate Codex work on stable, previously unseen file content.
- Status: experimental prototype, review_pending; no deployment or release claim.
- Implementation: Python watcher, immutable file snapshots, SQLite outbox, explicit existing-owner JSONL adapter.
- Validated: Linux filesystem integration and protocol test doubles; see evidence/test-results.txt.
- Unverified: Windows native watcher, actual Desktop owner connection, native tools, real model runs, external delivery and business retry integration.
- Configuration: synthetic examples only, dry mode by default; no real thread identifiers or private project paths.
- Next review: verify the actual owner's supported connection on a local test environment, then test the original thread without changing its model or permission settings.
- Workflow: implementation stays on the Draft branch/PR until separately reviewed and authorized for advancement.

Read README.md for purpose and examples, docs/DESIGN_AND_REFERENCES.md for provenance, and docs/INTEGRATION.md for the connection and receipt contract. Material changes belong in WORK_LOG.md with their actual evidence and executor.
