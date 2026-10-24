"""Explicit GUI smoke fixture: synthetic catalog, inputs and in-memory transport."""

import json
import sqlite3
import threading
import time
from pathlib import Path

import trigger as tr


class FakeTransport:
    def __init__(self):
        self.sent = []
        self.turns = {}
        self.lock = threading.RLock()
        self.targets = []

    def factory(self, c, paused):
        parent = self

        class Adapter:
            def inspect(self, row):
                with parent.lock:
                    idle = not any(v == "running" for v in parent.turns.values())
                    return {
                        "can_send": idle,
                        "reason": "idle" if idle else "waiting_owner_busy",
                        "fresh_state": {
                            "status": "idle" if idle else "busy",
                            "thread_id": c["thread_id"],
                            "cwd": c["expected_cwd"],
                            "owner_id": "fake-owner",
                            "revision": 1,
                            "requested_revision": 1,
                            "request_id": "fake-query",
                        },
                    }

            def prepare(self, row):
                return {
                    "request_id": "fake-" + row["client_id"],
                    "baseline": {"bytes": 10, "inode": 1, "sha256": "a" * 64},
                }

            def evidence(self, row, metadata, turn, phase):
                return {
                    "phase": phase,
                    "source": "native_ipc"
                    if phase == "accepted"
                    else "native_turn_rollout",
                    "thread_id": c["thread_id"],
                    "cwd": c["expected_cwd"],
                    "batch_id": row["id"],
                    "manifest_sha256": tr.digest((row["manifest"] + "\n").encode()),
                    "request_id": metadata["request_id"],
                    "client_id": row["client_id"],
                    "turn_id": turn,
                    "baseline": metadata["baseline"],
                    "text_sha256": tr.digest(row["dispatch_text"].encode()),
                    "exact_text": True,
                    "post_intent": True,
                }

            def send(self, row, text, metadata):
                if paused():
                    raise tr.NotDispatched("fake_paused_before_write")
                turn = "fake-turn-" + row["id"]
                with parent.lock:
                    parent.sent.append(row["id"])
                    parent.targets.append(c["thread_id"])
                    parent.turns[turn] = "running"
                return {
                    "state": "accepted",
                    "turn_id": turn,
                    "detail": "SIMULATED ONLY",
                    "notify_evidence": self.evidence(
                        dict(row, dispatch_text=text), metadata, turn, "accepted"
                    ),
                }

            def observe(self, row):
                if not row.get("turn_id"):
                    return None
                with parent.lock:
                    state = parent.turns.get(row["turn_id"], "running")
                result = {
                    "state": state,
                    "turn_id": row["turn_id"],
                    "execution_outcome": "unknown",
                }
                if state == "ended":
                    result["notify_evidence"] = self.evidence(
                        row,
                        json.loads(row["dispatch_meta"]),
                        row["turn_id"],
                        "terminal",
                    )
                return result

            def close(self):
                pass

        return Adapter()

    def finish(self):
        with self.lock:
            for key in self.turns:
                self.turns[key] = "ended"


def prepare(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError(
            "simulation fixture requires an empty directory; use a new profile"
        )
    input_dir = root / "input"
    input_dir.mkdir()
    (input_dir / "initial.txt").write_text("initial ignored", encoding="utf8")
    dbpath = root / "state_5.sqlite"
    db = sqlite3.connect(dbpath)
    try:
        db.execute(
            "CREATE TABLE threads(id TEXT PRIMARY KEY,name TEXT,title TEXT,cwd TEXT,rollout_path TEXT,updated_at INTEGER,source TEXT,thread_source TEXT,agent_path TEXT,archived INTEGER)"
        )
        db.execute(
            "CREATE TABLE thread_spawn_edges(parent_thread_id TEXT,child_thread_id TEXT,status TEXT)"
        )
        for n in (1, 2):
            ident = f"00000000-0000-4000-8000-{n:012d}"
            cwd = root / f"project-{n}"
            cwd.mkdir()
            rollout = root / f"rollout-{n}.jsonl"
            rollout.write_text(
                json.dumps(
                    {"type": "session_meta", "payload": {"id": ident, "cwd": str(cwd)}}
                )
                + "\n",
                encoding="utf8",
            )
            db.execute(
                "INSERT INTO threads VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    ident,
                    "同名试验",
                    "same",
                    str(cwd),
                    str(rollout),
                    int(time.time()),
                    "vscode",
                    "user",
                    None,
                    0,
                ),
            )
        db.commit()
    finally:
        db.close()
    return dbpath, input_dir, FakeTransport()
