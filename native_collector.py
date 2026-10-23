"""Read native outcomes for existing turns; never dispatch, authorize or ACK."""
from datetime import datetime, timezone
import json
import subprocess

from cwd_paths import cwd_matches


def project_turn(state, turn_id):
    """Known Desktop stream shape only; absence or ambiguity stays unknown.

    The canonical history stores ordered entry references to entitiesByKey.
    Unreferenced entities and transient overlays are not terminal evidence.
    """
    if state.get('resumeState') != 'resumed':
        return None
    history = state.get('turnHistory')
    if history is None:
        turns = state.get('turns')
    elif isinstance(history, dict) and history.get('kind') == 'canonical':
        h = history.get('history')
        if not isinstance(h, dict) or not isinstance(h.get('islands'), list) or not isinstance(h.get('entitiesByKey'), dict):
            return None
        turns = []
        for island in h['islands']:
            if not isinstance(island, dict) or not isinstance(island.get('entries'), list):
                return None
            for entry in island['entries']:
                if not isinstance(entry, dict) or not isinstance(entry.get('value'), str):
                    return None
                turns.append(h['entitiesByKey'].get(entry['value']))
    else:
        return None
    if not isinstance(turns, list) or not all(isinstance(t, dict) for t in turns):
        return None
    matching = [t for t in turns if t.get('turnId') == turn_id]
    if len(matching) != 1:
        return None
    turn = matching[0]
    if history is not None:
        overlays=state.get('turns')
        if not isinstance(overlays,list) or not all(isinstance(t,dict) for t in overlays):
            return None
        matching_overlays=[t for t in overlays if t.get('turnId')==turn_id]
        if len(matching_overlays)>1 or any(t.get('status')!=turn.get('status') or 'error' not in t
                or t['error']!=turn.get('error') for t in matching_overlays):
            return None
    status = turn.get('status')
    if status not in ('completed', 'failed', 'interrupted') or 'error' not in turn:
        return None
    if status == 'completed' and turn['error'] is not None:
        return None
    return dict(turn_id=turn_id, status=status, has_error=turn['error'] is not None)


def collect_outcomes(store, batch_id=None, client_factory=None):
    from desktop_ipc import IPCClient, RPCError
    from trigger import digest, encode
    if store.c.get('chat_adapter') != 'desktop_ipc':
        raise ValueError('native collector requires the registered Desktop adapter')
    results = []
    rows = [r for r in store.rows() if (batch_id is None or r['id'] == batch_id)
            and r['state'] in ('accepted','running','completed','ended','failed','uncertain','waiting_materials')
            and r['turn_id'] and r['execution_outcome'] == 'unknown']
    for row in rows:
        client = None
        try:
            client = (client_factory or IPCClient)(store.c['rpc_timeout_seconds'])
            owner = client.owner(store.c['thread_id'])
            snapshot = client.current_state(store.c['thread_id'],owner,store.c['expected_cwd'],turn_id=row['turn_id'])
            turn = snapshot.get('turn_result')
            if not turn:
                results.append(dict(batch_id=row['id'],status='unknown')); continue
            if (snapshot['thread_id'] != store.c['thread_id'] or not cwd_matches(snapshot['cwd'], store.c['expected_cwd'])
                    or turn['turn_id'] != row['turn_id']):
                raise ValueError('native binding mismatch')
            outcome = {'completed':'succeeded','failed':'failed','interrupted':'interrupted'}[turn['status']]
            evidence = dict(schema=1, source='verified_desktop_ipc', batch_id=row['id'],
                            manifest_sha256=digest((row['manifest']+'\n').encode()),
                            observed_at_utc=datetime.now(timezone.utc).isoformat(),
                            snapshot=snapshot, installation=client.installation)
            raw=encode(evidence)
            # Evidence and result commit together. Concurrent ACK/binding changes win.
            with store.db:
                store.db.execute('BEGIN IMMEDIATE')
                current=store.db.execute('SELECT * FROM batches WHERE id=?',(row['id'],)).fetchone()
                if (not current or current['state']=='delivered' or current['turn_id']!=row['turn_id']
                        or current['manifest']!=row['manifest'] or current['execution_outcome']!='unknown'
                        or store.db.execute('SELECT v FROM meta WHERE k=?',('execution_result:'+row['id'],)).fetchone()):
                    results.append(dict(batch_id=row['id'],status='changed'));continue
                store.db.execute('INSERT INTO meta VALUES (?,?)',('execution_result:'+row['id'],
                    encode(dict(attestation='verified_desktop_ipc',sha256=digest(raw.encode()),evidence=evidence,outcome=outcome))))
                state = 'ended' if outcome=='succeeded' else 'failed'
                if current['state']=='waiting_materials' and outcome=='succeeded': state='waiting_materials'
                store.db.execute('UPDATE batches SET state=?,execution_outcome=? WHERE id=?',(state,outcome,row['id']))
            results.append(dict(batch_id=row['id'],status='recorded',outcome=outcome))
        except (OSError, ValueError, RPCError, TimeoutError, EOFError, KeyError, subprocess.SubprocessError) as error:
            results.append(dict(batch_id=row['id'],status='unknown',reason=type(error).__name__))
        finally:
            if client is not None: client.close()
    return results
