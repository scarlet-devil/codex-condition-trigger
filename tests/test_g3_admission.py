"""Offline first-byte admission and isolated batch workflow regressions."""

import json
import time
import unittest
from unittest.mock import patch

import trigger as tr
from experimental import g3_launch as launch
from experimental.g3_trial import BudgetPipe, G3Budget, StartWindowClosed, BudgetStopped
import test_g3_trial as budget_tests
from test_g3_trial import Inner, frame
import test_g3_launch as launch_tests


class AdmissionTests(unittest.TestCase):
    setUp = budget_tests.BudgetTests.setUp
    make = budget_tests.BudgetTests.make

    def test_observed_last_fraction_is_known_unsent(self):
        b = self.make()
        self.now[0] = 1479.612
        inner = Inner()
        with self.assertRaises(StartWindowClosed):
            BudgetPipe(inner, b).write(frame("thread-follower-start-turn"), 490)
        self.assertEqual(inner.writes, [])
        self.assertEqual(b.counts["start_write_attempts"], 0)
        self.assertEqual(b.reason, "insufficient_start_time")
        with self.assertRaises(BudgetStopped):
            b.guard()

    def test_monotonic_reserve_survives_wall_rollback(self):
        b = self.make()
        self.now[:] = [1, 311]
        with self.assertRaises(StartWindowClosed):
            b.admit_start()

    def test_first_byte_callback_rechecks_after_persistence(self):
        b = self.make()
        outer = self

        class SlowSetup(Inner):
            def io(self, *a, **kw):
                outer.now[0] = 1301
                return super().io(*a, **kw)

        inner = SlowSetup()
        with self.assertRaises(StartWindowClosed):
            BudgetPipe(inner, b).write(frame("thread-follower-start-turn"), 490)
        self.assertEqual(inner.writes, [])
        self.assertEqual(b.counts["tx_known_bytes"], 0)
        self.assertEqual(b.counts["tx_upper_bytes"], 0)
        self.assertEqual(b.counts["start_write_attempts"], 1)  # reservation retained

    def test_partial_write_crossing_reserve_finishes_frame(self):
        b = self.make()
        outer = self

        class Partial(Inner):
            def io(self, data, deadline, write=False, before_write=None):
                before_write()
                self.writes.append(data)
                if len(self.writes) == 1:
                    outer.now[0] = 1301
                    return 1
                return len(data)

        inner = Partial()
        data = frame("thread-follower-start-turn")
        BudgetPipe(inner, b).write(data, 490)
        self.assertEqual(len(inner.writes), 2)
        self.assertEqual(b.counts["tx_known_bytes"], len(data))
        self.assertIsNone(b.reason)

    def test_partial_write_expiry_remains_ambiguous(self):
        b = self.make()
        outer = self

        class Partial(Inner):
            def io(self, data, deadline, write=False, before_write=None):
                before_write()
                self.writes.append(data)
                outer.now[0] = 1480
                return 1

        inner = Partial()
        with self.assertRaises(BudgetStopped):
            BudgetPipe(inner, b).write(frame("thread-follower-start-turn"), 490)
        self.assertEqual(b.counts["tx_known_bytes"], 1)
        self.assertEqual(len(inner.writes), 1)

    def test_readonly_query_allowed_below_start_reserve(self):
        b = self.make()
        self.now[0] = 1400
        inner = Inner()
        BudgetPipe(inner, b).write(frame("thread-owner-discovery"), 490)
        self.assertEqual(len(inner.writes), 1)

    def test_invalid_reserve_does_not_create_receipt(self):
        for reserve in [0, -1, float("nan"), float("inf"), True, "180", 481]:
            with self.subTest(reserve=reserve):
                self.contract["min_start_remaining_seconds"] = reserve
                with self.assertRaises(BudgetStopped):
                    self.make()
                self.assertFalse((self.root / "receipt.json").exists())


class BatchWorkflowTests(launch_tests.LauncherTests):
    def setup_contract(self):
        private = self.root / "private"
        private.mkdir()
        target = private / "target.json"
        target.write_text(json.dumps(self.selection))
        self.input.rename(self.root / "inbox")
        self.input = self.root / "inbox"
        (self.input / "initial.json").write_text("{}")
        self.contract.update(
            workflow="batches_only",
            min_start_remaining_seconds=180,
            trial_root=str(self.root),
            input_dir=str(self.input),
            selection_path=str(target),
            expected_archive_sha256="a" * 64,
            activation_allowed=False,
        )
        return private / "contract.json"

    def test_check_only_does_not_arm_or_query(self):
        path = self.setup_contract()
        self.contract["expires_at_epoch"] = None
        path.write_text(json.dumps(self.contract))
        with (
            patch("sys.argv", ["g3_launch", "--contract", str(path), "--check-only"]),
            patch.object(launch, "G3Budget") as budget,
            patch.object(launch, "TrialController") as controller,
        ):
            self.assertEqual(launch.main(), 0)
            budget.assert_not_called()
            controller.assert_not_called()
        self.assertFalse((path.parent / "budget.json").exists())

    def test_old_materials_or_rules_cannot_be_reused(self):
        self.setup_contract()
        launch.validate_launch(self.contract)
        for old in [self.input / "B.json", self.root / "rules" / "old-rule"]:
            old.parent.mkdir(exist_ok=True)
            old.write_text("old")
            with self.assertRaises(ValueError):
                launch.validate_launch(self.contract)
            old.unlink()
        for key, value in [
            ("workflow", "typo"),
            ("min_start_remaining_seconds", 1),
            ("duration_seconds", 600),
            ("expected_archive_sha256", None),
        ]:
            c = dict(self.contract, **{key: value})
            with self.assertRaises(ValueError):
                launch.validate_launch(c)

    def test_real_controller_bootstrap_ignores_seed_and_preserves_deadline(self):
        self.setup_contract()
        budget = G3Budget(self.contract, self.root / "private/new-budget.json")
        controller = launch.TrialController(self.root / "rules", budget, self.selection)
        controller.adapter_factory = self.fake.factory  # only transport replaced
        try:
            launch.start_batches(controller, budget, self.selection)
            until = time.monotonic() + 5
            while (
                not controller.view()["worker_started"]
                and not controller.view()["error"]
                and time.monotonic() < until
            ):
                time.sleep(0.02)
            self.assertIsNone(controller.view()["error"])
            self.assertTrue(controller.view()["worker_started"])
            status = launch.read_status(controller.config)
            self.assertEqual(status["initial_files"], 1)
            self.assertEqual(status["backlog"], 0)
            self.assertEqual(status["deadline"], self.contract["expires_at_epoch"])
            self.assertEqual(self.fake.sent, [])
        finally:
            launch.close_window(controller, None, None, None)
        self.assertTrue(controller.view()["closed"])

    def test_dispatch_intent_rejected_before_write_is_not_uncertain(self):
        from test_notify import NotifyFixture

        NotifyFixture.open(self)
        batch = NotifyFixture.batch(self, "new data")
        b = self.budget
        b.start_reserve = 480

        def send(*args):
            b.admit_start()

        with patch.object(self.fake, "send", side_effect=send):
            tr.dispatch_one(self.store, adapter_factory=self.fake.factory)
        row = self.store.db.execute(
            "SELECT * FROM batches WHERE id=?", (batch,)
        ).fetchone()
        self.assertEqual(row["state"], "ready")
        self.assertEqual(self.fake.sent, [])
        self.assertEqual(b.reason, "insufficient_start_time")

    def test_headless_two_batches_use_real_controller_and_watcher(self):
        path = self.setup_contract()
        self.contract["activation_allowed"] = True
        path.write_text(json.dumps(self.contract))
        controllers = []
        budgets = []
        original_budget = launch.G3Budget
        original_controller = launch.TrialController
        original_observe = self.fake.observe

        def budget_factory(*a, **kw):
            b = original_budget(*a, **kw)
            budgets.append(b)
            return b

        def controller_factory(*a, **kw):
            c = original_controller(*a, **kw)
            c.adapter_factory = self.fake.factory
            c.simulation = True
            c.interval = 0.05
            controllers.append(c)
            return c

        def life(*a, **kw):
            return dict(turns={k: dict(state=v[0]) for k, v in self.fake.turns.items()})

        def observe(row):
            if row.get("turn_id") and any(
                e["event"] == "b_waiting_while_a_running" for e in budgets[0].events
            ):
                self.fake.turns[row["turn_id"]] = ("ended", "unknown")
                self.fake.idle = True
            return original_observe(row)

        import threading

        timer = threading.Timer(10, lambda: budgets and budgets[0].stop("test_timeout"))
        timer.start()
        try:
            with (
                patch.object(launch, "G3Budget", side_effect=budget_factory),
                patch.object(launch, "TrialController", side_effect=controller_factory),
                patch.object(launch, "rollout_state", side_effect=life),
                patch.object(self.fake, "observe", side_effect=observe),
                patch.object(launch.tk, "Tk") as tk,
                patch("sys.argv", ["g3_launch", "--contract", str(path)]),
            ):
                self.assertEqual(launch.main(), 0)
                tk.assert_not_called()
        finally:
            timer.cancel()
            timer.join()
        self.assertEqual(len(controllers), 1)
        self.assertTrue(controllers[0].view()["closed"])
        result = json.loads((path.parent / "supervisor.json").read_bytes())
        self.assertTrue(result["gui_evidence_reused"])
        self.assertTrue(result["b_waiting_while_a_running"])
        self.assertTrue(result["two_released"])
        self.assertEqual(len(self.fake.sent), 2)
        status = launch.read_status(controllers[0].config)
        self.assertFalse(status["enabled"])
        self.assertEqual(status["backlog"], 0)
        self.assertTrue(
            all(r["business_delivery"] == "unverified" for r in status["batches"])
        )

    def test_contract_overrides_cannot_change_trial_semantics(self):
        for key, value in [
            ("dispatch_mode", "strict"),
            ("initial_files", "process"),
            ("settle_seconds", 0),
            ("owner_loading_enabled", True),
            ("resume_unloaded", True),
            ("native_result_collection", True),
        ]:
            with self.subTest(key=key):
                contract = dict(
                    self.contract,
                    rule_overrides=dict(
                        self.contract["rule_overrides"], **{key: value}
                    ),
                )
                with self.assertRaises(ValueError):
                    launch.constrained_preview(self.preview(), contract, self.selection)

    def check_installation_pin(self, observed):
        from desktop_ipc import IPCFailure
        from experimental.g3_trial import make_client

        self.contract["expected_archive_sha256"] = "a" * 64
        peer = launch_tests.Peer(self.config)
        verifier = lambda _: observed
        if observed.get("archive_sha256") == "a" * 64:
            client = make_client(
                self.budget, 10, pipe_factory=lambda: peer, verifier=verifier
            )
            client.close()
            self.assertEqual(self.budget.counts["initialize"], 1)
        else:
            with self.assertRaises(IPCFailure):
                make_client(
                    self.budget, 10, pipe_factory=lambda: peer, verifier=verifier
                )
            self.assertEqual(peer.requests, [])
            self.assertEqual(self.budget.counts["initialize"], 0)
            self.assertEqual(self.budget.reason, "installation_pin_mismatch")
        self.assertTrue(peer.closed)

    def test_matching_installation_pin_initializes(self):
        self.check_installation_pin({"archive_sha256": "a" * 64})

    def test_changed_installation_pin_never_initializes(self):
        self.check_installation_pin({"archive_sha256": "b" * 64})

    def test_missing_installation_pin_never_initializes(self):
        self.check_installation_pin({})


def load_tests(loader, tests, pattern):
    # Reuse fixture setup without duplicating the inherited regression suite.
    return unittest.TestSuite(
        cls(name)
        for cls in (AdmissionTests, BatchWorkflowTests)
        for name in cls.__dict__
        if name.startswith("test_")
    )
