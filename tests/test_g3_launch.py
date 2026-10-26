"""Offline launcher binding and real framing against a deterministic synthetic peer."""

import copy
import json
import time
from test_notify import NotifyFixture
from test_g3_trial import TARGET, pack
import desktop_ipc as ipc
import rule_service as rs
import trigger as tr
from experimental.g3_trial import G3Budget, BoundedAdapter, make_client
from experimental.g3_launch import constrained_preview, TrialController, rows, fixture


class Peer:
    def __init__(self, c):
        self.c = c
        self.pending = bytearray()
        self.closed = False
        self.requests = []

    def io(self, value, deadline, write=False, before_write=None):
        if not write:
            data = bytes(self.pending[:value])
            del self.pending[:value]
            return data
        if before_write:
            before_write()
        item = json.loads(value[4:])
        method = item["method"]
        self.requests.append(method)
        if item["type"] == "request":
            result = (
                {"clientId": "client"} if method == "initialize" else {"revision": 1}
            )
            self.pending.extend(
                pack(
                    dict(
                        type="response",
                        method=method,
                        resultType="success",
                        requestId=item["requestId"],
                        result=result,
                        sourceClientId="owner",
                        handledByClientId="owner",
                    )
                )
            )
        elif item["params"]["following"]:
            self.pending.extend(
                pack(
                    dict(
                        type="broadcast",
                        method="thread-stream-state-changed",
                        version=ipc.METHODS["thread-stream-state-changed"],
                        sourceClientId="owner",
                        targetClientIds=["client"],
                        params=dict(
                            conversationId=TARGET,
                            hostId="local",
                            change=dict(
                                type="snapshot",
                                revision=1,
                                conversationState=dict(
                                    id=TARGET,
                                    cwd=self.c["expected_cwd"],
                                    threadRuntimeStatus={"type": "idle"},
                                    resumeState="resumed",
                                ),
                            ),
                        ),
                    )
                )
            )
        return len(value)

    def close(self):
        self.closed = True


class LauncherTests(NotifyFixture):
    def setUp(self):
        super().setUp()
        self.config["thread_id"] = TARGET
        self.rollout = self.root / "rollout.jsonl"
        self.rollout.write_text(
            json.dumps(
                dict(type="session_meta", payload=dict(id=TARGET, cwd=str(self.root)))
            )
            + "\n"
        )
        self.selection = dict(
            id=TARGET,
            selection_key=TARGET,
            cwd=str(self.root),
            rollout_path=str(self.rollout),
        )
        self.contract = dict(
            thread_id=TARGET,
            input_dir=str(self.input),
            duration_seconds=480,
            expires_at_epoch=round(time.time() + 479, 6),
            instruction="synthetic only",
            limits=dict(
                start_write_attempts=2,
                initialize=12,
                owner_discovery=20,
                history=16,
                total_requests=50,
                non_cleanup_tx_frames=128,
                rx_frames=512,
                max_frame_bytes=33554432,
                total_rx_bytes=134217728,
                rollout_reads=64,
                total_rollout_bytes=134217728,
            ),
            rule_overrides=dict(
                dispatch_mode="notify",
                initial_files="ignore",
                settle_seconds=1,
                rescan_seconds=1,
                rpc_timeout_seconds=10,
                max_connect_attempts=1,
                max_pending_batches=2,
                max_state_bytes=33554432,
                max_file_bytes=65536,
                owner_loading_enabled=False,
                resume_unloaded=False,
                native_result_collection=False,
            ),
        )
        self.budget = G3Budget(self.contract, self.root / "budget.json")
        self.form = dict(
            folder=str(self.input),
            condition="new_content_stable",
            selection=self.selection,
            settle_seconds=1,
        )

    def preview(self):
        return rs.preview(
            **self.form,
            state_dir=str(self.root / "state"),
            identity_reader=self.budget.read_identity,
        )

    def test_preview_uses_counted_identity_and_fixed_limits(self):
        p = constrained_preview(self.preview(), self.contract, self.selection)
        self.assertEqual(self.budget.counts["rollout_reads"], 1)
        self.assertEqual(
            self.budget.counts["rollout_known_bytes"], self.rollout.stat().st_size
        )
        self.assertEqual(p["config"]["max_pending_batches"], 2)
        self.assertEqual(
            tr.trial_deadline(p["config"]), self.contract["expires_at_epoch"]
        )

    def test_wrong_binding_or_initial_option_cannot_preview(self):
        p = self.preview()
        for key, value in [
            ("thread_id", "11111111-1111-4111-8111-111111111111"),
            ("input_dir", str(self.root / "foreign")),
            ("settle_seconds", 120),
            ("initial_files", "process"),
            ("expected_cwd", str(self.root / "foreign")),
        ]:
            q = copy.deepcopy(p)
            q["config"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                constrained_preview(q, self.contract, self.selection)

    def test_enable_probe_and_later_connection_share_real_frame_budget(self):
        self.contract["limits"]["initialize"] = 1
        c = constrained_preview(self.preview(), self.contract, self.selection)["config"]
        peers = []

        def factory(c, paused):
            a = BoundedAdapter(c, paused, self.budget)

            def client(timeout):
                p = Peer(c)
                peers.append(p)
                return make_client(
                    self.budget, timeout, pipe_factory=lambda: p, verifier=lambda p: {}
                )

            a.client_factory = client
            return a

        (self.input / "seed.txt").write_text("seed")
        c = rs.enable(c, adapter_factory=factory)
        self.assertEqual(self.budget.counts["initialize"], 1)
        self.assertEqual(self.budget.counts["history"], 1)
        self.assertEqual(rows(c), [])
        self.assertEqual(rs.status(c)["backlog"], {"batches": 0})
        later = factory(c, lambda: False)
        with self.assertRaises(Exception):
            later.inspect(dict(state="ready"))
        later.close()
        self.assertEqual(peers[1].requests, [])
        self.assertEqual(self.budget.reason, "limit_initialize")
        rs.pause(c)

    def test_ordinary_notify_mode_preserves_no_receipt_observation(self):
        a = BoundedAdapter(self.config, lambda: False, self.budget)
        self.assertIsNone(a.observe(dict(state="ready")))
        self.assertIsNone(self.budget.reason)

    def test_new_controller_keeps_same_budget_and_rejects_changed_saved_target(self):
        c = constrained_preview(self.preview(), self.contract, self.selection)["config"]
        first = TrialController(self.root / "rules", self.budget, self.selection)
        first.close()
        second = TrialController(self.root / "rules", self.budget, self.selection)
        second.config = dict(c, expected_cwd=str(self.root / "foreign"))
        with self.assertRaises(ValueError):
            second._start(False)
        self.assertIs(second.budget, first.budget)
        second.close()

    def test_fixture_expectations_are_deterministic(self):
        for label, total in [("A", 311), ("B", 2911)]:
            records = fixture(label)["records"]
            self.assertEqual(len(records), 27)
            self.assertEqual(len({r["id"] for r in records}), 25)
            self.assertEqual(sum(r.get("value", 0) for r in records), total)

    def test_second_window_rejects_new_rule_or_changed_saved_config(self):
        from unittest.mock import patch

        c = constrained_preview(self.preview(), self.contract, self.selection)["config"]
        second = TrialController(
            self.root / "rules", self.budget, self.selection, expected_saved=c
        )
        second.config = dict(c)
        with self.assertRaises(ValueError):
            second._start(True)
        second.config = dict(c, rule_id="different-rule")
        with self.assertRaises(ValueError):
            second._start(False)
        second.config = dict(c)
        with patch("simple_controller.Controller._start") as start:
            second._start(False)
            start.assert_called_once_with(False)
        second.close()

    def test_gui_failure_closes_owned_resources_and_preserves_primary_over_report_failure(
        self,
    ):
        from unittest.mock import patch
        import threading
        from experimental import g3_launch as launch

        private = self.root / "private"
        private.mkdir()
        selection_path = private / "target.json"
        selection_path.write_text(json.dumps(self.selection))
        contract = dict(
            self.contract,
            activation_allowed=True,
            trial_root=str(self.root),
            selection_path=str(selection_path),
            catalog_path=str(self.root / "synthetic-catalog"),
        )
        contract_path = private / "contract.json"
        contract_path.write_text(json.dumps(contract))
        primary = TimeoutError("synthetic mainloop failure")

        class ControllerFake:
            config = None

            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

            def view(self):
                return dict(
                    closed=self.closed,
                    closing=self.closed,
                    error=None,
                    config=None,
                    worker_started=False,
                )

        class WindowFake:
            def __init__(self):
                self.destroyed = False

            def title(self, *a):
                pass

            def mainloop(self):
                raise primary

            def winfo_exists(self):
                return not self.destroyed

            def destroy(self):
                self.destroyed = True

        controller = ControllerFake()
        window = WindowFake()

        def save_failure(*a):
            if threading.current_thread() is threading.main_thread():
                raise OSError("secondary report failure")

        with (
            patch.object(launch, "TrialController", return_value=controller),
            patch.object(launch.tk, "Tk", return_value=window),
            patch.object(launch, "App"),
            patch.object(launch, "save", side_effect=save_failure),
            patch("sys.argv", ["g3_launch", "--contract", str(contract_path)]),
        ):
            try:
                launch.main()
            except BaseException as error:
                caught = error
            else:
                self.fail("main error disappeared")
        self.assertIs(caught, primary)
        self.assertTrue(controller.closed)
        self.assertTrue(window.destroyed)
        self.assertTrue(
            any("final report failure" in note for note in primary.__notes__)
        )
        self.assertFalse(
            any(t.name == "g3-bounded-supervisor" for t in threading.enumerate())
        )
