"""Synthetic transport tests: no Windows host, model, filesystem or GUI actions."""
import json
import os
import struct
import unittest
from unittest import mock

from experimental import snapshot_measure as sm

WORK_CWD = r'D:\private-work' if os.name == 'nt' else '/private-work'


class Pipe:
    def __init__(self, *, status='idle', wrong_cwd=False, owner_change=False,
                 oversize=False, noise=0, fail_read=False, tick=None):
        self.buffer = b''
        self.sent, self.read_sizes, self.deadlines = [], [], []
        self.status, self.wrong_cwd, self.owner_change = status, wrong_cwd, owner_change
        self.oversize, self.noise, self.fail_read, self.tick = oversize, noise, fail_read, tick
        self.owner_calls = self.rx = self.tx = self.closed = 0

    def add(self, value):
        body = json.dumps(value).encode()
        self.buffer += struct.pack('<I', len(body)) + body

    def write(self, data, deadline):
        self.deadlines.append(deadline)
        self.tx += len(data)
        r = json.loads(data[4:])
        self.sent.append(r)
        method = r['method']
        if r['type'] == 'broadcast':
            if r['params']['following']:
                self.add({
                    'type': 'broadcast', 'method': 'thread-stream-state-changed', 'version': 11,
                    'sourceClientId': 'private-owner', 'targetClientIds': ['private-client'],
                    'params': {'hostId': 'local', 'conversationId': 'private-thread', 'change': {
                        'type': 'snapshot', 'revision': 12, 'conversationState': {
                            'id': 'private-thread', 'cwd': '/wrong' if self.wrong_cwd else WORK_CWD,
                            'resumeState': 'resumed', 'threadRuntimeStatus': {'type': self.status},
                            'turns': [{'private': 'DO_NOT_EXPORT_HISTORY'}]}}}})
            return
        if method == 'thread-follower-load-complete-history' and self.oversize:
            self.buffer += struct.pack('<I', sm.FRAME_CAP + 1)
            return
        for _ in range(self.noise):
            self.add({'type': 'notification', 'private': 'DO_NOT_EXPORT_NOISE'})
        owner = 'private-owner'
        if method == 'thread-owner-discovery':
            self.owner_calls += 1
            if self.owner_change and self.owner_calls > 1:
                owner = 'changed-owner'
        self.add({'type': 'response', 'requestId': r['requestId'], 'method': method,
                  'handledByClientId': owner, 'resultType': 'success',
                  'result': {'clientId': 'private-client'} if method == 'initialize' else {'revision': 12}})

    def read(self, size, deadline):
        self.deadlines.append(deadline)
        self.read_sizes.append(size)
        if self.tick:
            self.tick()
        if self.fail_read and size > 4:
            raise EOFError('DO_NOT_EXPORT_PARTIAL_BODY')
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        self.rx += len(data)
        if len(data) != size:
            raise EOFError()
        return data

    def close(self):
        self.closed += 1


def verified(_):
    return {'archive_sha256': sm.ARCHIVE_SHA256, 'private': 'DO_NOT_EXPORT_INSTALLATION'}


class MeasurementTests(unittest.TestCase):
    def measure(self, pipe, **kwargs):
        return sm.measure_snapshot(pipe, 'private-thread', WORK_CWD, verifier=verified, **kwargs)

    def test_full_query_counts_all_bytes_and_exports_only_projection(self):
        p = Pipe()
        r = self.measure(p)
        self.assertTrue(r['snapshot_query_completed'])
        self.assertEqual(r['runtime_status'], 'idle')
        self.assertFalse(r['can_send'])
        self.assertEqual(r['measurements']['completed_read_bytes'], p.rx)
        self.assertEqual(r['measurements']['completed_write_bytes'], p.tx)
        self.assertGreaterEqual(r['measurements']['target_snapshot_bodies'], 2)
        self.assertEqual(r['revision'], r['requested_revision'])
        self.assertTrue(r['owner_same_after'])
        self.assertTrue(p.closed)
        exported = json.dumps(r)
        for secret in ('private-thread', 'private-owner', 'private-client', WORK_CWD, 'DO_NOT_EXPORT'):
            self.assertNotIn(json.dumps(secret)[1:-1], exported)
        self.assertEqual({x['method'] for x in p.sent}, sm.REQUESTS | {sm.FOLLOW})

    def test_busy_and_unknown_are_not_send_permission(self):
        for native, expected in [('active', 'busy'), ('notLoaded', 'unknown')]:
            with self.subTest(native=native):
                r = self.measure(Pipe(status=native))
                self.assertTrue(r['snapshot_query_completed'])
                self.assertEqual(r['runtime_status'], expected)
                self.assertFalse(r['can_send'])

    def test_wrong_native_cwd_is_rejected(self):
        r = self.measure(Pipe(wrong_cwd=True))
        self.assertFalse(r['snapshot_query_completed'])
        self.assertEqual(r['runtime_status'], 'unknown')

    def test_owner_change_after_snapshot_invalidates_idle(self):
        r = self.measure(Pipe(owner_change=True))
        self.assertFalse(r['snapshot_query_completed'])
        self.assertEqual(r['error_category'], 'owner_changed')
        self.assertEqual(r['runtime_status'], 'unknown')

    def test_oversize_header_is_recorded_without_reading_body(self):
        p = Pipe(oversize=True)
        r = self.measure(p)
        self.assertFalse(r['snapshot_query_completed'])
        self.assertEqual(r['error_category'], 'single_frame_limit')
        self.assertEqual(r['measurements']['max_declared_body_bytes'], sm.FRAME_CAP + 1)
        self.assertNotIn(sm.FRAME_CAP + 1, p.read_sizes)

    def test_cumulative_limit_includes_noise_and_precedes_body_read(self):
        p = Pipe(noise=2)
        c = sm.SnapshotMeter(p, verified(p), 'private-thread')
        baseline = c.metrics['read_budget_debited_bytes']
        c.rx_cap = baseline + 4
        read_count = len(p.read_sizes)
        with self.assertRaisesRegex(sm.ProbeFailure, 'cumulative_receive_limit'):
            c.owner('private-thread')
        self.assertEqual(p.read_sizes[read_count:], [4])
        self.assertEqual(c.metrics['read_budget_debited_bytes'], baseline + 4)

    def test_all_requests_share_deadline_and_noise_cannot_extend_it(self):
        now = [0.0]
        p = Pipe(tick=lambda: now.__setitem__(0, now[0] + .2))
        with mock.patch.object(sm.time, 'monotonic', side_effect=lambda: now[0]):
            c = sm.SnapshotMeter(p, verified(p), 'private-thread', seconds=1)
            p.noise = 20
            with self.assertRaises(TimeoutError):
                c.owner('private-thread')
            with self.assertRaises(TimeoutError):
                c.write_frame({'type': 'broadcast', 'method': sm.FOLLOW,
                               'params': {'conversationId': 'private-thread', 'following': False}}, 100)
        self.assertTrue(all(d <= 1 for d in p.deadlines))
        self.assertLessEqual(now[0], 1.2)

    def test_model_request_and_other_target_never_reach_pipe(self):
        p = Pipe()
        c = sm.SnapshotMeter(p, verified(p), 'private-thread')
        count = len(p.sent)
        with self.assertRaisesRegex(sm.ProbeFailure, 'method_not_allowed'):
            c.request('thread-follower-start-turn', {})
        with self.assertRaisesRegex(sm.ProbeFailure, 'wrong_request_target'):
            c.owner('different-thread')
        self.assertEqual(len(p.sent), count)

    def test_partial_read_is_not_claimed_as_exact_wire_total(self):
        p = Pipe(fail_read=True)
        r = self.measure(p)
        m = r['measurements']
        self.assertTrue(m['incomplete_io'])
        self.assertEqual(m['completed_read_bytes'], 4)
        self.assertGreater(m['read_budget_debited_bytes'], 4)
        self.assertNotIn('DO_NOT_EXPORT', json.dumps(r))
        self.assertTrue(p.closed)

    def test_verification_failure_prevents_protocol_io_and_redacts_error(self):
        p = Pipe()
        def fail(_):
            raise ValueError('DO_NOT_EXPORT_PRIVATE_PATH')
        r = sm.measure_snapshot(p, 'private-thread', WORK_CWD, verifier=fail)
        self.assertFalse(r['snapshot_query_completed'])
        self.assertEqual(p.sent, [])
        self.assertNotIn('DO_NOT_EXPORT', json.dumps(r))
        self.assertTrue(p.closed)

    def test_other_installation_never_sends_initialize(self):
        p = Pipe()
        r = sm.measure_snapshot(p, 'private-thread', WORK_CWD, verifier=lambda _: {'archive_sha256': 'other'})
        self.assertEqual(r['error_category'], 'installation_changed')
        self.assertEqual(p.sent, [])

    def test_budgets_cannot_expand_production_frame_cap(self):
        for kwargs in ({'frame_cap': sm.FRAME_CAP + 1}, {'rx_cap': sm.RX_CAP + 1},
                       {'seconds': 11}, {'seconds': float('nan')}, {'frame_cap': True}):
            p = Pipe()
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                sm.SnapshotMeter(p, verified(p), 'private-thread', **kwargs)
            self.assertEqual(p.sent, [])

    def test_cleanup_failure_does_not_claim_valid_sample(self):
        p = Pipe()
        p.close = mock.Mock(side_effect=OSError('DO_NOT_EXPORT_CLOSE'))
        r = self.measure(p)
        self.assertTrue(r['cleanup_failed'])
        self.assertFalse(r['snapshot_query_completed'])
        self.assertFalse(r['can_send'])
        self.assertNotIn('DO_NOT_EXPORT', json.dumps(r))


if __name__ == '__main__':
    unittest.main()
