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

## 2026-10-03 — Start static-review corrections

Actor: Alice, cloud execution. Input: the static review of head `9c658d6bffb16c53e8838f8432ac1e1319b6da6b`, reporting an ACK/poll race, an RPC deadline gap for unrelated response IDs, and history matching based only on a batch marker. The current Draft PR still has that head; all 15 local files match its Git blobs before changes.

Scope: reproduce these three paths, make bounded corrections, add regressions, and update the existing Draft PR. The source review supports the findings; runtime reproductions are still pending at this entry. No Windows installation, real owner connection, model call, automation switch, or merge is part of this round.

## 2026-10-03 — Complete correction implementation and checks

Actor: Alice, cloud execution. Reproduced all three reported paths on the unchanged baseline: seven regression methods failed, with nine failed assertions including subcases. Added atomic terminal-state protection for ACK and its evidence, a uniform absolute deadline for response consumption, and persisted exact dispatch text tied to send intent. Legacy databases add a nullable column without inventing missing send evidence.

Validation: 44 tests passed (33 original method names plus 11 new methods). Deterministic ACK/RPC barriers verify all three stale-result branches and next-batch progress. Protocol tests cover wrong-ID floods, late valid responses, ordinary user references, restart correlation, ambiguity and legacy state. A real Linux watcher subprocess with a labeled JSONL test double exits after STOP despite unrelated response traffic. One original positive history fixture now uses the actual submitted text.

Evidence: docs/REVIEW_FIXES_20261003.md, evidence/review-20261003-before.txt and evidence/test-results.txt. Source and evidence hashes are refreshed together. This remains S0 self-verification; the external input was a static report, not a runtime acceptance. Next action is review of the correction head in the same Draft PR before any local integration trial. No merge or deployment is performed.

Artifact clarification: checked the author's original 29,661-byte ZIP (CRC passed, all 15 Git blobs match the initial head); saved evidence/initial-archive-verification.json. This does not establish recipient access to that archive. It is the initial version, not the corrected implementation; the correction PR head is the next review input.
