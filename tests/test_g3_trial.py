import json
import pathlib
import struct
import tempfile
import unittest
from experimental.g3_trial import BudgetStopped, G3Budget, BudgetPipe

TARGET = "00000000-0000-0000-0000-000000000001"


def frame(method, client="A"):
    p = {"conversationId": TARGET}
    if method == "thread-follower-start-turn":
        from desktop_ipc import start_params

        p = start_params(TARGET, client, "data-only synthetic task")
    return pack({"type": "request", "method": method, "params": p, "requestId": client})


def pack(o):
    b = json.dumps(o).encode()
    return struct.pack("<I", len(b)) + b


class Inner:
    def __init__(self):
        self.writes = []
        self.closed = False

    def io(self, value, deadline, write=False, before_write=None):
        if before_write and before_write():
            raise TimeoutError("stopped")
        self.writes.append(value)
        return len(value)

    def close(self):
        self.closed = True


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.now = [1000.0, 10.0]
        self.contract = {
            "thread_id": TARGET,
            "expires_at_epoch": 1480.0,
            "duration_seconds": 480.0,
            "limits": {
                "start_write_attempts": 2,
                "history": 16,
                "initialize": 12,
                "owner_discovery": 20,
                "total_requests": 50,
                "non_cleanup_tx_frames": 128,
                "rx_frames": 512,
                "max_frame_bytes": 33554432,
                "total_rx_bytes": 134217728,
                "rollout_reads": 64,
                "total_rollout_bytes": 134217728,
            },
        }

    def make(self):
        return G3Budget(
            self.contract,
            self.root / "receipt.json",
            wall=lambda: self.now[0],
            mono=lambda: self.now[1],
        )

    def test_third_start_never_reaches_transport(self):
        b = self.make()
        i = Inner()
        p = BudgetPipe(i, b)
        p.write(frame("thread-follower-start-turn", "A"), 20)
        p.write(frame("thread-follower-start-turn", "B"), 20)
        with self.assertRaises(BudgetStopped):
            p.write(frame("thread-follower-start-turn", "C"), 20)
        self.assertEqual(len(i.writes), 2)

    def test_same_start_not_retried_on_new_connection(self):
        b = self.make()
        a = Inner()
        z = Inner()
        BudgetPipe(a, b).write(frame("thread-follower-start-turn"), 20)
        with self.assertRaises(BudgetStopped):
            BudgetPipe(z, b).write(frame("thread-follower-start-turn"), 20)
        self.assertEqual(z.writes, [])

    def test_absolute_deadline_stops_even_without_clock_progress(self):
        b = self.make()
        i = Inner()
        self.now[0] = 1480
        with self.assertRaises(BudgetStopped):
            BudgetPipe(i, b).write(frame("initialize"), 20)
        self.assertEqual(i.writes, [])

    def test_wall_clock_rollback_does_not_extend_monotonic_deadline(self):
        b = self.make()
        i = Inner()
        self.now[:] = [1, 491]
        with self.assertRaises(BudgetStopped):
            BudgetPipe(i, b).write(frame("initialize"), 999)
        self.assertEqual(i.writes, [])

    def test_restarting_existing_receipt_cannot_rearm(self):
        self.make()
        with self.assertRaises((BudgetStopped, FileExistsError)):
            self.make()

    def test_history_limit_shared_across_connections(self):
        self.contract["limits"]["history"] = 1
        b = self.make()
        i = Inner()
        p = BudgetPipe(i, b)
        p.write(frame("thread-follower-load-complete-history"), 20)
        with self.assertRaises(BudgetStopped):
            BudgetPipe(i, b).write(frame("thread-follower-load-complete-history"), 20)
        self.assertEqual(len(i.writes), 1)

    def test_evidence_write_failure_prevents_wire_action(self):
        from unittest.mock import patch
        import trigger as tr

        b = self.make()
        i = Inner()
        with patch.object(tr, "atomic_write", side_effect=OSError("disk full")):
            with self.assertRaises(BudgetStopped):
                BudgetPipe(i, b).write(frame("initialize"), 20)
        self.assertEqual(i.writes, [])
        with self.assertRaises(BudgetStopped):
            b.guard()

    def test_late_installation_validation_cannot_initialize(self):
        from experimental.g3_trial import make_client

        b = self.make()
        i = Inner()

        def slow(_):
            self.now[1] = 491
            return {}

        with self.assertRaises(Exception):
            make_client(b, 10, pipe_factory=lambda: i, verifier=slow)
        self.assertEqual(i.writes, [])
        self.assertTrue(i.closed)

    def test_partial_start_write_consumes_allowance_and_latches(self):
        b = self.make()
        i = Inner()
        calls = []

        def write(value, deadline, writing=False, before_write=None):
            calls.append(value)
            if len(calls) == 1:
                return 2
            raise OSError("broken pipe after partial write")

        i.io = write
        with self.assertRaises(OSError):
            BudgetPipe(i, b).write(frame("thread-follower-start-turn"), 20)
        self.assertEqual(b.counts["start_write_attempts"], 1)
        self.assertEqual(b.counts["tx_known_bytes"], 2)
        self.assertGreater(b.counts["tx_upper_bytes"], 2)
        with self.assertRaises(BudgetStopped):
            BudgetPipe(Inner(), b).write(frame("thread-follower-start-turn", "B"), 20)

    def test_partial_rx_accounts_header_and_unknown_failure_bound(self):
        b = self.make()
        i = Inner()
        parts = [
            b"\x08\0",
            b"\0\0",
            b"ab",
            TimeoutError("partial kernel result unknown"),
        ]

        def read(n, deadline):
            p = parts.pop(0)
            if isinstance(p, Exception):
                raise p
            return p

        i.io = read
        p = BudgetPipe(i, b)
        self.assertEqual(p.read(4, 20), struct.pack("<I", 8))
        with self.assertRaises(TimeoutError):
            p.read(8, 20)
        self.assertEqual(b.counts["rx_known_bytes"], 6)
        self.assertEqual(b.counts["rx_upper_bytes"], 12)
        self.assertIsNotNone(b.reason)

    def test_oversized_frame_body_never_read(self):
        self.contract["limits"]["max_frame_bytes"] = 16
        b = self.make()
        i = Inner()
        calls = []

        def read(n, deadline):
            calls.append(n)
            return struct.pack("<I", 17)

        i.io = read
        with self.assertRaises(BudgetStopped):
            BudgetPipe(i, b).read(4, 20)
        self.assertEqual(calls, [4])

    def test_whole_payload_must_fit_rx_budget_before_read(self):
        self.contract["limits"]["total_rx_bytes"] = 12
        b = self.make()
        i = Inner()
        i.io = lambda n, d: struct.pack("<I", 9)
        with self.assertRaises(BudgetStopped):
            BudgetPipe(i, b).read(4, 20)
        self.assertEqual(b.counts["rx_known_bytes"], 4)

    def test_unrelated_frames_cannot_exceed_frame_count(self):
        self.contract["limits"]["rx_frames"] = 1
        b = self.make()
        i = Inner()
        parts = [struct.pack("<I", 2), b"{}"]
        i.io = lambda n, d: parts.pop(0)
        p = BudgetPipe(i, b)
        p.read(4, 20)
        p.read(2, 20)
        with self.assertRaises(BudgetStopped):
            p.read(4, 20)
        self.assertEqual(b.counts["rx_known_bytes"], 6)

    def test_only_matching_existing_subscription_can_cleanup_after_stop(self):
        b = self.make()
        i = Inner()
        p = BudgetPipe(i, b)
        msg = {
            "type": "broadcast",
            "method": "thread-stream-following-changed",
            "params": {"conversationId": TARGET, "following": True},
        }
        p.write(pack(msg), 20)
        b.stop("synthetic stop")
        msg["params"]["following"] = False
        p.write(pack(msg), 20)
        with self.assertRaises(BudgetStopped):
            p.write(pack(msg), 20)
        self.assertEqual(len(i.writes), 2)
        self.assertEqual(b.counts["cleanup_frames"], 1)

    def test_wrong_target_rejected_before_wire(self):
        b = self.make()
        i = Inner()
        o = json.loads(frame("thread-owner-discovery")[4:])
        o["params"]["conversationId"] = "foreign"
        with self.assertRaises(BudgetStopped):
            BudgetPipe(i, b).write(pack(o), 20)
        self.assertEqual(i.writes, [])

    def test_rollout_reader_preserves_original_parser_and_counts_bytes(self):
        import desktop_ipc as ipc

        b = self.make()
        p = self.root / "rollout"
        raw = (
            json.dumps(
                {
                    "type": "session_meta",
                    "payload": {"id": TARGET, "cwd": str(self.root)},
                }
            )
            + "\n"
        ).encode()
        p.write_bytes(raw)
        expected = ipc.rollout_state(p, TARGET, str(self.root), lifecycle=False)
        actual = ipc.rollout_state(
            p, TARGET, str(self.root), lifecycle=False, reader=b.read_rollout
        )
        self.assertEqual(actual, expected)
        self.assertEqual(b.counts["rollout_known_bytes"], len(raw))
        self.contract["limits"]["rollout_reads"] = 1
        with self.assertRaises(BudgetStopped):
            b.read_rollout(p)
