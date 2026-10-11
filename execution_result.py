"""Explicit turn outcome evidence. A lifecycle end is never a success receipt."""
import json
from pathlib import Path


def record_outcome(store, batch_id, evidence):
    from trigger import digest, encode
    path = Path(evidence).resolve()
    raw = path.read_bytes()
    if not 0 < len(raw) <= 1024 * 1024:
        raise ValueError('invalid outcome evidence size')
    value = json.loads(raw)
    with store.db:
        store.db.execute('BEGIN IMMEDIATE')
        row = store.db.execute('SELECT * FROM batches WHERE id=?', (batch_id,)).fetchone()
        if (not row or row['state'] not in ('accepted', 'queued', 'running', 'completed', 'ended', 'failed', 'uncertain')
                or not row['turn_id'] or not isinstance(value, dict)
                or value.get('schema') != 1 or value.get('batch_id') != batch_id
                or value.get('turn_id') != row['turn_id']
                or value.get('manifest_sha256') != digest((row['manifest'] + '\n').encode())
                or value.get('source') != 'caller_verified_native_turn'
                or (value.get('native_runtime_status') == 'systemError' and value.get('native_turn_status') == 'completed')
                or value.get('native_turn_status') not in ('completed', 'failed', 'interrupted')):
            raise ValueError('outcome must attest the exact batch, manifest and native turn')
        outcome = {'completed': 'succeeded', 'failed': 'failed', 'interrupted': 'interrupted'}[value['native_turn_status']]
        if row['execution_outcome'] not in ('unknown', outcome):
            raise ValueError('conflicting outcome; retain evidence for manual reconciliation')
        attestation = encode(dict(evidence=str(path), sha256=digest(raw),
                                 attestation='caller_verified_native_turn', outcome=outcome))
        key = 'execution_result:' + batch_id
        old = store.db.execute('SELECT v FROM meta WHERE k=?', (key,)).fetchone()
        if old and old[0] != attestation:
            raise ValueError('outcome evidence already recorded')
        store.db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)', (key, attestation))
        state = 'ended' if outcome == 'succeeded' else 'failed'
        store.db.execute('UPDATE batches SET state=?,execution_outcome=? WHERE id=?',
                         (state, outcome, batch_id))


def batch_status(row):
    state = row['state']
    lifecycle = ('ended' if state in ('completed', 'ended', 'failed', 'waiting_materials') else
                 'unknown' if state == 'delivered' else state)
    return dict(id=row['id'], state=state, lifecycle=lifecycle,
                execution_outcome=row['execution_outcome'],
                business_delivery='caller_verified' if state == 'delivered' else 'unverified',
                submission=row['submission'], turn_id=row['turn_id'], detail=row['detail'])
