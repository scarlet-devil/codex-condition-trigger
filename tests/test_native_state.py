"""Bounded owner snapshot and old-history-gap regression contracts."""
import json
import unittest
from unittest import mock
import desktop_ipc as ipc
import test_desktop_ipc as fixtures


class SnapshotTests(unittest.TestCase):
    def client(self, change=None, outer=None, revision=12):
        helper = fixtures.WireTests()
        self.sent = []
        self.snapshot = dict(type='broadcast', method='thread-stream-state-changed', version=11,
            sourceClientId='owner', targetClientIds=['client'], params=dict(
                conversationId='target', hostId='local', change=dict(type='snapshot', revision=revision,
                    conversationState=dict(id='target', cwd='/work', resumeState='resumed',
                        threadRuntimeStatus=dict(type='idle')))))
        if change:
            self.snapshot['params']['change']['conversationState'].update(change)
        if outer:
            self.snapshot.update(outer)
        def replies(request):
            self.sent.append(request)
            if request['type'] == 'broadcast':
                return [self.snapshot] if request['params']['following'] else []
            response = helper.reply(request, handledByClientId='owner')
            response['result'] = {'revision': 12}
            return [response]
        return helper.client(replies)

    def test_current_status_is_bound_to_owner_target_cwd_and_revision(self):
        client = self.client()
        result = client.current_state('target', 'owner', '/work')
        self.assertEqual(result['status'], 'idle')
        self.assertEqual(result['revision'], 12)
        self.assertEqual(self.sent[-1]['params']['following'], False)
        self.assertTrue(all(r.get('targetClientIds', ['owner']) == ['owner'] for r in self.sent))
        self.assertEqual([r['method'] for r in self.sent if r['type'] == 'request'],
                         ['thread-follower-load-complete-history'])

    def test_busy_unknown_unresumed_and_wrong_identity_do_not_become_idle(self):
        for change, expected in [({'threadRuntimeStatus': {'type': 'active'}}, 'busy'),
                                 ({'threadRuntimeStatus': {'type': 'notLoaded'}}, 'unknown'),
                                 ({'threadRuntimeStatus': None}, 'unknown'),
                                 ({'resumeState': 'resuming'}, 'unknown')]:
            with self.subTest(change=change):
                self.assertEqual(self.client(change).current_state('target', 'owner', '/work')['status'], expected)
        for change in ({'id': 'other'}, {'cwd': '/other'}):
            with self.subTest(change=change), self.assertRaises(ipc.RPCError):
                self.client(change).current_state('target', 'owner', '/work')

    def test_old_revision_wrong_owner_or_targeted_client_is_not_evidence(self):
        cases = [dict(revision=11), dict(outer={'sourceClientId': 'other'}),
                 dict(outer={'targetClientIds': ['other']}), dict(outer={'version': 10})]
        for case in cases:
            with self.subTest(case=case), self.assertRaises((EOFError, TimeoutError)):
                self.client(**case).current_state('target', 'owner', '/work')
            self.assertFalse(self.sent[-1]['params']['following'])

    def test_malformed_runtime_type_cannot_escape_protocol_boundary(self):
        for value in ([], {}):
            with self.subTest(value=value):
                result = self.client({'threadRuntimeStatus': {'type': value}}).current_state('target', 'owner', '/work')
                self.assertEqual(result['status'], 'unknown')


class HistoryGapTests(fixtures.DesktopDispatchTests):
    # Only new regressions are collected from this class.
    def test_old_gap_does_not_block_fresh_idle_send_or_native_receipt(self):
        self.append('event_msg', type='task_started', turn_id='unclosed-old')
        self.append('event_msg', type='task_started', turn_id='later-old')
        self.append('event_msg', type='task_complete', turn_id='later-old')
        self.native_status = 'idle'
        self.ready()
        self.assertEqual(self.dispatch(), 'accepted')
        with mock.patch.object(self.client, 'current_state', side_effect=AssertionError('receipt needs no native query')):
            self.assertEqual(self.dispatch(), 'running')
        self.append('event_msg', type='task_complete', turn_id='native')
        self.assertEqual(self.dispatch(), 'completed')
        self.assertEqual(len(self.sent), 1)

    def test_unknown_native_state_does_not_infer_idle_from_history(self):
        self.native_status = 'unknown'
        self.ready()
        self.assertEqual(self.dispatch(), 'waiting_owner_unknown')
        self.assertEqual(self.sent, [])

    def test_failed_second_readonly_query_is_proven_not_dispatched(self):
        self.ready()
        with mock.patch.object(self.client, 'current_state', side_effect=[{'status': 'idle'}, ipc.RPCError('bad query')]):
            self.assertEqual(self.dispatch(), 'waiting_owner_unverified')
        self.assertEqual(self.sent, [])
        self.assertEqual(self.store.rows()[0]['state'], 'ready')


# Avoid rerunning inherited fixture tests already covered by their source module.
for name in dir(fixtures.DesktopDispatchTests):
    if name.startswith('test_') and name not in HistoryGapTests.__dict__:
        setattr(HistoryGapTests, name, None)
