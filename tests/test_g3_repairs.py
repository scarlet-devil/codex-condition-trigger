"""Evidence-driven offline regressions from the bounded S1 review."""

import json
import os
import threading
from pathlib import Path
from unittest.mock import patch
import test_g3_trial as fixtures
from test_g3_trial import Inner, frame
from experimental.g3_trial import BudgetPipe
import trigger as tr


# A standalone fixture avoids double-counting the existing 16 cases.
import unittest


class RepairTests(unittest.TestCase):
    setUp = fixtures.BudgetTests.setUp
    make = fixtures.BudgetTests.make

    def test_tx_and_supervisor_publication_serializes_without_stale_counts(self):
        b = self.make()
        inner = Inner()
        waiting = threading.Event()
        release = threading.Event()
        attempted = threading.Event()
        observer_replaced = threading.Event()
        failures = []
        real_lock = b.lock
        real_replace = os.replace
        wire_calls = 0

        class TrackedLock:
            def __enter__(self):
                if threading.current_thread().name == "observer":
                    attempted.set()
                real_lock.acquire()
                return self

            def __exit__(self, *args):
                real_lock.release()

        b.lock = TrackedLock()

        def controlled_replace(src, dst):
            nonlocal wire_calls
            if Path(dst) == b.receipt:
                if threading.current_thread().name == "wire":
                    wire_calls += 1
                    if wire_calls == 2:
                        waiting.set()
                        if not release.wait(3):
                            raise TimeoutError("test coordination failed")
                elif threading.current_thread().name == "observer":
                    result = real_replace(src, dst)
                    observer_replaced.set()
                    return result
            return real_replace(src, dst)

        def capture(fn):
            try:
                fn()
            except BaseException as e:
                failures.append(e)

        wire = threading.Thread(
            name="wire",
            target=lambda: capture(
                lambda: BudgetPipe(inner, b).write(frame("initialize"), 20)
            ),
        )
        observer = threading.Thread(
            name="observer", target=lambda: capture(lambda: b.event("supervisor"))
        )
        with patch.object(os, "replace", side_effect=controlled_replace):
            wire.start()
            self.assertTrue(waiting.wait(3))
            observer.start()
            self.assertTrue(attempted.wait(3))
            observer_replaced.wait(0.2)
            release.set()
            wire.join(3)
            observer.join(3)
        self.assertFalse(wire.is_alive() or observer.is_alive())
        self.assertEqual(failures, [])
        persisted = json.loads(b.receipt.read_bytes())
        self.assertEqual(
            persisted["counts"]["tx_known_bytes"], len(frame("initialize"))
        )
        self.assertEqual(
            persisted["counts"]["tx_upper_bytes"], len(frame("initialize"))
        )
        self.assertIsNone(persisted["reason"])
        self.assertTrue(any(e["event"] == "supervisor" for e in persisted["events"]))

    def primary_failure(self, operation, primary):
        b = self.make()
        real = tr.atomic_write

        def persist(path, data):
            if b.reason:
                raise OSError("secondary stop persistence")
            return real(path, data)

        with patch.object(tr, "atomic_write", side_effect=persist):
            try:
                operation(b, primary)
            except BaseException as e:
                caught = e
            else:
                self.fail("primary failure disappeared")
        self.assertIs(caught, primary)
        self.assertTrue(getattr(caught, "__notes__", []))
        self.assertIsNotNone(b.reason)

    def test_read_error_survives_secondary_stop_failure(self):
        def call(b, error):
            def fail():
                raise error

            b.transfer("rx", 4, fail)

        self.primary_failure(call, TimeoutError("primary read"))

    def test_write_error_survives_secondary_stop_failure(self):
        def call(b, error):
            i = Inner()

            def fail(*args):
                raise error

            i.io = fail
            BudgetPipe(i, b).write(frame("initialize"), 20)

        self.primary_failure(call, OSError("primary write"))

    def test_pipe_cleanup_preserves_active_error_and_lone_error_raises(self):
        b = self.make()
        i = Inner()
        failure = OSError("close failed")

        def fail():
            raise failure

        i.close = fail
        p = BudgetPipe(i, b)
        primary = TimeoutError("original read")
        caught = None
        try:
            try:
                raise primary
            finally:
                p.close()
        except BaseException as e:
            caught = e
        self.assertIs(caught, primary)
        self.assertTrue(primary.__notes__)
        with self.assertRaises(OSError):
            p.close()
