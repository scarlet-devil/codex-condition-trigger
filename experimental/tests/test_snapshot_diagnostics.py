"""Failure labels through the real parser/validator, with synthetic wire bytes."""
import json
import ntpath
import struct
import unittest
from unittest import mock

from experimental import snapshot_measure as sm
from experimental.tests.test_snapshot_measure import Pipe, verified

HISTORY = 'thread-follower-load-complete-history'


class ChangedPipe(Pipe):
    def __init__(self, change=lambda value: value, cleanup_error=None):
        super().__init__()
        self.change = change
        self.cleanup_error = cleanup_error

    def add(self, value):
        value = self.change(value)
        if isinstance(value, bytes):
            self.buffer += struct.pack('<I', len(value)) + value
        else:
            super().add(value)

    def write(self, data, deadline):
        item = json.loads(data[4:])
        if (item['method'] == sm.FOLLOW and not item['params']['following']
                and self.cleanup_error is not None):
            raise self.cleanup_error
        super().write(data, deadline)


def response_change(**fields):
    def change(item):
        if item.get('type') == 'response' and item.get('method') == HISTORY:
            item.update(fields)
        return item
    return change


def snapshot_change(part, value):
    def change(item):
        if item.get('method') == 'thread-stream-state-changed':
            if part == 'params':
                item['params'] = value
            elif part == 'change':
                item['params']['change'] = value
            elif part == 'state':
                item['params']['change']['conversationState'] = value
            else:
                item['params']['change']['conversationState'][part] = value
        return item
    return change


class DiagnosticTests(unittest.TestCase):
    def measure(self, pipe):
        result = sm.measure_snapshot(pipe, 'private-thread', '/private-work', verifier=verified)
        self.assertFalse(result['can_send'])
        self.assertEqual(result['model_sends'], 0)
        self.assertTrue(pipe.closed)
        exported = json.dumps(result)
        for secret in ('private-thread', 'private-owner', 'private-client', '/private-work', 'DO_NOT_EXPORT'):
            self.assertNotIn(secret, exported)
        self.assertTrue(all(x['method'] in sm.REQUESTS | {sm.FOLLOW} for x in pipe.sent))
        return result

    def assert_rejected(self, result, reason):
        self.assertFalse(result['snapshot_query_completed'])
        self.assertEqual(result['runtime_status'], 'unknown')
        self.assertEqual(result['error_reason'], reason)

    def test_response_validation_reasons(self):
        cases = [({'result': None}, 'history_result_not_object'),
                 ({'method': 'DO_NOT_EXPORT'}, 'response_method_mismatch'),
                 ({'handledByClientId': 'DO_NOT_EXPORT'}, 'response_owner_mismatch'),
                 ({'resultType': 'DO_NOT_EXPORT'}, 'response_not_success')]
        cases.extend(({'result': {'revision': value}}, 'history_revision_invalid')
                     for value in (None, True, -1, '12', []))
        for change, reason in cases:
            with self.subTest(reason=reason, change=change):
                result = self.measure(ChangedPipe(response_change(**change)))
                self.assert_rejected(result, reason)
                self.assertEqual(result['error_stage'], 'current_state')
                self.assertEqual(result['error_category'], 'protocol')

    def test_snapshot_validation_reasons(self):
        for part, value, reason in (
                ('params', None, 'snapshot_params_not_object'),
                ('change', [], 'snapshot_change_not_object'),
                ('state', None, 'snapshot_state_not_object'),
                ('id', 'DO_NOT_EXPORT', 'snapshot_thread_mismatch'),
                ('cwd', 42, 'snapshot_cwd_invalid'),
                ('cwd', '/DO_NOT_EXPORT', 'snapshot_cwd_mismatch')):
            with self.subTest(reason=reason):
                result = self.measure(ChangedPipe(snapshot_change(part, value)))
                self.assert_rejected(result, reason)

    def test_bad_json_and_nonobject_frames_are_distinct(self):
        for body, reason in ((None, 'frame_not_object'), ([], 'frame_not_object'),
                             (b'\xff', 'frame_json_invalid'),
                             (b'{"DO_NOT_EXPORT":', 'frame_json_invalid')):
            def change(item, body=body):
                return body if item.get('method') == HISTORY else item
            with self.subTest(reason=reason):
                self.assert_rejected(self.measure(ChangedPipe(change)), reason)

    def test_remote_error_text_cannot_spoof_local_reason(self):
        p = ChangedPipe(response_change(resultType='error', error='snapshot_cwd_mismatch DO_NOT_EXPORT'))
        self.assert_rejected(self.measure(p), 'remote_rejected')
        def fail(item):
            if item.get('method') == HISTORY:
                raise sm.ipc.RPCError('snapshot_cwd_mismatch DO_NOT_EXPORT')
            return item
        self.assert_rejected(self.measure(ChangedPipe(fail)), 'protocol_unclassified')
        self.assertEqual(str(sm.ProbeFailure('DO_NOT_EXPORT')), 'probe_unclassified')
        self.assertEqual(sm.ipc.protocol_reason(sm.ipc.ProtocolCheckError('DO_NOT_EXPORT')),
                         'protocol_unclassified')

    def test_cleanup_error_does_not_replace_primary_rejection(self):
        p = ChangedPipe(snapshot_change('cwd', '/DO_NOT_EXPORT'), ValueError('DO_NOT_EXPORT'))
        r = self.measure(p)
        self.assert_rejected(r, 'snapshot_cwd_mismatch')
        self.assertEqual(r['error_stage'], 'current_state')
        self.assertEqual(r['unsubscribe_failure'], {
            'category': 'protocol', 'reason': 'protocol_unclassified', 'primary_failed': True})

    def test_cleanup_only_failure_invalidates_sample(self):
        for error in (OSError('DO_NOT_EXPORT'), ValueError('DO_NOT_EXPORT')):
            with self.subTest(error=type(error).__name__):
                r = self.measure(ChangedPipe(cleanup_error=error))
                self.assertFalse(r['snapshot_query_completed'])
                self.assertEqual(r['runtime_status'], 'unknown')
                self.assertEqual(r['error_stage'], 'current_state_cleanup')
                self.assertFalse(r['unsubscribe_failure']['primary_failed'])

    def test_untrusted_or_stale_snapshots_still_fail_closed(self):
        def change(item):
            if item.get('method') == 'thread-stream-state-changed':
                item.update(fields)
                if revision is not None:
                    item['params']['change']['revision'] = revision
            return item
        for fields, revision in (({}, 11), ({'version': 10}, None),
                                 ({'sourceClientId': 'other'}, None),
                                 ({'targetClientIds': ['other']}, None)):
            with self.subTest(fields=fields, revision=revision):
                self.assert_rejected(self.measure(ChangedPipe(change)), 'transport_failed')

    def test_extended_path_equivalence_is_not_silently_enabled(self):
        p = ChangedPipe(snapshot_change('cwd', r'\\?\D:\project'))
        with mock.patch.object(sm.ipc.os, 'path', ntpath):
            r = sm.measure_snapshot(p, 'private-thread', r'D:\project', verifier=verified)
        self.assert_rejected(r, 'snapshot_cwd_mismatch')
        self.assertNotIn('project', json.dumps(r))

    def test_cancellation_survives_secondary_cleanup_error(self):
        def cancel(item):
            if item.get('method') == HISTORY:
                raise KeyboardInterrupt()
            return item
        p = ChangedPipe(cancel, ValueError('DO_NOT_EXPORT'))
        with self.assertRaises(KeyboardInterrupt):
            self.measure(p)
        self.assertTrue(p.closed)


if __name__ == '__main__':
    unittest.main()
