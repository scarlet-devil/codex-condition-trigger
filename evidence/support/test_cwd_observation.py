import unittest
import desktop_ipc as ipc
from experimental import snapshot_measure as sm
from experimental.tests.test_snapshot_diagnostics import ChangedPipe, snapshot_change, verified
from cwd_observation import cwd_values


class ObservationTests(unittest.TestCase):
    def test_cwd_rejection_projects_only_two_paths(self):
        captured = []
        original = sm.failure_reason
        def observe(error):
            captured.append(cwd_values(error, ipc.IPCClient.current_state.__code__))
            return original(error)
        sm.failure_reason = observe
        try:
            result = sm.measure_snapshot(ChangedPipe(snapshot_change('cwd', '/different')),
                'private-thread', '/private-work', verifier=verified)
        finally:
            sm.failure_reason = original
        self.assertEqual(result['error_reason'], 'snapshot_cwd_mismatch')
        self.assertEqual(captured, [{'expected_cwd':'/private-work','native_cwd':'/different'}])

    def test_non_cwd_error_is_not_projected(self):
        captured = []
        original = sm.failure_reason
        def observe(error):
            captured.append(cwd_values(error, ipc.IPCClient.current_state.__code__))
            return original(error)
        sm.failure_reason = observe
        try:
            result = sm.measure_snapshot(ChangedPipe(snapshot_change('id', 'wrong')),
                'private-thread', '/private-work', verifier=verified)
        finally:
            sm.failure_reason = original
        self.assertEqual(result['error_reason'],'snapshot_thread_mismatch')
        self.assertEqual(captured,[None])

    def test_unrelated_exception_text_cannot_trigger_projection(self):
        self.assertIsNone(cwd_values(ValueError('snapshot_cwd_mismatch'), ipc.IPCClient.current_state.__code__))


if __name__=='__main__':
    unittest.main()
