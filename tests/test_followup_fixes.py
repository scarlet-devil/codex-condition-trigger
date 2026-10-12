"""Failure-path regressions for progress, native outcomes and upload recovery."""
import base64
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import threading
import time
import unittest
from unittest import mock

import delivery_outbox as outbox
from execution_result import batch_status, record_outcome
from test_trigger import Fixture
from test_desktop_ipc import DesktopDispatchTests
import trigger as tr
import trial_worker
from worker_health import Progress, read_health


class HealthTests(Fixture):
    def test_stale_progress_and_clock_rollback_never_claim_alive(self):
        Progress(self.store, False)
        health = read_health(self.store.path, now=time.time() + 31)
        self.assertEqual(health['freshness'], 'stale')
        self.assertTrue(health['attention_required'])
        self.assertEqual(health['process_liveness'], 'not_proven')
        self.assertEqual(read_health(self.store.path, now=0)['freshness'], 'clock_uncertain')

    def test_real_loop_records_progress_and_stop_reason(self):
        stop = threading.Event()
        def scan(scanner, now):
            self.assertEqual(read_health(self.store.path)['phase'], 'scanning')
            stop.set()
        with mock.patch.object(tr.StableScanner, 'scan', scan):
            tr.run(self.store, stop_event=stop)
        value = read_health(self.store.path)
        self.assertEqual(value['state'], 'stopped')
        self.assertEqual(value['reason'], 'stop_event')
        self.assertIn('last_scan_at_utc', value)

    def test_unexpected_cycle_failure_leaves_failed_health(self):
        with mock.patch('owner_loading.cycle_tick', side_effect=RuntimeError('synthetic')):
            with self.assertRaises(RuntimeError):
                tr.run(self.store, live=True)
        health = read_health(self.store.path)
        self.assertEqual((health['state'], health['reason']), ('failed', 'RuntimeError'))

    def config_file(self):
        self.config['trial_expires_at_utc'] = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
        path = self.root / 'config.json'
        path.write_text(json.dumps(self.config))
        return path

    def test_duplicate_launcher_cannot_replace_current_worker_receipt(self):
        path = self.config_file()
        receipt = self.store.path / 'latest-worker.json'
        receipt.write_text('{"active_run":"preserve"}')
        before = receipt.read_bytes()
        self.assertEqual(trial_worker.run_worker(path, live=False), 0)
        self.assertEqual(receipt.read_bytes(), before)

    def test_worker_exit_replaces_startup_snapshot(self):
        path = self.config_file()
        self.store.close(); self.store.lock = None
        with mock.patch.object(tr, 'run', side_effect=OSError('synthetic')):
            self.assertEqual(trial_worker.run_worker(path, live=False), 1)
        receipt = json.loads((self.root / 'state/latest-worker.json').read_text())
        self.assertEqual((receipt['state'], receipt['exit_code']), ('failed', 1))
        self.assertIn('stopped_at_utc', receipt)

    def test_keyboard_stop_is_recorded_without_restarting_worker(self):
        path = self.config_file()
        self.store.close(); self.store.lock = None
        with mock.patch.object(tr, 'run', side_effect=KeyboardInterrupt) as run:
            self.assertEqual(trial_worker.run_bounded(path, live=False, retry_seconds=0), 130)
        self.assertEqual(run.call_count, 1)
        receipt = json.loads((self.root / 'state/latest-worker.json').read_text())
        self.assertEqual(receipt['state'], 'interrupted')


class OutcomeTests(DesktopDispatchTests):
    def evidence(self, **extra):
        row = self.store.rows()[0]
        value = dict(schema=1, batch_id=row['id'], turn_id=row['turn_id'],
                     manifest_sha256=tr.digest((row['manifest'] + '\n').encode()),
                     source='caller_verified_native_turn', native_turn_status='failed',
                     native_runtime_status='systemError')
        value.update(extra)
        path = self.root / 'native-outcome.json'
        path.write_text(json.dumps(value))
        return path

    def ended(self):
        self.ready(); self.dispatch()
        self.append('event_msg', type='task_complete', turn_id='native')
        self.assertEqual(self.dispatch(), 'ended')
        return self.store.rows()[0]

    def test_end_event_is_unknown_until_exact_native_failure_receipt(self):
        row = self.ended()
        view = batch_status(row)
        self.assertEqual((view['lifecycle'], view['execution_outcome'], view['business_delivery']),
                         ('ended', 'unknown', 'unverified'))
        record_outcome(self.store, row['id'], self.evidence())
        self.reopen()
        self.assertEqual(self.dispatch(), 'failed')
        self.assertEqual(self.store.rows()[0]['execution_outcome'], 'failed')
        self.assertEqual(len(self.sent), 1)

    def test_stale_receipt_cannot_erase_explicit_failure_or_release_as_materials(self):
        row = self.ended()
        record_outcome(self.store, row['id'], self.evidence())
        self.assertFalse(self.store.update(row['id'], 'running', execution_outcome='unknown'))
        self.assertEqual(self.store.rows()[0]['state'], 'failed')

    def test_mismatched_turn_or_contradictory_native_receipt_rejected(self):
        row = self.ended()
        for extra in ({'turn_id': 'other'}, {'native_turn_status': 'completed'}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                record_outcome(self.store, row['id'], self.evidence(**extra))
        self.assertEqual(self.store.rows()[0]['execution_outcome'], 'unknown')

    def test_failure_event_and_abort_keep_distinct_outcomes(self):
        self.ready(); self.dispatch()
        self.append('event_msg', type='turn_aborted', turn_id='native')
        self.assertEqual(self.dispatch(), 'failed')
        self.assertEqual(self.store.rows()[0]['execution_outcome'], 'interrupted')

    def test_old_completed_stays_unknown_and_delivery_ack_unchanged(self):
        row = self.ended()
        self.store.update(row['id'], 'completed')
        self.reopen()
        self.assertEqual(batch_status(self.store.rows()[0])['execution_outcome'], 'unknown')
        receipt = self.root / 'receipt'; receipt.write_text('verified delivery')
        self.store.acknowledge(row['id'], receipt)
        before = self.store.rows()[0]
        with self.assertRaises(ValueError):
            record_outcome(self.store, row['id'], self.evidence())
        self.assertEqual(self.store.rows()[0], before)


class UploadDriver:
    def __init__(self):
        self.remote, self.calls = {}, []
        self.lose_reply_name = None
        self.wrong_parent = False
        self.unknown = False

    def __call__(self, request):
        action, key = request['action'], request['key']
        self.calls.append((action, key))
        result = dict(schema=1, key=key)
        if action == 'lookup':
            if self.unknown:
                return dict(result, status='unknown')
            if key not in self.remote:
                return dict(result, status='absent', safe_to_create=True)
            return dict(result, status='found', file_id=key)
        if action == 'upload':
            self.remote[key] = Path(request['path']).read_bytes()
            if request['name'] == self.lose_reply_name:
                raise TimeoutError('remote succeeded but response lost')
            return dict(result, status='found', file_id=key)
        if action == 'readback':
            return dict(result, status='found', file_id=key,
                        parent_id='wrong' if self.wrong_parent else request['parent_id'],
                        name=request['name'], content_base64=base64.b64encode(self.remote[key]).decode())
        raise AssertionError(action)


class OutboxTests(Fixture):
    def test_freeze_in_nested_state_directory_with_legacy_windows_path_limit(self):
        # Reproduce the observed MAX_PATH failure on every platform. Only the
        # filesystem boundary is limited; freezing and reconciliation are real.
        padding = max(16, 140 - len(str(self.root)) - 1)
        self.config['state_dir'] = str(self.root / ('s' * padding))
        self.reopen()
        write = tr.atomic_write
        def bounded_write(path, data):
            self.assertLess(len(str(path.with_name(path.name + '.tmp'))), 260,
                            'freezing needlessly exceeds the legacy Windows path limit')
            return write(path, data)
        with mock.patch.object(tr, 'atomic_write', bounded_write):
            _, paths, job = self.make_job()
        frozen = outbox.jobs(self.store)[0]
        self.assertEqual({Path(a['path']).read_bytes() for a in frozen['artifacts']},
                         {p.read_bytes() for p in paths})
        self.assertEqual(outbox.resume(self.store, job, UploadDriver())['state'],
                         'uploaded_verified')

    def test_existing_frozen_blob_paths_remain_resumable(self):
        _, _, job_id = self.make_job()
        job = outbox.jobs(self.store)[0]
        for i, item in enumerate(job['artifacts']):
            legacy = self.root / (str(i) + '-' + item['sha256'] + '.blob')
            Path(item['path']).rename(legacy)
            item['path'] = str(legacy)
        outbox.save(self.store, job)
        self.reopen()
        self.assertEqual(outbox.resume(self.store, job_id, UploadDriver())['state'],
                         'uploaded_verified')

    def make_job(self):
        batch = self.ready()
        self.store.update(batch, 'ended', turn_id='native')
        paths = [self.root / name for name in ('report.md', 'proof.zip')]
        for p in paths:
            p.write_bytes(('frozen ' + p.name).encode())
        return batch, paths, outbox.stage(self.store, batch, 'exact-parent', paths)

    def test_response_loss_restart_reconciles_without_duplicate_or_model_or_ack(self):
        batch, paths, job = self.make_job()
        driver = UploadDriver(); driver.lose_reply_name = 'report.md'
        first = outbox.resume(self.store, job, driver)
        self.assertEqual(first['state'], 'upload_uncertain')
        self.assertEqual(sum(x['state'] == 'uploaded_verified' for x in first['artifacts']), 1)
        self.reopen()
        for p in paths:
            p.write_bytes(b'later source edits must not replace frozen artifact')
        # An explicit upload-only completion is allowed after stopping the
        # model watcher. STOP itself must remain set and there is no model call.
        (self.store.path / 'STOP').touch()
        with mock.patch.object(tr, 'make_adapter', side_effect=AssertionError('model replay')):
            result = outbox.resume(self.store, job, driver)
        self.assertEqual(result['state'], 'uploaded_verified')
        self.assertEqual(sum(a == 'upload' for a, _ in driver.calls), 2)
        self.assertEqual(self.store.rows()[0]['state'], 'ended')
        self.assertTrue((self.store.path / 'STOP').exists())
        before = list(driver.calls)
        outbox.resume(self.store, job, driver)
        self.assertEqual(driver.calls, before)

    def test_frozen_tampering_blocks_all_network_actions(self):
        _, _, job = self.make_job()
        item = outbox.jobs(self.store)[0]['artifacts'][0]
        Path(item['path']).write_bytes(b'tampered')
        driver = UploadDriver()
        with self.assertRaises(ValueError): outbox.resume(self.store, job, driver)
        self.assertEqual(driver.calls, [])

    def test_unknown_lookup_never_retries_creation(self):
        _, _, job = self.make_job()
        driver = UploadDriver(); driver.unknown = True
        self.assertEqual(outbox.resume(self.store, job, driver)['state'], 'upload_uncertain')
        self.assertEqual([a for a, _ in driver.calls], ['lookup'])

    def test_wrong_remote_parent_and_bytes_never_verify_delivery(self):
        _, _, job = self.make_job()
        driver = UploadDriver(); driver.wrong_parent = True
        self.assertEqual(outbox.resume(self.store, job, driver)['state'], 'upload_uncertain')
        driver.wrong_parent = False
        driver.remote[next(iter(driver.remote))] = b'incorrect remote bytes'
        self.assertEqual(outbox.resume(self.store, job, driver)['state'], 'upload_uncertain')
        self.assertEqual(sum(a == 'upload' for a, _ in driver.calls), 1)
        self.assertEqual(self.store.rows()[0]['state'], 'ended')

    def test_stage_deduplicates_order_and_never_modifies_business_ledger(self):
        batch, paths, job = self.make_job()
        before = self.store.rows()[0]
        self.assertEqual(outbox.stage(self.store, batch, 'exact-parent', list(reversed(paths))), job)
        self.assertEqual(len(outbox.jobs(self.store)), 1)
        self.assertEqual(self.store.rows()[0], before)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(cls(name) for cls in (HealthTests, OutcomeTests, OutboxTests)
                              for name in cls.__dict__ if name.startswith('test_'))
