"""Real child restarts against synthetic files; never native IPC."""
import importlib.util
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest import mock
from datetime import datetime, timezone, timedelta

from test_trigger import Fixture


class RecoveryWorkerTests(Fixture):
    def test_entry_retry_preserves_original_monotonic_budget(self):
        import trial_worker as worker
        cfg = self.config_file(30)
        config = json.loads(cfg.read_text())
        config['trial_expires_at_utc'] = datetime.fromtimestamp(1010, timezone.utc).isoformat()
        cfg.write_text(json.dumps(config))
        clock = {'utc': 1000.0, 'mono': 100.0}
        deadlines = []

        def execute(store, live=True):
            deadlines.append(store.monotonic_deadline)
            if len(deadlines) == 1:
                clock.update(utc=900.0, mono=101.0)
                raise OSError('synthetic worker failure and UTC rollback')
            clock['mono'] = 111.0
            self.assertTrue(store.paused())
            self.assertTrue((store.path / 'TRIAL_EXPIRED.json').exists())

        with mock.patch.object(worker.time, 'time', side_effect=lambda: clock['utc']), \
                mock.patch.object(worker.time, 'monotonic', side_effect=lambda: clock['mono']), \
                mock.patch.object(worker.trigger, 'run', side_effect=execute):
            self.assertEqual(worker.run_bounded(cfg, live=False, retry_seconds=0), 0)
        self.assertEqual(deadlines, [110.0, 110.0])

    def test_entry_retries_errors_but_not_normal_stop(self):
        import trial_worker as worker
        self.assertTrue(callable(getattr(worker, 'run_bounded', None)),
                        'entry has no verified retry path when OS retry is unavailable')
        cfg = self.config_file(30)
        with mock.patch.object(worker, 'run_worker', side_effect=[1, 0]) as call:
            self.assertEqual(worker.run_bounded(cfg, live=False, retry_seconds=.01), 0)
            self.assertEqual(call.call_count, 2)

    def test_entry_bounds_retries_and_stop_prevents_retry(self):
        import trial_worker as worker
        self.assertTrue(callable(getattr(worker, 'run_bounded', None)))
        cfg = self.config_file(30)
        with mock.patch.object(worker, 'run_worker', return_value=1) as call:
            self.assertEqual(worker.run_bounded(cfg, live=False, retry_seconds=.01), 1)
            self.assertEqual(call.call_count, 4)
        def failure_then_stop(*args, **kwargs):
            (self.root / 'state/STOP').touch()
            return 1
        with mock.patch.object(worker, 'run_worker', side_effect=failure_then_stop) as call:
            self.assertEqual(worker.run_bounded(cfg, live=False, retry_seconds=.01), 0)
            self.assertEqual(call.call_count, 1)

    def worker(self):
        path = Path(__file__).parents[1] / 'trial_worker.py'
        self.assertTrue(path.exists(), 'no restartable bounded worker entry point')
        return path

    def config_file(self, seconds=4):
        self.config['trial_expires_at_utc'] = (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()
        p = self.root / 'config.json'; p.write_text(json.dumps(self.config))
        self.store.close()
        # tearDown may safely close a closed SQLite handle.
        self.store.lock = None
        return p

    def invoke(self, cfg):
        return subprocess.Popen([sys.executable, '-B', str(self.worker()), '--config', str(cfg), '--dry'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def wait_record(self, process, test):
        limit = time.monotonic() + 5
        while time.monotonic() < limit:
            records = list((self.root / 'state' / 'worker-runs').glob('*/start.json'))
            if records and test(records): return records
            if process.poll() is not None: break
            time.sleep(.05)
        self.fail('worker did not record expected startup')

    def test_fixed_expiry_exits_and_records_without_renewal(self):
        cfg = self.config_file(2)
        p = self.invoke(cfg)
        out, err = p.communicate(timeout=8)
        self.assertEqual(p.returncode, 0, err)
        self.assertTrue((self.root / 'state/TRIAL_EXPIRED.json').exists())
        p2 = self.invoke(cfg); p2.communicate(timeout=5)
        self.assertEqual(p2.returncode, 0)
        self.assertTrue((self.root / 'state/STOP').exists())

    def test_forced_exit_then_new_process_retains_state_and_history(self):
        batch = self.ready(b'pre-restart content')
        cfg = self.config_file(30)
        p = self.invoke(cfg)
        try:
            self.wait_record(p, lambda r: len(r) == 1)
            p.kill(); p.communicate(timeout=5)
            p2 = self.invoke(cfg)
            try:
                records = self.wait_record(p2, lambda r: len(r) == 2)
                (self.root / 'state/STOP').touch()
                p2.communicate(timeout=5)
                self.assertEqual(p2.returncode, 0)
                self.assertEqual(len(records), 2)
                import sqlite3
                with contextlib.closing(sqlite3.connect(self.root / 'state/state.sqlite')) as db:
                    self.assertEqual(db.execute('SELECT id FROM batches').fetchall(), [(batch,)])
                self.assertEqual(len(list((self.root / 'state/worker-runs').glob('*/exit.json'))), 1)
            finally:
                if p2.poll() is None: p2.kill(); p2.communicate()
        finally:
            if p.poll() is None: p.kill(); p.communicate()

    def test_duplicate_launcher_exits_without_disturbing_first(self):
        cfg = self.config_file(30)
        p = self.invoke(cfg)
        try:
            self.wait_record(p, lambda r: len(r) == 1)
            duplicate = self.invoke(cfg); duplicate.communicate(timeout=5)
            self.assertEqual(duplicate.returncode, 0)
            self.assertIsNone(p.poll())
            exits = list((self.root / 'state/worker-runs').glob('*/exit.json'))
            self.assertEqual(json.loads(exits[0].read_bytes())['result'], 'already_running')
            (self.root / 'state/STOP').touch()
            p.communicate(timeout=5)
        finally:
            if p.poll() is None: p.kill(); p.communicate()
