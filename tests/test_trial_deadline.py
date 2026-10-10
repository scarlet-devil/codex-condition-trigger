"""Fixed trial deadline contracts, synthetic files/adapters only."""
import json
import time
import threading
import unittest
from unittest import mock
from test_trigger import Fixture
from test_desktop_ipc import DesktopDispatchTests
import trigger as tr

CUTOFF = 1893456000.0
STAMP = '2030-01-01T00:00:00Z'

class DeadlineTests(Fixture):
    def bind(self):
        self.config['trial_expires_at_utc'] = STAMP
        self.reopen()

    def test_valid_before_deadline_expired_work_persists_stop_without_send(self):
        with mock.patch('time.time', return_value=CUTOFF-10):
            self.bind(); self.ready()
            self.assertFalse(self.store.paused())
        before=self.store.rows()
        with mock.patch('time.time', return_value=CUTOFF):
            self.assertEqual(tr.dispatch_one(self.store, adapter_factory=lambda *a:self.fail('no adapter')), 'paused')
            self.assertTrue((self.store.path/'STOP').exists())
            self.assertTrue((self.store.path/'TRIAL_EXPIRED.json').exists())
        self.assertEqual(self.store.rows(),before)

    def test_expired_restart_cannot_resume_even_if_stop_removed(self):
        with mock.patch('time.time',return_value=CUTOFF-1): self.bind()
        with mock.patch('time.time',return_value=CUTOFF+1):
            self.assertTrue(self.store.paused())
            (self.store.path/'STOP').unlink()
            self.reopen()
            self.assertTrue(self.store.paused())
            self.assertIsNone(self.ready())

    def test_deadline_cannot_be_removed_or_extended_on_restart(self):
        self.bind();self.store.close()
        for value in (None,'2030-01-02T00:00:00Z'):
            with self.subTest(value=value):
                c=dict(self.config)
                if value is None:c.pop('trial_expires_at_utc')
                else:c['trial_expires_at_utc']=value
                with self.assertRaisesRegex(ValueError,'deadline'):
                    candidate=tr.Store(c)
                    candidate.close()

    def test_clock_rollback_does_not_extend_current_process_budget(self):
        with mock.patch('time.time',return_value=CUTOFF-10),mock.patch('time.monotonic',return_value=100): self.bind()
        with mock.patch('time.time',return_value=CUTOFF-100),mock.patch('time.monotonic',return_value=111):
            self.assertTrue(self.store.paused())

    def test_recorded_expiry_stays_expired_after_restart_and_clock_rollback(self):
        with mock.patch('time.time',return_value=CUTOFF+1):
            self.bind();self.assertTrue(self.store.paused())
        (self.store.path/'STOP').unlink()
        with mock.patch('time.time',return_value=CUTOFF-100):
            self.reopen();self.assertTrue(self.store.paused())

    def test_invalid_or_naive_deadline_rejected(self):
        for value in ('tomorrow','2030-01-01T00:00:00',42):
            with self.subTest(value=value):
                config=dict(self.config,trial_expires_at_utc=value)
                p=self.root/'config.json';p.write_text(json.dumps(config))
                with self.assertRaises(ValueError):tr.load_config(p)

    def test_expired_run_never_starts_observer(self):
        with mock.patch('time.time',return_value=CUTOFF+1):
            self.bind()
            stop=threading.Event();stop.set()
            with mock.patch('watchdog.observers.Observer') as observer:
                tr.run(self.store,live=True,stop_event=stop)
            observer.assert_not_called()

    def test_expiry_during_capture_does_not_commit_batch(self):
        now=[CUTOFF-1]
        with mock.patch('time.time',side_effect=lambda:now[0]):
            self.bind();(self.input/'one.md').write_text('real file bytes')
            files=tr.snapshot(self.config)
            original=tr.atomic_write
            def write_and_expire(path,data):
                original(path,data);now[0]=CUTOFF
            with mock.patch.object(tr,'atomic_write',write_and_expire):
                self.assertIsNone(self.store.plan(files))
            self.assertEqual(self.store.rows(),[])

    def test_expired_unpause_cannot_remove_stop(self):
        self.config['trial_expires_at_utc']='2000-01-01T00:00:00Z'
        p=self.root/'config.json';p.write_text(json.dumps(self.config))
        stop=self.store.path/'STOP';stop.touch()
        with mock.patch('sys.argv',['trigger','--config',str(p),'unpause']):
            with self.assertRaisesRegex(ValueError,'expired'):tr.main()
        self.assertTrue(stop.exists())

class DeadlineSendTests(DesktopDispatchTests):
    def test_final_request_retains_original_budget_after_wall_clock_rollback(self):
        self.config['trial_expires_at_utc']=STAMP
        with mock.patch('time.time',return_value=CUTOFF-10),mock.patch('time.monotonic',return_value=100):
            self.reopen();self.ready()
        with mock.patch('time.time',return_value=CUTOFF-100),mock.patch('time.monotonic',return_value=109.5):
            self.assertEqual(self.dispatch(),'accepted')
            self.assertEqual(self.sent[0][2]['deadline'],110)
            self.assertTrue(callable(self.sent[0][2]['before_write']))

    def test_final_start_request_deadline_cannot_exceed_trial(self):
        self.config['trial_expires_at_utc']=STAMP
        with mock.patch('time.time',return_value=CUTOFF-.25):
            self.reopen();self.ready()
            before=time.monotonic()
            self.assertEqual(self.dispatch(),'accepted')
            limit=self.sent[0][2].get('deadline')
            self.assertIsNotNone(limit)
            self.assertLessEqual(limit,time.monotonic()+.25)
            self.assertGreater(limit,before)

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(cls(name) for cls in (DeadlineTests,DeadlineSendTests)
        for name in cls.__dict__ if name.startswith('test_'))
