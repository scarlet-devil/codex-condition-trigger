# Work log

## 2026-10-03 — Initial prototype

Actor: Alice, cloud execution. Scope: research existing Codex event triggers and build a bounded prototype where no directly verified Windows original-thread integration was available.

Compared Codex Triggers, chokidar-cdx and gnosis-container; inspected pinned OpenAI queue/protocol source. The design separates conditions, durable batches, queue acceptance and verified business delivery. Source references are public and listed in SOURCES.json.

Implemented watchdog events, stable content snapshots, SHA-256 deduplication, SQLite state, immutable blobs, single-worker locking, and an explicit original-owner JSONL adapter. Test doubles are labeled; no real Codex thread or model was invoked.

Validation: 33 tests passed in the initial cloud Linux run, including real inotify and restart recovery. Self-review fixed worker locking so ack/status can run concurrently and bounded file capture reads. This is same-context self-review (S0), not an independent local review.

## 2026-10-03 — Prepare public repository

Authorization: the user requested a public GitHub repository containing the trigger, its purposes and its main reference ideas.

Prepared a separate public source tree. Replaced private paths and the original thread ID with synthetic examples; removed private handoff references and deployment counts. Added public-facing use cases, design attribution, integration instructions and this project entry. Generalized task messages so the trigger does not require a particular project or delivery service.

The public tree's fresh regression output is evidence/test-results.txt. Publication state is tracked by the actual remote repository and Draft PR, not inferred from this preparation record.

Remaining work: actual Windows/Desktop integration, native tool preservation, external receipt integration and business retries. This public prototype does not claim to solve those deployment-specific gaps.
