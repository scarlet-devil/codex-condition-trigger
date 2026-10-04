"""Synthetic IPC contracts. These tests do not invoke Desktop or a model."""
import json
from pathlib import Path
import tempfile
import struct
import subprocess
import ctypes
from ctypes import wintypes
from types import SimpleNamespace
import os
import threading
import time
import unittest
from unittest import mock

import desktop_ipc as ipc
import trigger as tr
from test_trigger import Fixture


class RolloutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'rollout.jsonl'
        self.cwd = str(Path(self.tmp.name))
        self.rows = [{'type': 'session_meta', 'payload': {'id': 'target', 'cwd': self.cwd}}]

    def scan(self, *rows):
        self.path.write_text(''.join(json.dumps(r) + '\n' for r in self.rows + list(rows)))
        return ipc.rollout_state(self.path, 'target', self.cwd)

    def event(self, kind, turn='a'):
        return {'type': 'event_msg', 'payload': {'type': kind, 'turn_id': turn}}

    def test_busy_and_idle_require_lifecycle(self):
        self.assertEqual(self.scan(self.event('task_started'))['status'], 'busy')
        self.assertEqual(self.scan(self.event('task_started'), self.event('task_complete'))['status'], 'idle')

    def test_unrelated_context_records_do_not_drop_tool_actions(self):
        tool = {'type': 'response_item', 'payload': {'type': 'function_call', 'name': 'read', 'call_id': 'call'}}
        state = self.scan(self.event('task_started'), {'type': 'token_usage_record', 'payload': {}}, tool, self.event('task_complete'))
        self.assertEqual(state['status'], 'idle')
        self.assertIn(tool, state['turns']['a']['records'])

    def test_wrong_identity_is_rejected(self):
        self.rows[0]['payload']['id'] = 'other'
        with self.assertRaises(ValueError):
            self.scan(self.event('task_started'), self.event('task_complete'))

    def test_partial_and_unmatched_lifecycle_are_not_idle(self):
        self.scan(self.event('task_started'), self.event('task_complete'))
        with self.path.open('ab') as f:
            f.write(b'{"type":')
        with self.assertRaises(ValueError):
            ipc.rollout_state(self.path, 'target', self.cwd)
        with self.assertRaises(ValueError):
            self.scan(self.event('task_complete'))

    def test_overlapping_or_duplicate_starts_cannot_report_idle(self):
        for second in ('a', 'b'):
            with self.subTest(second=second), self.assertRaises(ValueError):
                self.scan(self.event('task_started', 'a'), self.event('task_started', second),
                          self.event('task_complete', second))

    def test_inherited_start_has_no_setting_overrides(self):
        params = ipc.start_params('target', 'client', 'fixed prompt')
        self.assertEqual(params.get('conversationId'), 'target')
        request = params['turnStart']['request']
        self.assertEqual(request, {'threadId': 'target', 'clientUserMessageId': 'client', 'input': [
            {'type': 'text', 'text': 'fixed prompt', 'text_elements': []}], 'additionalContext': {}})
        self.assertTrue(params['turnStart']['context']['inheritThreadSettings'])
        self.assertFalse(params['isSteering'])


class WireTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows overlapped-I/O contract')
    def test_interrupt_cancels_and_drains_before_freeing_storage(self):
        calls = []
        class Overlapped(ctypes.Structure):
            _fields_ = [('hEvent', wintypes.HANDLE)]
        def interrupted(*args):
            calls.append('wait')
            raise KeyboardInterrupt()
        pipe = ipc.WindowsPipe.__new__(ipc.WindowsPipe)
        pipe.ct, pipe.wt, pipe.Overlapped, pipe.handle = ctypes, wintypes, Overlapped, 123
        pipe.k = SimpleNamespace(
            CreateEventW=lambda *args: 456,
            ReadFile=lambda *args: False,
            WaitForSingleObject=interrupted,
            CancelIoEx=lambda *args: calls.append('cancel'),
            GetOverlappedResult=lambda *args: calls.append('drain'),
            CloseHandle=lambda *args: calls.append('close'))
        with mock.patch.object(ctypes, 'get_last_error', return_value=997):
            with self.assertRaises(KeyboardInterrupt):
                pipe.io(4, ipc.time.monotonic()+1)
        self.assertEqual(calls, ['wait', 'cancel', 'drain', 'close'])

    def client(self, replies, tick=None):
        class Pipe:
            def write(self, data, deadline):
                self.request = json.loads(data[4:])
                packets = replies(self.request)
                self.buffer = b''.join(struct.pack('<I', len(p)) + p for p in [json.dumps(x).encode() for x in packets])
            def read(self, size, deadline):
                if tick:
                    tick()
                data, self.buffer = self.buffer[:size], self.buffer[size:]
                if len(data) != size:
                    raise EOFError()
                return data
        client = ipc.IPCClient.__new__(ipc.IPCClient)
        client.client_id, client.timeout, client.pipe = 'client', 1, Pipe()
        return client

    def reply(self, request, **extra):
        return dict(type='response', requestId=request['requestId'], method=request['method'],
                    resultType='success', result={}, **extra)

    def test_unrelated_notification_then_exact_response(self):
        client = self.client(lambda r: [{'type': 'notification'}, self.reply(r, handledByClientId='owner')])
        self.assertEqual(client.request('thread-owner-discovery', {})['handledByClientId'], 'owner')

    def test_wrong_owner_response_rejected(self):
        client = self.client(lambda r: [self.reply(r, handledByClientId='different')])
        with self.assertRaises(ValueError):
            client.request('thread-follower-start-turn', {}, target='owner')

    def test_noise_cannot_extend_absolute_deadline(self):
        clock = [0.0]
        def tick():
            clock[0] += .2
        client = self.client(lambda r: [{'type': 'notification'}] * 20, tick)
        with mock.patch.object(ipc.time, 'monotonic', side_effect=lambda: clock[0]):
            with self.assertRaises(TimeoutError):
                client.request('initialize', {})
        self.assertLessEqual(clock[0], 1.2)

    def test_frame_limit_precedes_body_read(self):
        client = self.client(lambda r: [])
        client.pipe.read = lambda size, deadline: struct.pack('<I', ipc.MAX_FRAME + 1)
        with self.assertRaises(ValueError):
            client.request('initialize', {})


class DesktopDispatchTests(Fixture):
    def test_watcher_still_captures_after_host_check_failure(self):
        self.ready()
        checked, stop = threading.Event(), threading.Event()
        errors = []
        def unavailable(*args):
            checked.set()
            raise subprocess.TimeoutExpired('synthetic-signature-check', 20)
        def writer():
            try:
                if not checked.wait(3):
                    raise AssertionError('adapter was not checked')
                (self.input / 'second.json').write_text('{"synthetic":"later input"}')
                end = time.monotonic() + 3
                while len(list((self.store.path / 'batches').glob('*.json'))) < 2:
                    if time.monotonic() > end:
                        raise AssertionError('watcher failed to preserve later input')
                    time.sleep(.02)
            except BaseException as error:
                errors.append(error)
            finally:
                stop.set()
        child = threading.Thread(target=writer)
        child.start()
        try:
            with mock.patch.object(tr, 'make_adapter', side_effect=unavailable):
                tr.run(self.store, live=True, stop_event=stop)
        finally:
            stop.set()
            child.join(timeout=4)
        if errors:
            raise errors[0]
        self.assertEqual(len(self.store.rows()), 2)
        self.assertTrue(all(row['state'] == 'ready' for row in self.store.rows()))

    def test_host_check_process_failures_leave_local_batch_retryable(self):
        self.ready()
        for error in (subprocess.TimeoutExpired('signature-check', 20),
                      subprocess.CalledProcessError(1, 'signature-check')):
            with self.subTest(error=type(error).__name__):
                self.store.update(self.store.rows()[0]['id'], 'ready', next_try=0)
                def fail(c, paused):
                    raise error
                self.assertEqual(tr.dispatch_one(self.store, adapter_factory=fail), 'pending')
                self.assertEqual(self.store.rows()[0]['state'], 'ready')

    def setUp(self):
        super().setUp()
        self.store.close()
        self.config.update(chat_adapter='desktop_ipc', state_dir=str(self.root / 'ipc-state'),
                           rollout_path=str(self.root / 'rollout.jsonl'))
        self.store = tr.Store(self.config)
        self.scanner = tr.StableScanner(self.store)
        self.path = Path(self.config['rollout_path'])
        self.path.write_text(json.dumps({'type': 'session_meta', 'payload': {
            'id': self.config['thread_id'], 'cwd': self.config['expected_cwd']}}) + '\n')
        self.append('event_msg', type='task_started', turn_id='old')
        self.append('event_msg', type='task_complete', turn_id='old')
        self.sent = []
        self.lose_ack = False
        self.match_text = None
        self.owner_changed = False
        test = self
        class Client:
            client_id, installation = 'source-client', {'synthetic': True}
            owners = 0
            def owner(self, thread):
                self.owners += 1
                return 'other' if test.owner_changed and self.owners > 1 else 'owner'
            def request(self, method, params, **kwargs):
                test.sent.append((method, params, kwargs))
                test.append('event_msg', type='task_started', turn_id='native')
                text = params['turnStart']['request']['input'][0]['text']
                test.append('response_item', type='message', role='user', content=[{
                    'type': 'input_text', 'text': text if test.match_text is None else test.match_text}])
                if test.lose_ack:
                    raise TimeoutError()
                return {'result': {'result': {'turn': {'id': 'native'}}}}
            def close(self):
                pass
        self.client = Client

    def append(self, kind, **payload):
        with self.path.open('a') as f:
            f.write(json.dumps({'type': kind, 'payload': payload}) + '\n')

    def adapter(self, c, paused):
        return ipc.DesktopAdapter(c, paused, lambda timeout: self.client())

    def dispatch(self):
        return tr.dispatch_one(self.store, adapter_factory=self.adapter)

    def test_busy_keeps_batch_local(self):
        self.ready()
        self.append('event_msg', type='task_started', turn_id='busy')
        self.assertEqual(self.dispatch(), 'waiting_owner_busy')
        self.assertEqual(self.store.rows()[0]['state'], 'ready')
        self.assertEqual(self.sent, [])

    def test_native_acceptance_completion_and_ack_are_distinct(self):
        batch = self.ready()
        self.assertEqual(self.dispatch(), 'accepted')
        self.assertIsNone(self.store.rows()[0]['submission'])
        self.assertEqual(self.dispatch(), 'running')
        self.append('event_msg', type='task_complete', turn_id='native')
        self.assertEqual(self.dispatch(), 'completed')
        self.assertEqual(len(self.sent), 1)
        receipt = self.root / 'receipt.json'
        receipt.write_text('{"synthetic_result_verified":true}')
        self.store.acknowledge(batch, receipt)
        self.assertEqual(self.dispatch(), 'quiet')

    def test_lost_ack_exact_new_turn_reconciles_without_resend(self):
        self.ready()
        self.lose_ack = True
        self.assertEqual(self.dispatch(), 'uncertain')
        self.reopen()
        self.assertEqual(self.dispatch(), 'running')
        self.assertEqual(len(self.sent), 1)

    def test_plain_reference_after_lost_ack_remains_uncertain(self):
        batch = self.ready()
        self.lose_ack, self.match_text = True, 'Explain batch_id=' + batch
        self.assertEqual(self.dispatch(), 'uncertain')
        self.assertEqual(self.dispatch(), 'uncertain')
        self.assertEqual(len(self.sent), 1)

    def test_rewritten_rollout_cannot_reconcile(self):
        self.ready()
        self.lose_ack = True
        self.assertEqual(self.dispatch(), 'uncertain')
        self.path.write_text(self.path.read_text().replace('"old"', '"odd"'))
        self.assertEqual(self.dispatch(), 'pending')
        self.assertEqual(self.store.rows()[0]['state'], 'uncertain')
        self.assertEqual(len(self.sent), 1)

    def test_owner_change_and_stop_prevent_send_after_intent(self):
        self.ready()
        self.owner_changed = True
        self.assertEqual(self.dispatch(), 'waiting_owner_changed')
        self.assertEqual(self.sent, [])
        self.assertEqual(self.store.rows()[0]['state'], 'ready')
        self.owner_changed = False
        original = self.client.owner
        test = self
        def stop(client, thread):
            result = original(client, thread)
            if client.owners > 1:
                (test.store.path / 'STOP').touch()
            return result
        self.client.owner = stop
        self.assertEqual(self.dispatch(), 'paused')
        self.assertEqual(self.sent, [])

    def test_ack_wins_against_stale_ipc_result(self):
        batch = self.ready()
        self.assertEqual(self.dispatch(), 'accepted')
        receipt = self.root / 'receipt.json'
        receipt.write_text('{"synthetic_result_verified":true}')
        original = ipc.DesktopAdapter.observe
        def racing(adapter, row):
            result = original(adapter, row)
            other = tr.Store(self.config, worker=False)
            try:
                other.acknowledge(batch, receipt)
            finally:
                other.close()
            return result
        with mock.patch.object(ipc.DesktopAdapter, 'observe', racing):
            self.assertEqual(self.dispatch(), 'delivered')
        self.assertEqual(self.store.rows()[0]['state'], 'delivered')


if __name__ == '__main__':
    unittest.main()
