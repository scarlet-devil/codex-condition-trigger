import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import trigger as tr
from test_notify import FakeDesktop


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input = self.root / "input"
        self.input.mkdir()
        p = mock.patch.object(
            tr, "target_registry_root", return_value=self.root / "registry"
        )
        p.start()
        self.addCleanup(p.stop)
        self.fake = FakeDesktop()
        self.controllers = []
        self.addCleanup(self.cleanup_controllers)
        self.rollout = self.root / "rollout.jsonl"
        self.id = "00000000-0000-4000-8000-000000000001"
        self.rollout.write_text(
            json.dumps(
                {
                    "type": "session_meta",
                    "payload": {"id": self.id, "cwd": str(self.root)},
                }
            )
            + "\n",
            encoding="utf8",
        )
        self.selection = {
            "id": self.id,
            "selection_key": self.id,
            "cwd": str(self.root),
            "rollout_path": str(self.rollout),
            "display_name": "Duplicate",
        }

    def cleanup_controllers(self):
        for c in self.controllers:
            c.close()
        for c in self.controllers:
            self.wait(lambda c=c: not c.view()["alive"], limit=8)

    def controller(self, **kw):
        from simple_controller import Controller

        c = Controller(
            self.root / "rules",
            adapter_factory=self.fake.factory,
            simulation=True,
            dispatch_interval=0.05,
            **kw,
        )
        self.controllers.append(c)
        return c

    def wait(self, fn, limit=8):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            if fn():
                return
            time.sleep(0.02)
        self.fail(
            "bounded condition wait expired: "
            + repr([c.view() for c in self.controllers])
        )

    def preview(self, c, **kw):
        c.update(
            dict(
                folder=str(self.input),
                condition="new_content_stable",
                selection=self.selection,
                settle_seconds=0.1,
                **kw,
            )
        )
        c.preview()
        self.wait(lambda: not c.view()["command_busy"])
        self.assertIsNotNone(c.view()["preview"], c.view())
        return c.view()["preview"]

    def enable(self, c):
        self.preview(c)
        c.enable()
        self.wait(lambda: c.view()["worker_started"] or c.view()["error"])
        self.assertIsNone(c.view()["error"], c.view())

    def status(self, c):
        c.refresh()
        self.wait(lambda: not c.view()["refresh_busy"])
        return c.view()["status"]

    def test_real_watcher_two_batches_pause_resume_and_baseline(self):
        (self.input / "old.txt").write_text("old")
        c = self.controller()
        self.enable(c)
        self.wait(lambda: self.status(c).get("monitoring") == "listening")
        self.assertEqual(self.status(c)["initial_files"], 1)
        (self.input / "a.txt").write_text("A")
        self.wait(lambda: len(self.fake.sent) == 1)
        (self.input / "b.txt").write_text("B")
        time.sleep(0.45)
        self.assertEqual(len(self.fake.sent), 1)
        self.fake.turns["turn-" + self.fake.sent[0]] = ("ended", "unknown")
        self.fake.idle = True
        self.wait(lambda: len(self.fake.sent) == 2)
        c.pause()
        self.wait(lambda: not c.view()["alive"])
        before = self.status(c)
        self.assertFalse(before["enabled"])
        self.assertTrue(
            all(x["business_delivery"] == "unverified" for x in before["batches"])
        )
        (self.input / "c.txt").write_text("C")
        c.resume()
        self.wait(lambda: c.view()["worker_started"])
        time.sleep(0.3)
        self.assertEqual(len(self.fake.sent), 2)
        self.fake.turns["turn-" + self.fake.sent[1]] = ("ended", "unknown")
        self.fake.idle = True
        self.wait(lambda: len(self.fake.sent) == 3)
        self.assertEqual(self.status(c)["initial_files"], 1)

    def test_stale_preview_cannot_enable_and_preview_does_not_write(self):
        import rule_service

        c = self.controller()
        entered = threading.Event()
        release = threading.Event()
        original = rule_service.preview

        def blocked(*a, **kw):
            entered.set()
            release.wait(3)
            return original(*a, **kw)

        c.update(
            {
                "folder": str(self.input),
                "condition": "new_content_stable",
                "selection": self.selection,
                "settle_seconds": 0.1,
            }
        )
        with mock.patch.object(rule_service, "preview", side_effect=blocked):
            c.preview()
            self.assertTrue(entered.wait(2))
            c.update(dict(c.form, instruction="new"))
            release.set()
            self.wait(lambda: not c.view()["command_busy"])
        self.assertIsNone(c.view()["preview"])
        with self.assertRaises(ValueError):
            c.enable()
        self.assertFalse((self.root / "rules").exists())

    def test_pause_during_enable_probe_cannot_start_worker(self):
        c = self.controller()
        self.preview(c)
        entered = threading.Event()
        release = threading.Event()
        original = self.fake.inspect

        def blocked(row):
            entered.set()
            release.wait(3)
            return original(row)

        with mock.patch.object(self.fake, "inspect", side_effect=blocked):
            c.enable()
            self.assertTrue(entered.wait(2))
            c.pause()
            release.set()
            self.wait(lambda: not c.view()["alive"])
        self.assertFalse(c.view()["worker_started"])
        self.assertEqual(self.fake.sent, [])
        self.assertFalse(self.status(c)["enabled"])

    def test_worker_start_failure_preserves_disabled_rule_and_baseline(self):
        c = self.controller(
            run_fn=mock.Mock(side_effect=RuntimeError("observer start failed"))
        )
        self.preview(c)
        c.enable()
        self.wait(lambda: not c.view()["alive"])
        self.assertIn("observer start failed", c.view()["error"])
        self.assertFalse(self.status(c)["enabled"])
        self.assertTrue((Path(c.config["state_dir"]) / "rule.json").is_file())

    def test_reopen_does_not_resume_and_missing_db_is_not_recreated(self):
        from simple_controller import saved_rules

        c = self.controller()
        self.enable(c)
        c.close()
        self.wait(lambda: not c.view()["alive"])
        d = self.controller()
        entries = saved_rules(d.home)
        self.assertEqual(len(entries), 1)
        d.load(entries[0]["path"])
        self.wait(lambda: not d.view()["command_busy"])
        self.assertFalse(d.view()["worker_started"])
        self.assertFalse(d.view()["alive"])
        db = Path(d.config["state_dir"]) / "state.sqlite"
        db.unlink()
        d.refresh()
        self.wait(lambda: not d.view()["refresh_busy"])
        self.assertIn("needs_review", d.view()["error"])
        self.assertFalse(db.exists())

    def test_no_native_fallback_and_duplicate_enable_target(self):
        with self.assertRaises(ValueError):
            from simple_controller import Controller

            Controller(self.root / "rules", adapter_factory=None, simulation=True)
        c = self.controller()
        self.enable(c)
        with self.assertRaises(ValueError):
            c.enable()
        d = self.controller()
        self.preview(d)
        d.enable()
        self.wait(lambda: not d.view()["alive"])
        self.assertIsNotNone(d.view()["error"])
        self.assertTrue(c.view()["worker_started"])

    def test_health_requires_current_worker_scan_and_refresh_has_no_ipc(self):
        c = self.controller()
        self.enable(c)
        self.wait(lambda: self.status(c).get("monitoring") == "listening")
        c.pause()
        self.wait(lambda: not c.view()["alive"])
        with mock.patch.object(
            self.fake, "inspect", side_effect=AssertionError("status used IPC")
        ):
            s = self.status(c)
        self.assertNotEqual(s["monitoring"], "listening")

    def test_unknown_write_survives_reopen_without_resend(self):
        self.fake.loss = True
        c = self.controller()
        self.enable(c)
        (self.input / "a.txt").write_text("A")
        self.wait(lambda: len(self.fake.sent) == 1)
        self.wait(
            lambda: any(x["state"] == "uncertain" for x in self.status(c)["batches"])
        )
        c.pause()
        self.wait(lambda: not c.view()["alive"])
        c.resume()
        self.wait(lambda: c.view()["worker_started"])
        time.sleep(0.5)
        self.assertEqual(len(self.fake.sent), 1)

    def test_enable_baseline_count_is_rescanned_not_preview_count(self):
        c = self.controller()
        self.preview(c)
        (self.input / "new.txt").write_text("new")
        c.enable()
        self.wait(lambda: c.view()["worker_started"])
        self.assertEqual(self.status(c)["initial_files"], 1)

    def test_progress_write_survives_short_lived_external_reader(self):
        from types import SimpleNamespace

        from worker_health import Progress

        p = Progress(SimpleNamespace(path=self.root), False)
        opened = threading.Event()

        def reader():
            with p.path.open("rb"):
                opened.set()
                time.sleep(0.08)

        t = threading.Thread(target=reader)
        t.start()
        self.assertTrue(opened.wait(1))
        p.write("after_reader")
        t.join(1)
        self.assertEqual(json.loads(p.path.read_bytes())["phase"], "after_reader")

    def test_close_is_responsive_and_waits_for_inflight_probe(self):
        c = self.controller()
        self.preview(c)
        entered = threading.Event()
        release = threading.Event()
        original = self.fake.inspect

        def blocked(row):
            entered.set()
            release.wait(3)
            return original(row)

        with mock.patch.object(self.fake, "inspect", side_effect=blocked):
            c.enable()
            self.assertTrue(entered.wait(2))
            start = time.monotonic()
            c.close()
            self.assertLess(time.monotonic() - start, 0.3)
            self.assertFalse(c.view()["closed"])
            release.set()
            self.wait(lambda: c.view()["closed"])

    def test_failed_capability_retry_reuses_same_rule(self):
        c = self.controller()
        self.preview(c)
        self.fake.idle = False
        c.enable()
        self.wait(lambda: not c.view()["alive"])
        first = dict(c.config)
        self.assertFalse(self.status(c)["initialized"])
        self.fake.idle = True
        c.enable()
        self.wait(lambda: c.view()["worker_started"])
        self.assertEqual(c.config["rule_id"], first["rule_id"])
        self.assertEqual(len(list(c.home.glob("*/simple-rule.json"))), 1)

    def test_second_form_resume_cannot_pause_first_form_worker(self):
        c = self.controller()
        self.enable(c)
        d = self.controller()
        d.load(c.config["state_dir"])
        self.wait(lambda: not d.view()["command_busy"])
        d.resume()
        self.wait(lambda: not d.view()["alive"])
        self.assertIsNotNone(d.view()["error"])
        self.assertTrue(c.view()["worker_started"])
        self.assertTrue(self.status(c)["enabled"])
        # Its close must not pause the other controller's owned worker either.
        d.close()
        self.wait(lambda: not d.view()["alive"])
        self.assertTrue(self.status(c)["enabled"])

    def test_partial_write_ready_gate_and_identical_rename(self):
        c = self.controller()
        c.update(
            {
                "folder": str(self.input),
                "condition": "ready_content_stable",
                "selection": self.selection,
                "settle_seconds": 0.3,
            }
        )
        c.preview()
        self.wait(lambda: not c.view()["command_busy"])
        c.enable()
        self.wait(lambda: c.view()["worker_started"])
        (self.input / "a.txt").write_text("first")
        time.sleep(0.35)
        self.assertEqual(self.fake.sent, [])
        (self.input / "READY").write_text("ready")
        time.sleep(0.1)
        (self.input / "a.txt").write_text("second")
        time.sleep(0.1)
        self.assertEqual(self.fake.sent, [])
        self.wait(lambda: len(self.fake.sent) == 1)
        self.fake.turns["turn-" + self.fake.sent[0]] = ("ended", "unknown")
        self.fake.idle = True
        self.wait(
            lambda: any(b["notification_released"] for b in self.status(c)["batches"])
        )
        (self.input / "a.txt").rename(self.input / "renamed.txt")
        time.sleep(0.7)
        self.assertEqual(len(self.fake.sent), 1)

    def test_view_invalidates_cached_green_when_worker_exits_or_health_stales(self):
        c = self.controller()
        self.enable(c)
        self.wait(lambda: self.status(c).get("monitoring") == "listening")
        with c.lock:
            c.status["watcher"]["progress_at_utc"] = "2000-01-01T00:00:00+00:00"
        self.assertNotEqual(c.view()["status"]["monitoring"], "listening")
        c.pause()
        self.wait(lambda: not c.view()["alive"])
        self.assertNotEqual(c.view()["status"]["monitoring"], "listening")

    def test_preview_does_not_parse_history_after_verified_first_line(self):
        with self.rollout.open("a", encoding="utf8") as f:
            f.write("invalid history after the metadata line")
        c = self.controller()
        self.preview(c)
        self.assertIsNotNone(c.view()["preview"])

    def test_stop_is_not_cleared_by_resume(self):
        c = self.controller()
        self.enable(c)
        c.pause()
        self.wait(lambda: not c.view()["alive"])
        stop = Path(c.config["state_dir"]) / "STOP"
        stop.write_text("retained stop")
        c.resume()
        self.wait(lambda: not c.view()["alive"])
        self.assertEqual(stop.read_text(), "retained stop")
        self.assertFalse(self.status(c)["enabled"])

    def test_actual_gui_fake_completes_two_file_batches(self):
        from experimental.simple_form_fake import FakeTransport

        self.fake = FakeTransport()
        c = self.controller()
        self.enable(c)
        (self.input / "a.txt").write_text("GUI-A")
        self.wait(
            lambda: any(b["native_acceptance"] for b in self.status(c)["batches"])
        )
        (self.input / "b.txt").write_text("GUI-B")
        self.wait(lambda: self.status(c)["backlog"] == 2)
        self.assertEqual(len(self.fake.sent), 1)
        self.fake.finish()
        self.wait(lambda: len(self.fake.sent) == 2)
        self.fake.finish()
        self.wait(lambda: self.status(c)["backlog"] == 0)
        self.assertEqual(set(self.fake.targets), {self.id})

    def test_failed_initialization_can_reopen_and_retry_after_input_fixed(self):
        c = self.controller()
        self.preview(c)
        broken = self.input / "broken.zip"
        broken.write_bytes(b"not a ZIP")
        c.enable()
        self.wait(lambda: not c.view()["alive"])
        self.assertIn("BadZipFile", c.view()["error"])
        self.assertFalse(self.status(c)["initialized"])
        saved = c.config["state_dir"]
        c.close()
        self.wait(lambda: c.view()["closed"])
        broken.unlink()
        d = self.controller()
        d.load(saved)
        self.wait(lambda: not d.view()["command_busy"])
        self.assertIsNone(d.view()["error"])
        self.assertFalse(d.initialized)
        d.enable()
        self.wait(lambda: d.view()["worker_started"])
        self.assertEqual(d.config["state_dir"], saved)
        self.assertEqual(self.fake.sent, [])

    def test_completed_status_threads_are_not_retained(self):
        c = self.controller()
        self.enable(c)
        c.pause()
        self.wait(lambda: not c.view()["alive"])
        for _ in range(10):
            self.status(c)
        self.assertLessEqual(len(c.threads), 1)
