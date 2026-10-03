import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile

import trigger as tr


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.input = self.root / "input"
        self.input.mkdir()
        self.config = json.loads((Path(__file__).parents[1] / "example.windows.json").read_text())
        self.config.update(input_dir=str(self.input), state_dir=str(self.root / "state"),
                           expected_cwd=str(self.root), settle_seconds=0.15, rescan_seconds=1,
                           rpc_timeout_seconds=1, owner_verified=True)
        self.store = tr.Store(self.config)
        self.scanner = tr.StableScanner(self.store)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.store.close()
        self.output.__exit__(None, None, None)
        self.tmp.cleanup()

    def ready(self, data=b"new report"):
        (self.input / "report.md").write_bytes(data)
        self.scanner.scan(0)
        return self.scanner.scan(0.2)

    def reopen(self):
        self.store.close()
        self.store = tr.Store(self.config)
        self.scanner = tr.StableScanner(self.store)


class ConditionTests(Fixture):
    def test_quiet_never_opens_rpc(self):
        self.scanner.scan(0)
        self.scanner.scan(10)
        self.assertEqual(self.store.rows(), [])
        self.assertEqual(tr.dispatch_one(self.store, lambda c: self.fail("unexpected RPC")), "quiet")

    def test_writing_resets_stability(self):
        p = self.input / "report.md"
        p.write_text("half")
        self.scanner.scan(0)
        p.write_text("finished")
        self.assertIsNone(self.scanner.scan(0.2))
        self.assertIsNone(self.scanner.scan(0.3))
        self.assertIsNotNone(self.scanner.scan(0.4))

    def test_touch_copy_and_rename_are_deduplicated(self):
        self.ready()
        p = self.input / "report.md"
        os.utime(p, None)
        p.rename(self.input / "renamed.md")
        (self.input / "copy.md").write_bytes(b"new report")
        self.scanner.scan(1)
        self.scanner.scan(2)
        self.assertEqual(len(self.store.rows()), 1)

    def test_same_size_same_mtime_new_content_is_detected(self):
        self.ready(b"AAAA")
        p = self.input / "report.md"
        old = p.stat()
        p.write_bytes(b"BBBB")
        os.utime(p, ns=(old.st_atime_ns, old.st_mtime_ns))
        self.scanner.scan(1)
        self.scanner.scan(2)
        self.assertEqual(len(self.store.rows()), 2)

    def test_burst_is_one_batch(self):
        for i in range(10):
            (self.input / f"{i}.md").write_text(str(i))
        self.scanner.scan(0)
        self.scanner.scan(1)
        self.assertEqual(len(self.store.rows()), 1)
        self.assertEqual(len(json.loads(self.store.rows()[0]["manifest"])["files"]), 10)

    def test_restart_preserves_dedup_and_pending(self):
        batch = self.ready()
        self.reopen()
        self.scanner.scan(0)
        self.scanner.scan(1)
        self.assertEqual([r["id"] for r in self.store.rows()], [batch])
        self.assertEqual(self.store.rows()[0]["state"], "ready")

    def test_captured_version_survives_overwrite(self):
        self.ready(b"original")
        (self.input / "report.md").write_bytes(b"replacement")
        row = self.store.rows()[0]
        f = json.loads(row["manifest"])["files"][0]
        self.assertEqual((self.store.path / "blobs" / f["sha256"]).read_bytes(), b"original")

    def test_source_change_before_capture_is_rejected(self):
        (self.input / "report.md").write_bytes(b"first")
        snap = tr.snapshot(self.config)
        (self.input / "report.md").write_bytes(b"second")
        with self.assertRaises(ValueError):
            self.store.plan(snap)
        self.assertEqual(self.store.rows(), [])

    def test_partial_zip_waits_then_valid_zip_works(self):
        p = self.input / "report.zip"
        p.write_bytes(b"PK broken")
        self.scanner.scan(0)
        with self.assertRaises(zipfile.BadZipFile):
            self.scanner.scan(1)
        self.assertEqual(self.store.rows(), [])
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("report.md", "whole report")
        self.scanner.scan(2)
        self.assertIsNotNone(self.scanner.scan(3))

    def test_ready_file_is_a_batch_completeness_gate(self):
        self.config["ready_file"] = "READY"
        (self.input / "report.md").write_bytes(b"report")
        with self.assertRaises(ValueError):
            self.scanner.scan(0)
        (self.input / "READY").touch()
        self.scanner.scan(1)
        self.scanner.scan(2)
        self.assertEqual(len(json.loads(self.store.rows()[0]["manifest"])["files"]), 1)

    def test_deleted_input_root_does_not_erase_baseline(self):
        self.ready()
        (self.input / "report.md").unlink()
        self.input.rmdir()
        with self.assertRaises(ValueError):
            self.scanner.scan(1)
        self.assertEqual(len(self.store.rows()), 1)

    def test_seed_imports_only_attested_versions(self):
        p = self.root / "baseline.json"
        p.write_text(json.dumps({"verified_delivered": True, "evidence": "prior manifest",
                                "files": [{"sha256": tr.digest(b"old"), "size": 3}]}))
        self.store.seed(p)
        (self.input / "moved.md").write_bytes(b"old")
        self.scanner.scan(0)
        self.scanner.scan(1)
        self.assertEqual(self.store.rows(), [])

    def test_single_worker_but_ack_and_status_can_open(self):
        with self.assertRaises(RuntimeError):
            tr.Store(self.config)
        reader = tr.Store(self.config, worker=False)
        reader.close()

    def test_config_binding_prevents_silent_thread_switch(self):
        self.store.close()
        other = {**self.config, "thread_id": "00000000-0000-0000-0000-000000000001"}
        with self.assertRaises(ValueError):
            tr.Store(other)
        self.store = tr.Store(self.config)

    def test_stop_blocks_planning_and_sending(self):
        (self.store.path / "STOP").touch()
        self.assertIsNone(self.ready())
        self.assertEqual(tr.dispatch_one(self.store, lambda c: self.fail("unexpected RPC")), "paused")

    @unittest.skipIf(os.name == "nt", "symlink creation depends on Windows developer mode")
    def test_symlink_input_is_not_followed(self):
        target = self.root / "outside"
        target.write_text("outside")
        (self.input / "link").symlink_to(target)
        with self.assertRaises(ValueError):
            tr.snapshot(self.config)


class FakeRPC:
    def __init__(self, c):
        self.c = c
        self.calls = []
        self.thread = {"id": c["thread_id"], "cwd": c["expected_cwd"],
                       "status": {"type": "idle"}, "turns": []}
        self.queued = []
        self.lose_ack = False
        self.count = 0

    def close(self):
        pass

    def request(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == "thread/read":
            return {"thread": self.thread}
        if method == "thread/queue/list":
            return {"data": self.queued, "nextCursor": None}
        if method == "thread/resume":
            self.thread["status"]["type"] = "idle"
            return {"thread": self.thread}
        if method == "thread/queue/add":
            self.count += 1
            item = {"id": "submission-1", "clientUserMessageId": params["clientUserMessageId"], "input": params["input"]}
            self.queued.append(item)
            if self.lose_ack:
                raise TimeoutError("reply lost after acceptance")
            return {"queuedSubmission": item}
        raise AssertionError(method)


class DispatchTests(Fixture):
    def setUp(self):
        super().setUp()
        self.batch = self.ready()
        self.rpc = FakeRPC(self.config)

    def send(self, **kwargs):
        return tr.dispatch_one(self.store, lambda c: self.rpc, **kwargs)

    def test_idle_enqueues_exact_thread_without_policy_overrides(self):
        self.assertEqual(self.send(), "queued")
        p = next(p for m, p in self.rpc.calls if m == "thread/queue/add")
        self.assertEqual(p["threadId"], self.config["thread_id"])
        self.assertEqual(set(p), {"threadId", "input", "clientUserMessageId"})
        self.assertNotIn("delivered", [r["state"] for r in self.store.rows()])

    def test_busy_queues_without_steering_or_starting(self):
        self.rpc.thread["status"]["type"] = "active"
        self.assertEqual(self.send(), "queued")
        self.assertEqual([m for m, _ in self.rpc.calls], ["thread/read", "thread/queue/list", "thread/queue/add"])

    def test_unloaded_waits_without_falsely_claiming_wake(self):
        self.rpc.thread["status"]["type"] = "notLoaded"
        self.assertEqual(self.send(), "waiting_owner_resume")
        self.assertEqual(self.rpc.count, 0)
        self.assertEqual(self.store.rows()[0]["state"], "ready")

    def test_opt_in_resume_has_only_thread_id(self):
        self.config["resume_unloaded"] = True
        self.rpc.thread["status"]["type"] = "notLoaded"
        self.assertEqual(self.send(), "queued")
        self.assertEqual(next(p for m, p in self.rpc.calls if m == "thread/resume"), {"threadId": self.config["thread_id"]})

    def test_resume_does_not_start_foreign_pending_work(self):
        self.config["resume_unloaded"] = True
        self.rpc.thread["status"]["type"] = "notLoaded"
        self.rpc.queued = [{"id": "other", "clientUserMessageId": "other"}]
        self.assertEqual(self.send(), "waiting_owner_resume")
        self.assertNotIn("thread/resume", [m for m, _ in self.rpc.calls])

    def test_wrong_thread_or_cwd_never_gets_mutated(self):
        self.rpc.thread["cwd"] = "different"
        self.assertEqual(self.send(now=0), "pending")
        self.assertEqual(self.rpc.count, 0)

    def test_ack_loss_reconciles_without_reenqueue_after_restart(self):
        self.rpc.lose_ack = True
        self.assertEqual(self.send(), "uncertain")
        self.reopen()
        self.rpc.lose_ack = False
        self.assertEqual(self.send(), "queued")
        self.assertEqual(self.rpc.count, 1)

    def test_accepted_missing_from_queue_is_not_blindly_retried(self):
        self.send()
        self.rpc.queued = []
        self.assertEqual(self.send(), "uncertain")
        self.assertEqual(self.send(), "uncertain")
        self.assertEqual(self.rpc.count, 1)

    def test_recovery_marks_crashed_send_uncertain(self):
        self.store.update(self.batch, "sending")
        self.reopen()
        self.assertEqual(self.store.rows()[0]["state"], "uncertain")
        self.assertEqual(self.send(), "uncertain")
        self.assertEqual(self.rpc.count, 0)

    def test_pre_send_offline_retries_are_bounded(self):
        def offline(c):
            raise OSError("offline")
        for i in range(self.config["max_connect_attempts"]):
            tr.dispatch_one(self.store, offline, now=i * 1000)
        self.assertEqual(self.store.rows()[0]["state"], "blocked")
        tr.dispatch_one(self.store, lambda c: self.fail("must wait for operator"), now=99999)

    def test_running_and_completion_need_matching_user_message(self):
        self.send()
        self.rpc.queued = []
        self.rpc.thread["turns"] = [{"id": "turn-1", "status": "completed", "items": [
            {"type": "userMessage", "content": [{"type": "text", "text": "batch_id=" + self.batch}]}]}]
        self.assertEqual(self.send(), "completed")
        evidence = self.root / "receipt.json"
        evidence.write_text('{"verified": true}')
        ack_store = tr.Store(self.config, worker=False)
        ack_store.acknowledge(self.batch, evidence)
        ack_store.close()
        self.assertEqual(self.store.rows()[0]["state"], "delivered")

    def test_assistant_text_cannot_be_a_dispatch_receipt(self):
        self.store.update(self.batch, "uncertain")
        self.rpc.thread["turns"] = [{"id": "turn-1", "status": "completed", "items": [
            {"type": "agentMessage", "content": [{"type": "text", "text": "batch_id=" + self.batch}]}]}]
        self.assertEqual(self.send(), "uncertain")

    def test_interrupted_thread_is_left_for_owner(self):
        self.rpc.thread["turns"] = [{"id": "turn-0", "status": "interrupted", "items": []}]
        self.assertEqual(self.send(), "waiting_owner_after_interrupt")
        self.assertEqual(self.rpc.count, 0)

    def test_unverified_owner_never_opens_proxy(self):
        self.config["owner_verified"] = False
        with self.assertRaises(ValueError):
            tr.dispatch_one(self.store, lambda c: self.fail("must not connect"))

    def test_next_batch_waits_for_verified_delivery(self):
        self.send()
        (self.input / "report.md").write_text("second version")
        self.scanner.scan(1)
        self.scanner.scan(2)
        self.send()
        self.assertEqual(self.rpc.count, 1)
        self.assertEqual(len(self.store.rows()), 2)


class ProtocolProcessTests(Fixture):
    def test_real_jsonl_proxy_process_handshake_and_queue(self):
        state = self.root / "fake-owner.json"
        state.write_text(json.dumps({"thread_id": self.config["thread_id"], "cwd": self.config["expected_cwd"], "queue": []}))
        self.config["transport_command"] = [sys.executable, str(Path(__file__).with_name("fake_owner.py")), str(state)]
        self.ready()
        self.assertEqual(tr.dispatch_one(self.store), "queued")
        self.assertEqual(tr.dispatch_one(self.store), "queued")
        server = json.loads(state.read_text())
        self.assertEqual(len(server["queue"]), 1)
        self.assertEqual(server["initializations"], 2)


class WatcherProcessTests(Fixture):
    def test_native_watcher_and_offline_restart_recovery(self):
        self.store.close()
        config_path = self.root / "config.json"
        config_path.write_text(json.dumps(self.config))
        script = str(Path(__file__).parents[1] / "trigger.py")
        log = self.root / "watcher.log"
        def launch():
            output = log.open("a")
            return subprocess.Popen([sys.executable, script, "--config", str(config_path), "run"], stdout=output, stderr=output), output
        def wait_for_count(count):
            end = time.monotonic() + 6
            while time.monotonic() < end:
                import sqlite3
                db = sqlite3.connect(self.root / "state" / "state.sqlite")
                actual = db.execute("SELECT count(*) FROM batches").fetchone()[0]
                db.close()
                if actual == count:
                    return
                time.sleep(0.05)
            self.fail(log.read_text())
        p, out = launch()
        try:
            time.sleep(0.3)
            (self.input / "one.md").write_text("first")
            wait_for_count(1)
            (self.root / "state" / "STOP").touch()
            self.assertEqual(p.wait(timeout=5), 0)
        finally:
            if p.poll() is None: p.kill(); p.wait()
            out.close()
        (self.input / "two.md").write_text("during downtime")
        (self.root / "state" / "STOP").unlink()
        p, out = launch()
        try:
            wait_for_count(2)
            (self.root / "state" / "STOP").touch()
            self.assertEqual(p.wait(timeout=5), 0)
        finally:
            if p.poll() is None: p.kill(); p.wait()
            out.close()
            self.store = tr.Store(self.config)
        self.assertIn('"backend":"InotifyObserver"' if sys.platform.startswith("linux") else '"event":"watching"', log.read_text())
        self.assertNotIn("queue_accepted", log.read_text())


if __name__ == "__main__":
    unittest.main()
