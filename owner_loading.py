"""Default-off, single-worker window lifecycle, separate from delivery state.

Only explicit owner absence permits an open. An unconfirmed external action
survives restart and blocks the next cycle. No business ACK is generated here.
"""
import json
import subprocess
import time
from pathlib import Path

from desktop_ipc import DesktopAdapter


class CommandBackend:
    """Bounded JSON stdin/stdout protocol; argv execution, never shell expansion.

    inspect/close must revalidate the complete lease and main-window invariant.
    'absent' means this owned window is gone AND the main window is unchanged.
    A timeout is an unknown action, never permission to replay it.
    """
    def __init__(self, config):
        self.config = config

    def call(self, action, **values):
        c = self.config
        request = dict(action=action, thread_id=c['thread_id'],
                       expected_cwd=c['expected_cwd'],
                       stop_file=str(Path(c['state_dir']) / 'STOP'),
                       options=c.get('window_backend_options', {}), **values)
        result = subprocess.run(c['window_backend_command'],
            input=json.dumps(request, ensure_ascii=False).encode('utf-8'), capture_output=True,
            timeout=c.get('window_timeout_seconds', 30),
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), check=True)
        value = json.loads(result.stdout.decode('utf-8-sig'))
        if not isinstance(value, dict) or value.get('error'):
            raise ValueError('window backend failed')
        return value

    def open(self, **values):
        return self.call('open')['lease']

    def inspect(self, lease):
        return self.call('inspect', lease=lease)

    def close(self, lease):
        return self.call('close', lease=lease)


class WindowCycles:
    def __init__(self, store, backend=None, adapter_factory=None):
        if not store.lock:
            raise ValueError('window lifecycle requires the Store worker lock')
        self.store = store
        self.batch_id = None
        self.backend = backend
        if backend is None and store.c.get('window_backend_command'):
            self.backend = CommandBackend(store.c)
        self.adapter_factory = adapter_factory or (lambda c, paused: DesktopAdapter(c, paused))

    def records(self):
        return [json.loads(r[0]) for r in self.store.db.execute(
            "SELECT v FROM meta WHERE k LIKE 'window_cycle:%' ORDER BY k")]

    def save(self, cycle, phase, reason, **values):
        cycle.update(values, phase=phase)
        cycle.setdefault('events', []).append(dict(at=time.time(), phase=phase, reason=reason))
        with self.store.db:
            self.store.db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)',
                ('window_cycle:' + cycle['batch_id'], json.dumps(cycle)))

    def inspect_owner(self, row):
        adapter = self.adapter_factory(self.store.c, self.store.paused)
        try:
            # Force a fresh native check instead of delivered-row short circuit.
            return adapter.inspect(dict(row, state='ready'))
        finally:
            adapter.close()

    def completion(self, row):
        adapter = self.adapter_factory(self.store.c, self.store.paused)
        try:
            receipt = adapter.observe(row)
            return bool(row.get('turn_id') and receipt and receipt['state'] == 'completed'
                        and receipt.get('turn_id') == row['turn_id'])
        finally:
            adapter.close()

    def claim_open(self, row):
        """Claim before action; also usable by an explicitly supervised probe.

        Scheduling calls only after fresh explicit absence. No model turn is
        sent here, and a direct probe must not be presented as cold recovery.
        """
        if self.store.paused():
            return 'paused'
        if not self.store.c.get('owner_loading_enabled') or not self.store.c['owner_verified'] or self.store.c.get('chat_adapter') != 'desktop_ipc':
            return 'owner_not_verified'
        if self.store.db.execute('SELECT 1 FROM meta WHERE k=?',
                ('owner_load_attempt:' + self.store.c['thread_id'],)).fetchone():
            return 'legacy_reconciliation_required'
        if self.backend is None:
            return 'loader_unavailable'
        active = [x for x in self.records() if x['phase'] != 'closed']
        if active:
            cycle = active[0]
            # Reuse spent no window action. Preserve its history and promote
            # only this exact never-opened cycle, never an uncertain action.
            if (len(active) != 1 or cycle['batch_id'] != row['id']
                    or cycle['phase'] != 'reused' or cycle.get('lease') is not None
                    or not cycle.get('events')
                    or any(e.get('phase') != 'reused'
                           or e.get('reason') != 'fresh_idle_owner_reused'
                           for e in cycle['events'])):
                return 'window_reconciliation_required'
            previous = json.dumps(cycle)
            cycle = dict(cycle, phase='opening')
        else:
            cycle = dict(batch_id=row['id'], phase='opening', lease=None, events=[])
        with self.store.db:
            if active:
                claimed = self.store.db.execute("UPDATE meta SET v=? WHERE k=? AND v=? "
                    "AND EXISTS (SELECT 1 FROM batches WHERE id=? AND state='ready' "
                    "AND dispatch_text IS NULL AND dispatch_meta IS NULL)",
                    (json.dumps(cycle), 'window_cycle:' + row['id'], previous, row['id']))
            else:
                claimed = self.store.db.execute("INSERT OR IGNORE INTO meta(k,v) "
                    "SELECT ?,? WHERE EXISTS (SELECT 1 FROM batches WHERE id=? AND state='ready' "
                    "AND dispatch_text IS NULL AND dispatch_meta IS NULL)",
                    ('window_cycle:' + row['id'], json.dumps(cycle), row['id']))
        if claimed.rowcount != 1:
            return 'window_reconciliation_required'
        if self.store.paused():
            self.save(cycle, 'closed', 'stopped_before_any_window_action')
            return 'paused'
        self.save(cycle, 'opening', 'claimed_before_open')
        try:
            lease = self.backend.open(thread_id=self.store.c['thread_id'],
                expected_cwd=self.store.c['expected_cwd'],
                timeout_seconds=self.store.c.get('window_timeout_seconds', 30))
            if (not isinstance(lease, dict) or not isinstance(lease.get('token'), str)
                    or not lease['token'] or lease.get('thread_id') != self.store.c['thread_id']):
                raise ValueError('unverified lease')
            self.save(cycle, 'open', 'opened_and_minimized', lease=lease)
        except Exception as e:
            self.save(cycle, 'opening', 'open_outcome_unknown', error_type=type(e).__name__)
            return 'window_open_unknown'
        if self.store.paused():
            return 'paused'
        result = self.inspect_owner(row)
        return 'owner_ready' if result['can_send'] else result['reason']

    def finish(self, cycle, row):
        s = self.store
        if not self.completion(row):
            return 'waiting_turn_completion'
        from trigger import digest
        attestation = json.loads(row['detail'])
        if (attestation.get('attestation') != 'caller_verified_delivery'
                or digest(Path(attestation['evidence']).read_bytes()) != attestation['sha256']):
            return 'delivery_evidence_unconfirmed'
        if cycle['phase'] == 'reused':
            self.save(cycle, 'closed', 'reused_owner_no_window_to_close')
            return 'cycle_closed'
        if not cycle.get('lease') or self.backend is None:
            return 'window_reconciliation_required'
        observed = self.backend.inspect(cycle['lease'])
        if observed['status'] == 'absent':
            return self.closed(cycle, row, 'owned_window_confirmed_absent')
        if observed['status'] != 'owned':
            return 'window_identity_unconfirmed'
        if cycle['phase'] == 'closing':
            return 'window_reconciliation_required'
        current = self.inspect_owner(row)
        if not current['can_send']:
            return current['reason']
        if s.paused():
            return 'paused'
        self.save(cycle, 'closing', 'claimed_before_close')
        try:
            result = self.backend.close(cycle['lease'])
            if result['status'] != 'absent':
                raise ValueError('close not confirmed')
        except Exception as e:
            self.save(cycle, 'closing', 'close_outcome_unknown', error_type=type(e).__name__)
            return 'window_close_unknown'
        return self.closed(cycle, row, 'normal_close_confirmed')

    def closed(self, cycle, row, reason):
        try:
            after = self.inspect_owner(row)
            owner = 'available' if after['can_send'] else after['reason']
        except Exception:
            owner = 'unknown'
        self.save(cycle, 'closed', reason, owner_after_close=owner)
        return 'cycle_closed'

    def step(self):
        s = self.store
        if s.paused():
            return 'paused'
        if not s.c.get('owner_loading_enabled', False):
            return 'loader_disabled'
        if not s.c['owner_verified'] or s.c.get('chat_adapter') != 'desktop_ipc':
            return 'owner_not_verified'
        if s.db.execute('SELECT 1 FROM meta WHERE k=?',
                        ('owner_load_attempt:' + s.c['thread_id'],)).fetchone():
            return 'legacy_reconciliation_required'
        try:
            active = [x for x in self.records() if x['phase'] != 'closed']
            if len(active) > 1:
                return 'window_reconciliation_required'
            rows = s.rows()
            if active:
                cycle = active[0]
                row = next(r for r in rows if r['id'] == cycle['batch_id'])
                self.batch_id = row['id']
                if cycle['phase'] == 'opening':
                    return 'window_reconciliation_required'
                if row['state'] == 'delivered':
                    return self.finish(cycle, row)
                if row['state'] != 'ready' or row.get('dispatch_text') or row.get('dispatch_meta'):
                    return 'receipt_only'
                result = self.inspect_owner(row)
                if result['reason'] == 'waiting_owner' and cycle['phase'] == 'reused':
                    return self.claim_open(row)
                return 'owner_ready' if result['can_send'] else result['reason']
            pending = [r for r in rows if r['state'] != 'delivered']
            if not pending:
                return 'quiet'
            row = pending[0]
            self.batch_id = row['id']
            if row['state'] != 'ready' or row.get('dispatch_text') or row.get('dispatch_meta'):
                return 'receipt_only'
            result = self.inspect_owner(row)
            if result['can_send']:
                self.save(dict(batch_id=row['id'], lease=None), 'reused', 'fresh_idle_owner_reused')
                return 'owner_ready'
            if result['reason'] != 'waiting_owner':
                return result['reason']
            return self.claim_open(row)
        except Exception:
            # Malformed IPC/UI replies cannot terminate the file listener.
            # Any action intent stays durable and is never silently replayed.
            return 'owner_check_failed'


def cycle_tick(store, backend=None, adapter_factory=None):
    """Serial cleanup-before-dispatch under the existing worker lock."""
    from trigger import dispatch_one
    if not store.c.get('owner_loading_enabled', False):
        active = store.db.execute("SELECT v FROM meta WHERE k LIKE 'window_cycle:%'")
        if any(json.loads(r[0])['phase'] != 'closed' for r in active):
            return 'window_cycle_disabled_reconciliation_required'
        return dispatch_one(store, adapter_factory=adapter_factory)
    manager = WindowCycles(store, backend, adapter_factory)
    result = manager.step()
    if result in ('owner_ready', 'receipt_only'):
        return dispatch_one(store, adapter_factory=adapter_factory, expected_batch_id=manager.batch_id)
    return result
