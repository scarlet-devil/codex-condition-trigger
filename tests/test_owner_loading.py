"""Synthetic owner recovery checks. No native IPC or window actions."""
import unittest
from types import SimpleNamespace
from unittest import mock

import desktop_ipc as ipc
import trigger as tr
from test_desktop_ipc import WireTests, DesktopDispatchTests


class NegativeReplyTests(WireTests):
    def test_initialize_errors_preserve_stage_and_fixed_category(self):
        for error, expected in ((TimeoutError('private'), 'timeout'),
                                (OSError('private'), 'transport'), (ValueError('private'), 'protocol')):
            client = self.client(lambda r: [])
            with mock.patch.object(ipc.IPCClient, 'request', side_effect=error):
                with self.assertRaises(ipc.IPCFailure) as caught:
                    ipc.IPCClient(1, pipe=client.pipe, verifier=lambda p: {})
            self.assertEqual((caught.exception.stage, caught.exception.category), ('initialize', expected))
            self.assertNotIn('private', str(caught.exception))

    def test_correlated_negative_without_method_keeps_fixed_reason(self):
        client = self.client(lambda r: [dict(type='response', requestId=r['requestId'],
                                            resultType='error', error='no-client-found')])
        with self.assertRaises(ipc.IPCFailure) as caught:
            client.owner('target')
        self.assertEqual((caught.exception.stage, caught.exception.category),
                         ('owner_discovery', 'owner_unavailable'))

    def test_unknown_remote_error_is_redacted_and_not_owner_missing(self):
        client = self.client(lambda r: [dict(type='response', requestId=r['requestId'],
                                            resultType='error', error='secret remote detail')])
        with self.assertRaises(ipc.IPCFailure) as caught:
            client.owner('target')
        self.assertEqual(caught.exception.category, 'remote_rejected')
        self.assertNotIn('secret', str(caught.exception))

    def test_mismatched_negative_is_ignored(self):
        client = self.client(lambda r: [dict(type='response', requestId='other',
            resultType='error', error='no-client-found'), self.reply(r, handledByClientId='owner')])
        self.assertEqual(client.owner('target'), 'owner')

    def test_success_still_requires_method_and_exact_target(self):
        for value in ({'method': None}, {'handledByClientId': 'other'}):
            client = self.client(lambda r: [dict(self.reply(r, handledByClientId='owner'), **value)])
            with self.assertRaises(ValueError):
                client.request('thread-follower-start-turn', {}, target='owner')


class OwnerLoadingTests(DesktopDispatchTests):
    def setUp(self):
        super().setUp()
        self.ready()
        self.missing = True
        original = self.client.owner
        case = self
        def owner(client, thread):
            if case.missing:
                raise ipc.IPCFailure('owner_discovery', 'owner_unavailable')
            return original(client, thread)
        self.client.owner = owner
        self.loads = []

    def load(self, **kwargs):
        self.loads.append(kwargs)
        self.missing = False
        return {'token': 'synthetic-lease', 'thread_id': self.config['thread_id']}

    def prepare_owner(self, loader=None):
        from owner_loading import WindowCycles
        backend = SimpleNamespace(open=loader) if loader else None
        return WindowCycles(self.store, backend, self.adapter).step()

    def test_owner_wait_survives_restart_without_spending_connection_budget(self):
        for n in range(8):
            self.assertEqual(tr.dispatch_one(self.store, now=100+n*60, adapter_factory=self.adapter), 'waiting_owner')
        self.reopen()
        row = self.store.rows()[0]
        self.assertEqual((row['state'], row['attempts'], row['detail']), ('ready', 0, 'waiting_owner'))
        self.missing = False
        self.assertEqual(tr.dispatch_one(self.store, now=1000, adapter_factory=self.adapter), 'accepted')
        self.assertEqual(len(self.sent), 1)

    def test_owner_lost_during_snapshot_also_waits_without_failure_budget(self):
        self.missing = False
        with mock.patch.object(self.client, 'current_state', side_effect=ipc.IPCFailure('current_state', 'owner_unavailable')):
            for n in range(8):
                self.assertEqual(tr.dispatch_one(self.store, now=100+n*60, adapter_factory=self.adapter), 'waiting_owner')
        self.assertEqual(self.store.rows()[0]['attempts'], 0)
        self.assertEqual(self.sent, [])

    def test_negative_start_reply_remains_uncertain_and_never_loads(self):
        self.missing = False
        self.config['owner_loading_enabled'] = True
        with mock.patch.object(self.client, 'request', side_effect=ipc.IPCFailure('start_turn', 'owner_unavailable')):
            self.assertEqual(self.dispatch(), 'uncertain')
        self.assertEqual(self.prepare_owner(self.load), 'receipt_only')
        self.assertEqual(self.loads, [])

    def test_waiting_does_not_prevent_later_file_capture(self):
        self.dispatch()
        self.ready(b'second version')
        self.assertEqual(len(self.store.rows()), 2)

    def test_loader_disabled_by_default(self):
        self.assertEqual(self.prepare_owner(self.load), 'loader_disabled')
        self.assertEqual(self.loads, [])

    def test_inspect_never_loads(self):
        self.config['owner_loading_enabled'] = True
        self.assertEqual(self.dispatch(), 'waiting_owner')
        self.assertEqual(self.loads, [])

    def test_available_owner_reused_without_backend_or_window_action(self):
        self.config['owner_loading_enabled'] = True
        self.missing = False
        self.assertEqual(self.prepare_owner(self.load), 'owner_ready')
        self.assertEqual(self.loads, [])

    def test_load_is_explicit_no_prompt_and_rechecks_owner(self):
        self.config['owner_loading_enabled'] = True
        self.assertEqual(self.prepare_owner(self.load), 'owner_ready')
        self.assertEqual(set(self.loads[0]), {'thread_id', 'expected_cwd', 'timeout_seconds'})
        self.assertEqual(self.loads[0]['thread_id'], self.config['thread_id'])
        self.assertEqual(self.sent, [])
        self.assertEqual(self.store.rows()[0]['state'], 'ready')

    def test_one_load_budget_is_durable_across_failures_and_new_batch(self):
        self.config['owner_loading_enabled'] = True
        def failure(**kwargs):
            self.loads.append(kwargs)
            raise OSError('private backend detail')
        self.assertEqual(self.prepare_owner(failure), 'window_open_unknown')
        self.reopen()
        self.ready(b'new file event')
        self.assertEqual(self.prepare_owner(self.load), 'window_reconciliation_required')
        self.assertEqual(len(self.loads), 1)
        self.assertEqual(self.sent, [])

    def test_not_configured_does_not_spend_action_budget(self):
        self.config['owner_loading_enabled'] = True
        self.assertEqual(self.prepare_owner(), 'loader_unavailable')
        self.assertEqual(self.prepare_owner(self.load), 'owner_ready')

    def test_stop_and_every_sent_state_block_loading(self):
        self.config['owner_loading_enabled'] = True
        row = self.store.rows()[0]
        for state in ('accepted', 'queued', 'running', 'completed', 'uncertain', 'failed', 'sending'):
            self.store.update(row['id'], state)
            self.assertEqual(self.prepare_owner(self.load), 'receipt_only')
        self.store.update(row['id'], 'ready')
        (self.store.path / 'STOP').touch()
        self.assertEqual(self.prepare_owner(self.load), 'paused')
        self.assertEqual(self.loads, [])

    def test_ready_with_prior_send_intent_cannot_load(self):
        self.config['owner_loading_enabled'] = True
        self.store.update(self.store.rows()[0]['id'], 'ready', dispatch_text='old intent')
        self.assertEqual(self.prepare_owner(self.load), 'receipt_only')

    def test_after_load_busy_is_not_ready(self):
        self.config['owner_loading_enabled'] = True
        self.native_status = 'busy'
        self.assertEqual(self.prepare_owner(self.load), 'waiting_owner_busy')
        self.assertEqual(self.sent, [])

    def test_non_owner_error_cannot_trigger_loader(self):
        self.config['owner_loading_enabled'] = True
        with mock.patch.object(self.client, 'owner', side_effect=ipc.IPCFailure('owner_discovery', 'timeout')):
            self.assertEqual(self.prepare_owner(self.load), 'owner_check_failed')
        self.assertEqual(self.loads, [])

    def test_stop_appearing_after_owner_check_prevents_action(self):
        self.config['owner_loading_enabled'] = True
        original = self.client.owner
        def stop_then_missing(client, thread):
            (self.store.path / 'STOP').touch()
            return original(client, thread)
        with mock.patch.object(self.client, 'owner', stop_then_missing):
            self.assertEqual(self.prepare_owner(self.load), 'paused')
        self.assertEqual(self.loads, [])

    def test_owner_presence_does_not_override_bad_thread_identity(self):
        self.config['owner_loading_enabled'] = True
        with mock.patch.object(self.client, 'current_state', side_effect=ipc.RPCError('wrong cwd')):
            self.assertEqual(self.prepare_owner(self.load), 'owner_check_failed')
        self.assertEqual(len(self.loads), 1)
        self.assertEqual(self.sent, [])


def load_tests(loader, tests, pattern):
    # Fixtures supply helpers; their existing cases run in their own module.
    return unittest.TestSuite(cls(name) for cls in (NegativeReplyTests, OwnerLoadingTests)
        for name in cls.__dict__ if name.startswith('test_'))
