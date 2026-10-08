"""Bounded final-write regression probes; no real IPC, UI, or watcher.

Run with the existing project interpreter, -X utf8 -B, and TEMP/TMP pointing
to the trial test-temp directory. Pass --repo to select the reviewed checkout.
Only synthetic temporary fixture state is created. Production code is imported,
but WindowsPipe.__init__ is never called and all kernel functions are fake.
The original reviewed implementation fails the first two regression contracts.
The additional probes verify callback propagation, partial writes and callback
latency on the repaired path. All five must pass on the repaired implementation.
"""
import argparse
import ctypes
from ctypes import wintypes
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

parser = argparse.ArgumentParser()
parser.add_argument('--repo', required=True)
args = parser.parse_args()
repo = Path(args.repo).resolve()
sys.path[:0] = [str(repo), str(repo / 'tests')]

import desktop_ipc as ipc
from test_desktop_ipc import DesktopDispatchTests

OBSERVATIONS = {}


def fake_pipe(clock, writes, prepare=None, after_write=None, write_limit=None):
    class Overlapped(ctypes.Structure):
        _fields_ = [('hEvent', wintypes.HANDLE)]

    def create_event(*unused):
        if prepare:
            prepare()
        return 456

    def write_file(handle, buffer, length, count, overlapped):
        writes.append(clock['mono'])
        count._obj.value = length if write_limit is None else min(length, write_limit)
        if after_write:
            after_write()
        return True

    pipe = ipc.WindowsPipe.__new__(ipc.WindowsPipe)
    pipe.ct, pipe.wt, pipe.Overlapped, pipe.handle = ctypes, wintypes, Overlapped, 123
    pipe.k = SimpleNamespace(CreateEventW=create_event, WriteFile=write_file,
                             CloseHandle=lambda *unused: None)
    return pipe


class FinalWriteProbe(unittest.TestCase):
    def test_rollback_must_not_extend_store_deadline_at_final_write(self):
        cutoff = 1893456000.0
        clock = {'wall': cutoff - 10, 'mono': 100.0}
        case = DesktopDispatchTests('test_busy_keeps_batch_local')
        case.setUp()
        result = {}
        try:
            with mock.patch('time.time', side_effect=lambda: clock['wall']), \
                    mock.patch('time.monotonic', side_effect=lambda: clock['mono']):
                case.config['trial_expires_at_utc'] = '2030-01-01T00:00:00Z'
                case.reopen()
                case.ready()
                original = case.client.request
                writes = []
                pipe = fake_pipe(clock, writes)

                def delayed_start(client, method, params, **kwargs):
                    result['store_deadline'] = case.store.monotonic_deadline
                    result['request_deadline'] = kwargs['deadline']
                    clock['mono'] = 110.25
                    options = {}
                    if 'before_write' in inspect.signature(pipe.io).parameters:
                        options['before_write'] = kwargs.get('before_write')
                    pipe.io(b'synthetic only', kwargs['deadline'], write=True, **options)
                    return original(client, method, params, **kwargs)

                case.client.request = delayed_start
                clock.update(wall=cutoff - 100, mono=109.5)
                result['dispatch_result'] = case.dispatch()
                result['fake_write_times'] = writes
                result['store_reports_expired_after_send'] = case.store.paused()
        finally:
            case.tearDown()
        OBSERVATIONS['rollback'] = result
        self.assertLessEqual(result['request_deadline'], result['store_deadline'])
        self.assertEqual(result['fake_write_times'], [])
        self.assertNotEqual(result['dispatch_result'], 'accepted')

    def test_expiry_during_preparation_must_prevent_actual_write(self):
        clock, writes = {'mono': 9.9}, []
        pipe = fake_pipe(clock, writes, lambda: clock.update(mono=10.1))
        outcome = 'returned'
        with mock.patch('time.monotonic', side_effect=lambda: clock['mono']):
            try:
                pipe.io(b'synthetic only', 10.0, write=True)
            except TimeoutError:
                outcome = 'timeout'
        OBSERVATIONS['preparation'] = dict(deadline=10.0,
                                           fake_write_times=writes, outcome=outcome)
        self.assertEqual(writes, [])
        self.assertEqual(outcome, 'timeout')

    def request_with_fake_transport(self, pipe, callback):
        client = ipc.IPCClient.__new__(ipc.IPCClient)
        client.pipe, client.client_id, client.timeout = pipe, 'synthetic-client', 1.0
        with self.assertRaises(TimeoutError):
            client.request('thread-follower-start-turn', {}, deadline=10.0,
                           before_write=callback)

    def test_wall_clock_callback_reaches_final_native_write(self):
        clock, writes = {'mono': 5.0, 'wall': 9.0, 'callbacks': 0}, []
        pipe = fake_pipe(clock, writes, lambda: clock.update(wall=11.0))

        def expired():
            clock['callbacks'] += 1
            return clock['wall'] >= 10.0

        with mock.patch('time.monotonic', side_effect=lambda: clock['mono']):
            self.request_with_fake_transport(pipe, expired)
        OBSERVATIONS['wall_callback'] = dict(fake_write_times=writes, **clock)
        self.assertEqual(clock['callbacks'], 1)
        self.assertEqual(writes, [])

    def test_pause_between_partial_frame_writes_stops_remaining_frame(self):
        clock, writes = {'mono': 5.0, 'paused': False, 'callbacks': 0}, []
        pipe = fake_pipe(clock, writes, after_write=lambda: clock.update(paused=True),
                         write_limit=1)

        def paused():
            clock['callbacks'] += 1
            return clock['paused']

        with mock.patch('time.monotonic', side_effect=lambda: clock['mono']):
            self.request_with_fake_transport(pipe, paused)
        OBSERVATIONS['partial_frame_pause'] = dict(fake_write_times=writes, **clock)
        self.assertEqual(clock['callbacks'], 2)
        self.assertEqual(writes, [5.0])

    def test_callback_latency_cannot_cross_actual_write_deadline(self):
        clock, writes = {'mono': 5.0}, []
        pipe = fake_pipe(clock, writes)

        def delayed_clearance():
            clock['mono'] = 10.1
            return False

        with mock.patch('time.monotonic', side_effect=lambda: clock['mono']):
            self.request_with_fake_transport(pipe, delayed_clearance)
        OBSERVATIONS['callback_latency'] = dict(fake_write_times=writes, **clock)
        self.assertEqual(writes, [])


result = unittest.TextTestRunner(verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(FinalWriteProbe))
print(json.dumps(OBSERVATIONS, sort_keys=True))
sys.exit(0 if result.wasSuccessful() else 1)
