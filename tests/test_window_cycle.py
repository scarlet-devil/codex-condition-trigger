"""Stateful lifecycle contracts; all IPC and window actions are synthetic."""
import json
import unittest
from unittest import mock

from test_desktop_ipc import DesktopDispatchTests
import trigger as tr
from owner_loading import WindowCycles, cycle_tick


class CycleTests(DesktopDispatchTests):
    def setUp(self):
        super().setUp()
        self.config['owner_loading_enabled'] = True
        self.ready()
        self.available = True
        self.window = 'owned'
        self.actions = []
        case = self
        original = self.client.owner
        def owner(client, target):
            if not case.available:
                from desktop_ipc import IPCFailure
                raise IPCFailure('owner_discovery', 'owner_unavailable')
            return original(client, target)
        self.client.owner = owner
        def request(client, method, params, **kwargs):
            case.sent.append((method, params, kwargs))
            turn = 'cycle-turn-' + str(len(case.sent))
            case.append('event_msg', type='task_started', turn_id=turn)
            case.append('response_item', type='message', role='user', content=[{
                'type': 'input_text', 'text': params['turnStart']['request']['input'][0]['text']}])
            return {'result': {'result': {'turn': {'id': turn}}}}
        self.client.request = request
        class Backend:
            def open(self, **kwargs):
                case.actions.append('open')
                case.available = True
                return {'token': 'synthetic-owned-window', 'thread_id': case.config['thread_id']}
            def inspect(self, lease):
                return {'status': case.window}
            def close(self, lease):
                case.actions.append('close')
                case.window = 'absent'
                return {'status': 'absent'}
        self.backend = Backend()

    def manager(self):
        return WindowCycles(self.store, self.backend, self.adapter)

    def tick(self):
        return cycle_tick(self.store, self.backend, self.adapter)

    def complete(self, ack=True):
        row = next(r for r in self.store.rows() if r['state'] != 'delivered')
        self.append('event_msg', type='task_complete', turn_id=row['turn_id'])
        self.dispatch()
        if ack:
            p = self.root / (row['id'] + '.receipt')
            p.write_text('caller verified synthetic result')
            self.store.acknowledge(row['id'], p)

    def test_idle_reused_and_busy_waits_without_window_actions(self):
        self.native_status = 'busy'
        self.assertEqual(self.tick(), 'waiting_owner_busy')
        self.assertEqual(self.sent, [])
        self.native_status = 'idle'
        self.assertEqual(self.tick(), 'accepted')
        self.complete()
        self.tick()
        self.assertEqual(self.actions, [])

    def test_two_batches_after_verified_close_have_separate_load_budget(self):
        self.available = False
        self.assertEqual(self.tick(), 'accepted')
        self.complete()
        self.assertEqual(self.tick(), 'cycle_closed')
        self.assertEqual(self.actions, ['open', 'close'])
        self.available, self.window = False, 'owned'
        self.ready(b'different second batch')
        self.assertEqual(self.tick(), 'accepted')
        self.complete()
        self.assertEqual(self.tick(), 'cycle_closed')
        self.assertEqual(self.actions, ['open', 'close', 'open', 'close'])
        self.assertEqual(len(self.sent), 2)

    def test_surviving_owner_reused_on_second_batch(self):
        self.available = False
        self.tick(); self.complete(); self.tick()
        self.ready(b'second')
        self.assertEqual(self.tick(), 'accepted')
        self.assertEqual(self.actions, ['open', 'close'])

    def test_open_timeout_survives_restart_and_new_batch(self):
        self.available = False
        with mock.patch.object(self.backend, 'open', side_effect=TimeoutError):
            self.assertEqual(self.tick(), 'window_open_unknown')
        self.reopen(); self.ready(b'next file')
        self.assertEqual(self.tick(), 'window_reconciliation_required')
        self.assertEqual(self.actions, [])
        self.assertEqual(self.sent, [])

    def test_sent_batch_never_loads_after_owner_loss(self):
        self.tick(); self.available = False
        self.assertEqual(self.tick(), 'running')
        self.assertEqual(self.actions, [])
        self.assertEqual(len(self.sent), 1)

    def test_completion_alone_does_not_close_or_ack(self):
        self.available = False
        self.tick(); self.complete(ack=False)
        self.tick()
        self.assertEqual(self.actions, ['open'])
        self.assertEqual(self.store.rows()[0]['state'], 'completed')

    def test_early_ack_does_not_close_active_turn(self):
        self.available = False
        self.tick()
        p = self.root / 'receipt'; p.write_text('caller attestation')
        self.store.acknowledge(self.store.rows()[0]['id'], p)
        self.assertEqual(self.tick(), 'waiting_turn_completion')
        self.assertEqual(self.actions, ['open'])

    def test_close_failure_preserves_delivery_and_blocks_next_send(self):
        self.available = False
        self.tick(); self.complete()
        original_detail = self.store.rows()[0]['detail']
        with mock.patch.object(self.backend, 'close', side_effect=TimeoutError):
            self.assertEqual(self.tick(), 'window_close_unknown')
        self.reopen(); self.ready(b'next')
        self.assertEqual(self.tick(), 'window_reconciliation_required')
        self.assertEqual(self.store.rows()[0]['state'], 'delivered')
        self.assertEqual(self.store.rows()[0]['detail'], original_detail)
        self.assertEqual(len(self.sent), 1)
        self.window = 'absent'
        self.assertEqual(self.tick(), 'cycle_closed')
        self.assertEqual(self.tick(), 'accepted')

    def test_changed_window_identity_not_closed(self):
        self.available = False
        self.tick(); self.complete(); self.window = 'mismatch'
        self.assertEqual(self.tick(), 'window_identity_unconfirmed')
        self.assertEqual(self.actions, ['open'])

    def test_busy_after_ack_delays_close(self):
        self.available = False
        self.tick(); self.complete(); self.native_status = 'busy'
        self.assertEqual(self.tick(), 'waiting_owner_busy')
        self.assertEqual(self.actions, ['open'])

    def test_legacy_claim_not_silently_reset(self):
        key = 'owner_load_attempt:' + self.config['thread_id']
        with self.store.db:
            self.store.db.execute('INSERT INTO meta VALUES (?,?)', (key, '{"legacy":true}'))
        self.assertEqual(self.tick(), 'legacy_reconciliation_required')
        self.assertEqual(self.actions, [])

    def test_unknown_owner_reply_never_opens(self):
        from desktop_ipc import IPCFailure
        with mock.patch.object(self.client, 'owner', side_effect=IPCFailure('owner_discovery', 'timeout')):
            self.assertEqual(self.tick(), 'owner_check_failed')
        self.assertEqual(self.actions, [])

    def test_stop_during_open_preserves_lease_without_sending(self):
        self.available = False
        original = self.backend.open
        def stop(**kwargs):
            value = original(**kwargs)
            (self.store.path / 'STOP').touch()
            return value
        with mock.patch.object(self.backend, 'open', stop):
            self.assertEqual(self.tick(), 'paused')
        self.assertEqual(self.sent, [])
        self.assertTrue(self.manager().records()[0]['lease'])

    def test_no_files_no_window_or_ipc(self):
        self.store.db.execute('DELETE FROM batches'); self.store.db.commit()
        with mock.patch.object(self.client, 'owner', side_effect=AssertionError('no query')):
            self.assertEqual(self.tick(), 'quiet')
        self.assertEqual(self.actions, [])

    def test_worker_lock_required_for_lifecycle(self):
        self.store.close(); self.store = tr.Store(self.config, worker=False)
        with self.assertRaises(ValueError):
            self.manager()

    def test_ack_between_prepare_and_dispatch_cannot_send_next_batch(self):
        self.available = False
        self.tick(); self.complete(ack=False); self.ready(b'next waiting batch')
        original = WindowCycles.step
        def raced(manager):
            result = original(manager)
            receipt = self.root / 'concurrent-ack'; receipt.write_text('verified result')
            external = tr.Store(self.config, worker=False)
            try:
                external.acknowledge(self.store.rows()[0]['id'], receipt)
            finally:
                external.close()
            return result
        with mock.patch.object(WindowCycles, 'step', raced):
            self.tick()
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.actions, ['open'])
        self.assertEqual(self.tick(), 'cycle_closed')
        self.assertEqual(self.tick(), 'accepted')
        self.assertEqual(self.actions, ['open', 'close'])

    def test_lost_acceptance_requires_correlation_before_cycle_ack(self):
        self.available = False
        original = self.client.request
        def lose(client, *args, **kwargs):
            original(client, *args, **kwargs)
            raise TimeoutError('reply lost')
        with mock.patch.object(self.client, 'request', lose):
            self.assertEqual(self.tick(), 'uncertain')
        self.append('event_msg', type='task_complete', turn_id='cycle-turn-1')
        receipt = self.root / 'receipt'; receipt.write_text('verified')
        with self.assertRaisesRegex(ValueError, 'correlated turn'):
            self.store.acknowledge(self.store.rows()[0]['id'], receipt)
        self.assertEqual(self.tick(), 'completed')
        self.store.acknowledge(self.store.rows()[0]['id'], receipt)
        self.assertEqual(self.tick(), 'cycle_closed')
        self.assertEqual(len(self.sent), 1)

    def test_disabling_loader_cannot_bypass_unclosed_cycle(self):
        self.available = False
        self.tick(); self.complete(); self.ready(b'next')
        self.config['owner_loading_enabled'] = False
        self.assertEqual(self.tick(), 'window_cycle_disabled_reconciliation_required')
        self.assertEqual(len(self.sent), 1)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(CycleTests(name) for name in CycleTests.__dict__ if name.startswith('test_'))
