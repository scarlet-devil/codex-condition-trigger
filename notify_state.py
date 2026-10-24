"""Notify-only state. Terminal release never changes business delivery."""
import json
from pathlib import Path
import re
import sqlite3
import uuid
import zipfile


def enabled_mode(c):
    return c.get('dispatch_mode', 'verified_delivery') == 'notify'


def validate(c):
    mode = c.setdefault('dispatch_mode', 'verified_delivery')
    if mode not in ('notify', 'verified_delivery'):
        raise ValueError('unknown dispatch_mode')
    if not enabled_mode(c):
        return
    if (c.get('chat_adapter') != 'desktop_ipc' or c.get('rule_schema') != 2
            or c.get('owner_loading_enabled') or c.get('native_result_collection')
            or c.get('resume_unloaded')):
        raise ValueError('notify requires schema2 desktop_ipc without loading or outcome collection')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', c.get('rule_id', '')):
        raise ValueError('invalid rule identity')
    for key, default in [('rule_revision', 1), ('max_pending_batches', 100), ('max_state_bytes', 1024**3)]:
        value = c.setdefault(key, default)
        if type(value) is not int or value <= 0:
            raise ValueError('invalid ' + key)
    if c.setdefault('initial_files', 'ignore') not in ('ignore', 'process'):
        raise ValueError('invalid initial_files')
    uuid.UUID(c['thread_id'])
    for key in ('input_dir', 'state_dir', 'expected_cwd', 'rollout_path'):
        if not Path(c[key]).is_absolute():
            raise ValueError('notify paths must be absolute')
    a, b = Path(c['input_dir']).resolve(), Path(c['state_dir']).resolve()
    if a == b or a in b.parents or b in a.parents:
        raise ValueError('input/state overlap')


def binding(c):
    return dict(schema=2, mode='notify', rule_id=c['rule_id'], revision=c['rule_revision'],
                rollout_path=c['rollout_path'], initial_files=c['initial_files'],task_instruction=c.get('task_instruction'),
                condition={k: c.get(k) for k in ('include', 'exclude', 'ready_file', 'settle_seconds')})


def setup(store):
    store.db.executescript('''
      CREATE TABLE IF NOT EXISTS baseline_versions(sha256 TEXT PRIMARY KEY,size INTEGER NOT NULL,reason TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS notifications(batch_id TEXT PRIMARY KEY,revision INTEGER NOT NULL,
        acceptance TEXT,terminal TEXT,released INTEGER NOT NULL DEFAULT 0,release_evidence TEXT);
    ''')
    with store.db:
        store.db.execute("INSERT OR IGNORE INTO meta VALUES ('notify_enabled','false')")
        store.db.execute("INSERT OR IGNORE INTO meta VALUES ('pause_epoch','0')")


def active(store):
    row = store.db.execute("SELECT v FROM meta WHERE k='notify_enabled'").fetchone()
    return row is not None and row[0] == 'true'


def pause_epoch(store):
    return int(store.db.execute("SELECT v FROM meta WHERE k='pause_epoch'").fetchone()[0])


def assert_target_available(c, path):
    from trigger import target_registry_root
    registry_path=target_registry_root()/'targets.sqlite'
    if not registry_path.exists():
        return
    db=sqlite3.connect(registry_path.as_uri()+'?mode=ro',uri=True)
    try:
        row=db.execute('SELECT state_dir FROM targets WHERE thread=?',(str(uuid.UUID(c['thread_id'])),)).fetchone()
        if row and row[0] != str(path.resolve()):
            raise ValueError('target already has an enabled rule')
    finally:
        db.close()


def registry(store):
    from trigger import target_registry_root
    root = target_registry_root()
    root.mkdir(parents=True, exist_ok=True)
    # ATTACH permits baseline, claim and enablement in one rollback-journal transaction.
    store.db.execute('ATTACH DATABASE ? AS rule_registry', (str(root/'targets.sqlite'),))
    store.db.execute('CREATE TABLE IF NOT EXISTS rule_registry.targets(thread TEXT PRIMARY KEY,state_dir TEXT NOT NULL)')


def guard(store):
    return store.trial_expired() or (store.path/'STOP').exists()


def validate_files(c, files):
    from trigger import file_hash
    for item in files:
        path = Path(c['input_dir'])/item['path']
        if path.suffix.lower() == '.zip':
            with zipfile.ZipFile(path) as archive:
                if sum(x.file_size for x in archive.infolist()) > c['max_zip_expanded_bytes']:
                    raise ValueError('ZIP exceeds expanded-size limit')
                if archive.testzip() is not None:
                    raise ValueError('ZIP CRC validation failed')
        if file_hash(path, c['max_file_bytes']) != (item['sha256'], item['size']):
            raise ValueError('baseline source changed')


def initialize(store, expected_pause_epoch=None):
    from trigger import snapshot
    if store.db.execute("SELECT 1 FROM meta WHERE k='notify_initialized'").fetchone():
        return  # a restart must never reset an existing baseline or pause
    expected_pause_epoch=pause_epoch(store) if expected_pause_epoch is None else expected_pause_epoch
    if guard(store):
        raise ValueError('paused or expired')
    files = snapshot(store.c, lambda: guard(store), require_ready=False)
    validate_files(store.c, files)
    if files != snapshot(store.c, lambda: guard(store), require_ready=False):
        raise ValueError('initial collection changed')
    if resource_reason(store, reserve=65536):
        raise ValueError('state_capacity')
    registry(store)
    try:
        with store.db:
            store.db.execute('BEGIN IMMEDIATE')
            claim(store)
            if store.c['initial_files'] == 'ignore':
                store.db.executemany('INSERT INTO baseline_versions VALUES (?, ?, ?)',
                    [(x['sha256'], x['size'], 'initial_ignore') for x in {f['sha256']: f for f in files}.values()])
            if guard(store) or pause_epoch(store) != expected_pause_epoch:
                raise ValueError('paused during initialization')
            store.db.execute("INSERT INTO meta VALUES ('notify_initialized','true')")
            store.db.execute("UPDATE meta SET v='true' WHERE k='notify_enabled'")
    finally:
        store.db.execute('DETACH DATABASE rule_registry')


def claim(store):
    target = str(uuid.UUID(store.c['thread_id']))
    directory = str(store.path.resolve())
    old = store.db.execute('SELECT state_dir FROM rule_registry.targets WHERE thread=?', (target,)).fetchone()
    if old and old[0] != directory:
        raise ValueError('target already has an enabled rule')
    store.db.execute('INSERT OR IGNORE INTO rule_registry.targets VALUES (?,?)', (target, directory))


def set_active(store, value):
    if value and (guard(store) or not store.db.execute("SELECT 1 FROM meta WHERE k='notify_initialized'").fetchone()):
        raise ValueError('uninitialized, STOP or expired; cannot resume')
    registry(store)
    try:
        with store.db:
            store.db.execute('BEGIN IMMEDIATE')
            if value:
                claim(store)
            else:
                store.db.execute("UPDATE meta SET v=CAST(CAST(v AS INTEGER)+1 AS TEXT) WHERE k='pause_epoch'")
                store.db.execute('DELETE FROM rule_registry.targets WHERE thread=? AND state_dir=?',
                    (str(uuid.UUID(store.c['thread_id'])), str(store.path.resolve())))
            store.db.execute("UPDATE meta SET v=? WHERE k='notify_enabled'", ('true' if value else 'false',))
    finally:
        store.db.execute('DETACH DATABASE rule_registry')


def pending(store):
    released = {r[0] for r in store.db.execute('SELECT batch_id FROM notifications WHERE released=1')}
    return [r for r in store.rows() if r['id'] not in released]


def resource_reason(store, reserve=0, freezing=False):
    from trigger import safe_stat
    used = sum(safe_stat(p).st_size for p in store.path.rglob('*') if p.is_file())
    if used + reserve >= store.c['max_state_bytes']:
        return 'state_capacity'
    if freezing and len(pending(store)) >= store.c['max_pending_batches']:
        return 'batch_capacity'
    return None


def context(store, row, turn_id):
    from trigger import digest
    meta = json.loads(row['dispatch_meta'])
    baseline = meta['baseline']
    if (not isinstance(baseline, dict) or type(baseline.get('bytes')) is not int
            or baseline['bytes'] <= 0 or not isinstance(baseline.get('inode'), int)
            or not re.fullmatch('[0-9a-f]{64}', baseline.get('sha256', ''))
            or not isinstance(meta.get('request_id'), str) or not meta['request_id']
            or not isinstance(turn_id, str) or not turn_id or not row.get('dispatch_text')):
        raise ValueError('incomplete notification intent')
    return dict(thread_id=store.c['thread_id'], cwd=store.c['expected_cwd'], batch_id=row['id'],
                manifest_sha256=digest((row['manifest']+'\n').encode()), request_id=meta['request_id'],
                client_id=row['client_id'], turn_id=turn_id, baseline=baseline,
                text_sha256=digest(row['dispatch_text'].encode()), exact_text=True, post_intent=True)


def commit(store, batch_id, receipt, from_send=False):
    from trigger import encode
    with store.db:
        store.db.execute('BEGIN IMMEDIATE')
        row = dict(store.db.execute('SELECT * FROM batches WHERE id=?', (batch_id,)).fetchone())
        note = store.db.execute('SELECT * FROM notifications WHERE batch_id=?', (batch_id,)).fetchone()
        if not note or note['released']:
            return 'notification_released' if note else 'needs_reconciliation'
        state = receipt['state']
        outcome = receipt.get('execution_outcome', 'unknown')
        if state not in ('accepted','running','queued','ended','completed','failed','uncertain') or outcome not in ('unknown','failed','interrupted','succeeded'):
            raise ValueError('invalid notification lifecycle')
        proof = receipt.get('notify_evidence')
        if from_send:
            expected = dict(context(store, row, receipt.get('turn_id')), phase='accepted', source='native_ipc')
            if state != 'accepted' or proof != expected:
                raise ValueError('missing native acceptance binding')
            if note['acceptance'] and json.loads(note['acceptance']) != proof:
                raise ValueError('conflicting native receipt')
            store.db.execute('UPDATE notifications SET acceptance=? WHERE batch_id=?', (encode(proof),batch_id))
        elif state in ('ended','completed','failed'):
            if not note['acceptance']:
                return 'needs_reconciliation'
            accepted = json.loads(note['acceptance'])
            expected = dict(context(store,row,row['turn_id']), phase='terminal',source='native_turn_rollout')
            if proof != expected or receipt.get('turn_id') != accepted['turn_id']:
                return 'needs_reconciliation'
            if note['terminal'] and json.loads(note['terminal']) != proof:
                return 'needs_reconciliation'
            store.db.execute('UPDATE notifications SET terminal=? WHERE batch_id=?', (encode(proof),batch_id))
        elif receipt.get('turn_id') and (not note['acceptance'] or receipt['turn_id'] != row['turn_id']):
            return 'needs_reconciliation'
        if note['terminal'] or row['state'] == 'delivered':
            return row['state']  # late observations cannot rewrite the final outcome
        store.db.execute('UPDATE batches SET state=?,turn_id=?,execution_outcome=?,detail=? WHERE id=?',
            (state, receipt.get('turn_id',row['turn_id']),outcome,receipt.get('detail'),batch_id))
        return state


def release(store, row, adapter):
    from cwd_paths import cwd_matches
    from trigger import encode
    note = store.db.execute('SELECT acceptance,terminal FROM notifications WHERE batch_id=?',(row['id'],)).fetchone()
    if not note or not note['acceptance'] or not note['terminal']:
        return None
    inspection = adapter.inspect(dict(row,state='ready'))
    if not inspection['can_send']:
        return inspection['reason']
    fresh = inspection.get('fresh_state')
    if (not isinstance(fresh, dict) or fresh.get('status') != 'idle'
            or fresh.get('thread_id') != store.c['thread_id']
            or not isinstance(fresh.get('cwd'), str) or not cwd_matches(fresh['cwd'],store.c['expected_cwd'])
            or not isinstance(fresh.get('owner_id'), str) or not fresh['owner_id']
            or not isinstance(fresh.get('request_id'),str) or not fresh['request_id']
            or type(fresh.get('revision')) is not int or type(fresh.get('requested_revision')) is not int
            or fresh['requested_revision'] < 0 or fresh['revision'] < fresh['requested_revision']):
        return 'needs_fresh_idle_evidence'
    with store.db:
        store.db.execute('BEGIN IMMEDIATE')
        if store.paused() or resource_reason(store):
            return 'paused_or_capacity'
        store.db.execute('UPDATE notifications SET released=1,release_evidence=? WHERE batch_id=? AND acceptance IS NOT NULL AND terminal IS NOT NULL', (encode(fresh),row['id']))
    return 'notification_released'


def status(store):
    from execution_result import batch_status
    from worker_health import read_health
    notes = {r['batch_id']:dict(r) for r in store.db.execute('SELECT * FROM notifications')}
    rows=[]
    for row in store.rows():
        n=notes[row['id']]
        rows.append(dict(batch_status(row), notification_released=bool(n['released']),
            native_acceptance=bool(n['acceptance']), exact_terminal=bool(n['terminal']),rule_revision=n['revision']))
    return dict(dispatch_mode='notify',enabled=active(store),paused=store.paused(),
                resource_reason=resource_reason(store,freezing=True),watcher=read_health(store.path),
                backlog=dict(batches=len(pending(store))),batches=rows)
