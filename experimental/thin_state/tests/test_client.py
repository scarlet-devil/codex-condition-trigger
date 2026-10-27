import json
import struct
import unittest

from thin_client import query_status


def frame(obj):
    data = json.dumps(obj).encode()
    return struct.pack('<I', len(data)) + data


class Pipe:
    def __init__(self, status='idle'):
        self.data = b''
        self.writes = []
        self.reads = []
        self.status = status
        self.mutate = lambda response: response
        self.prefix = b''
        self.closed = False

    def write(self, data, deadline):
        item = json.loads(data[4:])
        self.writes.append(item)
        result = {'clientId': 'synthetic-client'} if item['method'] == 'initialize' else {
            'schema': 1, 'hostId': 'local', 'threadId': 'synthetic-thread',
            'cwd': 'C:\\fixture', 'status': self.status, 'connectionGeneration': 7}
        response = {'type': 'response', 'requestId': item['requestId'], 'method': item['method'],
                    'handledByClientId': 'synthetic-owner', 'resultType': 'success', 'result': result}
        self.data += self.prefix + frame(self.mutate(response))

    def read(self, size, deadline):
        self.reads.append(size)
        if len(self.data) < size:
            raise EOFError()
        result, self.data = self.data[:size], self.data[size:]
        return result

    def close(self):
        self.closed = True


class ClientTests(unittest.TestCase):
    def query(self, pipe, **kwargs):
        return query_status(pipe, thread_id='synthetic-thread', owner_id='synthetic-owner',
                            expected_cwd='C:\\fixture', enabled=True, **kwargs)

    def test_disabled_sends_nothing(self):
        p = Pipe()
        with self.assertRaises(ValueError):
            query_status(p, thread_id='synthetic-thread', owner_id='synthetic-owner', expected_cwd='C:\\fixture')
        self.assertEqual(p.writes, [])

    def test_statuses_and_only_two_requests(self):
        for status, expected in [('idle', 'idle'), ('active', 'busy'), ('notLoaded', 'waiting_connection'),
                                 ('systemError', 'unknown')]:
            p = Pipe(status)
            r = self.query(p)
            self.assertEqual(r['observation'], expected)
            self.assertFalse(r['can_send'])
            self.assertEqual([q['method'] for q in p.writes], ['initialize', 'thread-follower-read-thread-status'])
            self.assertNotIn('hostId', p.writes[-1])
            self.assertTrue(p.closed)

    def test_wrong_binding_missing_status_settings_and_generation(self):
        changes = [('threadId', 'other'), ('cwd', 'C:\\other'), ('hostId', 'remote'),
                   ('status', None), ('connectionGeneration', -1), ('connectionGeneration', True)]
        for key, value in changes:
            p = Pipe()
            def mutate(r, key=key, value=value):
                if r['method'] != 'initialize':
                    r['result'][key] = value
                return r
            p.mutate = mutate
            with self.assertRaises(ValueError):
                self.query(p)
            self.assertTrue(p.closed)

    def test_wrong_owner_and_method(self):
        for key in ['handledByClientId', 'method']:
            p = Pipe()
            p.mutate = lambda r, key=key: dict(r, **{key: 'wrong'})
            with self.assertRaises(ValueError):
                self.query(p)

    def test_oversize_body_never_read(self):
        p = Pipe()
        p.prefix = struct.pack('<I', 65537)
        with self.assertRaises(ValueError):
            self.query(p)
        self.assertEqual(p.reads, [4])

    def test_unrelated_flood_has_cumulative_bound(self):
        p = Pipe()
        p.prefix = frame({'type': 'broadcast', 'padding': 'x' * 60000}) * 20
        with self.assertRaises(ValueError):
            self.query(p)
        self.assertLessEqual(sum(p.reads), 1048576)

    def test_wrong_request_id_never_accepted(self):
        p = Pipe()
        p.mutate = lambda r: dict(r, requestId='wrong')
        with self.assertRaises(EOFError):
            self.query(p)

    def test_truncated_frame(self):
        p = Pipe()
        p.prefix = struct.pack('<I', 10000)
        with self.assertRaises(EOFError):
            self.query(p)

    def test_unknown_method_no_legacy_fallback(self):
        p = Pipe()
        def mutate(r):
            if r['method'] != 'initialize':
                return dict(r, resultType='error', error='unsupported-method')
            return r
        p.mutate = mutate
        with self.assertRaises(ValueError):
            self.query(p)
        self.assertEqual(len(p.writes), 2)

    def test_one_shared_deadline_including_initialize(self):
        p = Pipe()
        tick = [0.0]
        def clock():
            tick[0] += 1.0
            return tick[0]
        with self.assertRaises(TimeoutError):
            self.query(p, clock=clock)
        self.assertLessEqual(len(p.writes), 2)
        self.assertTrue(p.closed)

    def test_settings_only_never_runtime(self):
        p = Pipe()
        def mutate(r):
            if r['method'] != 'initialize':
                r['result'] = {'settings': {'model': 'synthetic'}}
            return r
        p.mutate = mutate
        with self.assertRaises(ValueError):
            self.query(p)


if __name__ == '__main__':
    unittest.main()
