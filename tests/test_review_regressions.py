"""Regressions for the 2026-10-03 static review; no real Codex connection."""
import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import time
import unittest
from unittest import mock

import trigger as tr
from test_trigger import FakeRPC, Fixture


class AckRaceTests(Fixture):
    def check_stale_poll(self, result):
        batch = self.ready()
        rpc = FakeRPC(self.config)
        self.assertEqual(tr.dispatch_one(self.store, lambda c: rpc), "queued")
        text = rpc.queued[0]["input"][0]["text"]
        (self.input / "report.md").write_text("next version")
        self.scanner.scan(1)
        self.scanner.scan(2)
        if result == "completed":
            rpc.thread["turns"] = [{"id": "turn-1", "status": "completed", "items": [
                {"type": "userMessage", "content": [{"type": "text", "text": text}]}]}]
        if result != "queued":
            rpc.queued = []

        # Freeze the RPC result, commit ACK on a second SQLite connection,
        # then release the old result. No timing-based race is required.
        poll_waiting, ack_committed = threading.Event(), threading.Event()
        receipt = self.root / "receipt.json"
        receipt.write_text('{"verified": true}')
        acknowledged, errors = [], []
        original_request = rpc.request

        def delayed_request(method, params):
            response = copy.deepcopy(original_request(method, params))
            if method == "thread/queue/list":
                poll_waiting.set()
                if not ack_committed.wait(3):
                    raise AssertionError("ACK did not reach its barrier")
            return response

        def ack():
            try:
                if not poll_waiting.wait(3):
                    raise AssertionError("poll did not reach its barrier")
                other = tr.Store(self.config, worker=False)
                try:
                    other.acknowledge(batch, receipt)
                    acknowledged.append(next(r for r in other.rows() if r["id"] == batch))
                finally:
                    other.close()
            except BaseException as exc:
                errors.append(exc)
            finally:
                ack_committed.set()

        rpc.request = delayed_request
        actor = threading.Thread(target=ack)
        actor.start()
        try:
            polled_state = tr.dispatch_one(self.store, lambda c: rpc)
        finally:
            actor.join(timeout=4)
            rpc.request = original_request
        self.assertFalse(actor.is_alive())
        if errors:
            raise errors[0]
        current = next(r for r in self.store.rows() if r["id"] == batch)
        self.assertEqual(current["state"], "delivered")
        self.assertEqual(current, acknowledged[0])  # includes evidence and its hash
        self.assertEqual(polled_state, "delivered")
        rpc.thread["turns"] = []
        self.assertEqual(tr.dispatch_one(self.store, lambda c: rpc), "queued")
        self.assertEqual(rpc.count, 2)
        self.assertEqual(next(r for r in self.store.rows() if r["id"] == batch), acknowledged[0])

    def test_ack_survives_stale_completed_poll(self):
        self.check_stale_poll("completed")

    def test_ack_survives_stale_queued_poll(self):
        self.check_stale_poll("queued")

    def test_ack_survives_stale_uncertain_poll(self):
        self.check_stale_poll("uncertain")


class RPCDeadlineTests(unittest.TestCase):
    def client(self, inbox):
        rpc = tr.StdioRPC.__new__(tr.StdioRPC)
        rpc.timeout, rpc.serial, rpc.inbox = 1, 0, inbox
        rpc._write = lambda message: None
        return rpc

    def test_continuous_wrong_response_ids_obey_deadline(self):
        clock = [0.0]

        class Noise:
            calls = 0

            def get(self, timeout):
                self.calls += 1
                clock[0] += 0.25
                if self.calls > 8:
                    raise AssertionError("wrong-ID stream bypassed the RPC deadline")
                return {"id": "unrelated", "result": {}}

        inbox = Noise()
        with mock.patch.object(tr.time, "monotonic", side_effect=lambda: clock[0]):
            with self.assertRaises(TimeoutError):
                self.client(inbox).request("thread/read", {})
        self.assertLessEqual(clock[0], 1.0)
        self.assertLessEqual(inbox.calls, 4)

    def test_matching_response_after_deadline_is_rejected(self):
        clock = [0.0]

        class Late:
            def get(self, timeout):
                clock[0] = 2.0
                return {"id": 1, "result": {"late": True}}

        with mock.patch.object(tr.time, "monotonic", side_effect=lambda: clock[0]):
            with self.assertRaises(TimeoutError):
                self.client(Late()).request("thread/read", {})


class HistoryReceiptTests(Fixture):
    def setUp(self):
        super().setUp()
        self.batch = self.ready()
        self.rpc = FakeRPC(self.config)

    def send(self):
        return tr.dispatch_one(self.store, lambda c: self.rpc)

    def history(self, text, turn_id="turn-1"):
        return {"id": turn_id, "status": "completed", "items": [
            {"type": "userMessage", "content": [{"type": "text", "text": text}]}]}

    def test_unsent_user_reference_cannot_replace_first_dispatch(self):
        self.rpc.thread["turns"] = [self.history("Explain why batch_id=" + self.batch + " is still pending.")]
        self.assertEqual(self.send(), "queued")
        self.assertEqual(self.rpc.count, 1)

    def test_queued_user_references_cannot_become_receipts(self):
        self.send()
        sent_text = self.rpc.queued[0]["input"][0]["text"]
        self.rpc.queued = []
        for text in ("Explain batch_id=" + self.batch, "> " + sent_text, sent_text + "\nWhat does this mean?"):
            with self.subTest(reference=text[:30]):
                self.store.update(self.batch, "queued")
                self.rpc.thread["turns"] = [self.history(text)]
                self.assertEqual(self.send(), "uncertain")
                self.assertIsNone(self.store.rows()[0]["turn_id"])
        self.assertEqual(self.rpc.count, 1)

    def test_exact_sent_text_recovers_after_ack_loss_and_restart(self):
        self.rpc.lose_ack = True
        self.assertEqual(self.send(), "uncertain")
        sent_text = self.rpc.queued[0]["input"][0]["text"]
        self.reopen()
        self.rpc.queued = []
        self.rpc.thread["turns"] = [self.history(sent_text)]
        self.assertEqual(self.send(), "completed")
        self.assertEqual(self.rpc.count, 1)

    def test_ambiguous_identical_history_messages_remain_uncertain(self):
        self.send()
        sent_text = self.rpc.queued[0]["input"][0]["text"]
        self.rpc.queued = []
        self.rpc.thread["turns"] = [self.history(sent_text, "one"), self.history(sent_text, "two")]
        self.assertEqual(self.send(), "uncertain")
        self.assertEqual(self.rpc.count, 1)

    def test_legacy_pending_batch_is_not_given_invented_history_evidence(self):
        self.send()
        sent_text = self.rpc.queued[0]["input"][0]["text"]
        self.store.close()
        # Recreate the original on-disk batch schema, preserving actual rows.
        with sqlite3.connect(self.root / "state" / "state.sqlite") as db:
            db.executescript("""
              ALTER TABLE batches RENAME TO saved_batches;
              CREATE TABLE batches(
                id TEXT PRIMARY KEY, state TEXT NOT NULL, manifest TEXT NOT NULL,
                client_id TEXT NOT NULL, submission TEXT, turn_id TEXT,
                attempts INTEGER NOT NULL DEFAULT 0, next_try REAL NOT NULL DEFAULT 0,
                detail TEXT, created REAL NOT NULL);
              INSERT INTO batches SELECT id,state,manifest,client_id,submission,turn_id,
                attempts,next_try,detail,created FROM saved_batches;
              DROP TABLE saved_batches;
            """)
        self.store = tr.Store(self.config)
        self.assertIsNone(self.store.rows()[0].get("dispatch_text"))
        self.rpc.queued = []
        self.rpc.thread["turns"] = [self.history(sent_text)]
        self.assertEqual(self.send(), "uncertain")
        self.assertEqual(self.rpc.count, 1)
        receipt = self.root / "legacy-receipt.json"
        receipt.write_text('{"verified": true}')
        self.store.acknowledge(self.batch, receipt)
        self.assertEqual(self.store.rows()[0]["state"], "delivered")


class WatcherDeadlineTests(Fixture):
    def test_stop_after_wrong_id_flood_returns_from_live_watcher(self):
        self.ready()
        self.store.close()
        state = self.root / "fake-owner.json"
        state.write_text(json.dumps({"thread_id": self.config["thread_id"],
                                    "cwd": self.config["expected_cwd"], "queue": [],
                                    "mode": "wrong_id_flood"}))
        self.config["rpc_timeout_seconds"] = 0.5
        self.config["transport_command"] = [sys.executable, str(Path(__file__).with_name("fake_owner.py")), str(state)]
        config = self.root / "config.json"
        config.write_text(json.dumps(self.config))
        log = self.root / "watcher.log"
        script = str(Path(__file__).parents[1] / "trigger.py")
        with log.open("w") as output:
            process = subprocess.Popen([sys.executable, script, "--config", str(config), "run", "--live"],
                                       stdout=output, stderr=output)
            try:
                end = time.monotonic() + 4
                while True:
                    try:
                        started = json.loads(state.read_text()).get("noise_started", False)
                    except json.JSONDecodeError:
                        started = False
                    if started:
                        break
                    if process.poll() is not None or time.monotonic() >= end:
                        self.fail("fake proxy never started its wrong-ID stream: " + log.read_text())
                    time.sleep(0.01)
                (self.root / "state" / "STOP").touch()
                self.assertEqual(process.wait(timeout=3), 0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                self.store = tr.Store(self.config)
        self.assertIn('"watcher_stopped"', log.read_text())
        self.assertIn('"reason":"TimeoutError"', log.read_text())
        self.assertNotIn('"queue_accepted"', log.read_text())


if __name__ == "__main__":
    unittest.main()
