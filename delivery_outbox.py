"""Upload-only recovery for frozen artifacts; never starts a turn or writes ACK.

The explicit resume command is separate from watcher/trial activation. A local
authorized backend implements lookup/upload/readback; no backend is bundled.
Unknown creation outcomes always require reconciliation before another upload.
"""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

MAX_ARTIFACT = 20 * 1024 * 1024
PREFIX = 'delivery_job:'


def jobs(store):
    return [json.loads(r[0]) for r in store.db.execute(
        "SELECT v FROM meta WHERE k LIKE 'delivery_job:%' ORDER BY k")]


def save(store, job):
    from trigger import encode
    job['updated_at_utc'] = datetime.now(timezone.utc).isoformat()
    with store.db:
        store.db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (PREFIX + job['id'], encode(job)))


def stage(store, batch_id, parent_id, paths):
    from trigger import InstanceLock, atomic_write, digest, encode, file_hash
    if not isinstance(parent_id, str) or not parent_id.strip() or len(parent_id) > 256:
        raise ValueError('an exact remote parent ID is required')
    if not 1 <= len(paths) <= 32:
        raise ValueError('expected 1 to 32 artifacts')
    lock = InstanceLock(store.path / 'delivery.lock')
    try:
        row = next((r for r in store.rows() if r['id'] == batch_id), None)
        if not row or row['state'] not in ('ended', 'completed', 'failed', 'waiting_materials', 'delivered'):
            raise ValueError('freeze delivery artifacts only after the batch lifecycle ends')
        artifacts, payloads = [], []
        for value in paths:
            path = Path(value)
            if not path.is_absolute():
                raise ValueError('artifact paths must be absolute')
            sha, size = file_hash(path, MAX_ARTIFACT)
            data = path.read_bytes()
            if len(data) != size or digest(data) != sha:
                raise ValueError('artifact changed while freezing')
            artifacts.append(dict(name=path.name, sha256=sha, size=size))
            payloads.append(data)
        if len({a['name'] for a in artifacts}) != len(artifacts):
            raise ValueError('artifact names must be unique within the delivery')
        ordered = sorted(zip(artifacts, payloads), key=lambda pair: pair[0]['name'])
        artifacts, payloads = map(list, zip(*ordered))
        descriptor = dict(schema=1, batch_id=batch_id, parent_id=parent_id,
                          manifest_sha256=digest((row['manifest'] + '\n').encode()), artifacts=artifacts)
        job_id = digest(encode(descriptor).encode())
        old = store.db.execute('SELECT v FROM meta WHERE k=?', (PREFIX + job_id,)).fetchone()
        if old:
            return job_id
        root = store.path / 'delivery-outbox' / job_id
        root.mkdir(parents=True, exist_ok=True)
        for i, (item, data) in enumerate(zip(artifacts, payloads)):
            # The job directory already binds the full descriptor hashes.
            # Repeating a hash here can exceed legacy Windows MAX_PATH.
            blob = root / (str(i) + '.blob')
            atomic_write(blob, data)
            item.update(path=str(blob), key=job_id + ':' + str(i), state='pending_upload', attempts=0)
        save(store, dict(descriptor, id=job_id, state='pending_upload'))
        return job_id
    finally:
        lock.close()


class CommandDriver:
    def __init__(self, config):
        self.command = config.get('delivery_command', [])
        self.timeout = config.get('delivery_timeout_seconds', 60)
        if (not isinstance(self.command, list) or not self.command
                or not all(isinstance(v, str) and v for v in self.command)):
            raise ValueError('delivery_command must name an authorized upload-only argv backend')
        if type(self.timeout) not in (int, float) or not 0 < self.timeout <= 120:
            raise ValueError('delivery timeout must be within (0, 120]')

    def __call__(self, request):
        result = subprocess.run(self.command, input=json.dumps(request).encode(), capture_output=True,
                                timeout=self.timeout, check=True,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        # Limit the accepted readback to a single bounded artifact plus metadata.
        if len(result.stdout) > MAX_ARTIFACT * 4 // 3 + 65536:
            raise ValueError('upload backend reply exceeds limit')
        return json.loads(result.stdout.decode('utf-8-sig'))


def resume(store, job_id, driver=None):
    """One operator-requested attempt, with per-artifact durable checkpoints.

STOP/deadline continue to govern watcher and model actions. This explicit
upload-only command may finish frozen delivery after a trial has ended; it
never clears STOP, starts the watcher, or infers new model authorization.
"""
    from trigger import InstanceLock, digest, file_hash
    lock = InstanceLock(store.path / 'delivery.lock')
    try:
        row = store.db.execute('SELECT v FROM meta WHERE k=?', (PREFIX + job_id,)).fetchone()
        if not row:
            raise ValueError('unknown delivery job')
        job = json.loads(row[0])
        for item in job['artifacts']:
            if file_hash(Path(item['path']), MAX_ARTIFACT) != (item['sha256'], item['size']):
                raise ValueError('frozen artifact changed; no external call made')
        if job['state'] == 'uploaded_verified':
            return job
        driver = CommandDriver(store.c) if driver is None else driver
        for item in job['artifacts']:
            if item['state'] == 'uploaded_verified':
                continue
            request = dict(schema=1, key=item['key'], batch_id=job['batch_id'],
                           manifest_sha256=job['manifest_sha256'], parent_id=job['parent_id'],
                           name=item['name'], sha256=item['sha256'], size=item['size'], path=item['path'])
            def call(action, **extra):
                reply = driver(dict(request, action=action, **extra))
                if (not isinstance(reply, dict) or reply.get('schema') != 1
                        or reply.get('key') != item['key']):
                    raise ValueError('unbound backend response')
                return reply
            try:
                # Even after timeout/process death, lookup is first. Merely
                # finding no matching filename is insufficient to recreate.
                observed = call('lookup')
                if observed.get('status') == 'absent' and observed.get('safe_to_create') is True:
                    item.update(state='upload_uncertain', attempts=item['attempts'] + 1)
                    job['state'] = 'upload_uncertain'
                    save(store, job)  # durable intent BEFORE any external upload
                    observed = call('upload')
                if observed.get('status') != 'found' or not isinstance(observed.get('file_id'), str) or not observed['file_id']:
                    raise ValueError('remote object not uniquely reconciled')
                file_id = observed['file_id']
                item['file_id'] = file_id
                save(store, job)
                receipt = call('readback', file_id=file_id)
                if (receipt.get('status') != 'found' or receipt.get('file_id') != file_id
                        or receipt.get('parent_id') != job['parent_id'] or receipt.get('name') != item['name']
                        or not isinstance(receipt.get('content_base64'), str)
                        or len(receipt['content_base64']) > (MAX_ARTIFACT + 2) // 3 * 4):
                    raise ValueError('readback identity or target mismatch')
                data = base64.b64decode(receipt['content_base64'], validate=True)
                if len(data) != item['size'] or digest(data) != item['sha256']:
                    raise ValueError('remote bytes differ from frozen artifact')
                item.update(state='uploaded_verified', receipt=dict(file_id=file_id,
                    parent_id=job['parent_id'], name=item['name'], size=len(data), sha256=digest(data),
                    verified_at_utc=datetime.now(timezone.utc).isoformat()))
                item.pop('error_type', None)
                save(store, job)
            except (OSError, ValueError, KeyError, TimeoutError, subprocess.SubprocessError) as error:
                # Do not publish backend stderr/credentials or reset to ready.
                item.update(state='upload_uncertain', error_type=type(error).__name__)
                job['state'] = 'upload_uncertain'
                save(store, job)
                return job
        job['state'] = 'uploaded_verified'
        save(store, job)
        return job
    finally:
        lock.close()
