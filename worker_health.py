"""Progress evidence, not a PID-based claim that a worker is alive."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import uuid


class Progress:
    def __init__(self, store, live):
        self.path = store.path / 'watcher-progress.json'
        self.record = dict(schema=1, run_id=uuid.uuid4().hex, pid=os.getpid(),
                           mode='live' if live else 'dry', started_at_utc=self.utc(),
                           state='running')
        self.last_write = float('-inf')
        self.write('starting')

    @staticmethod
    def utc():
        return datetime.now(timezone.utc).isoformat()

    def write(self, phase=None, **values):
        if phase is None and time.monotonic() - self.last_write < 10:
            return
        from trigger import atomic_write, encode
        if phase is not None:
            self.record['phase'] = phase
        self.record.update(values, progress_at_utc=self.utc())
        atomic_write(self.path, (encode(self.record) + '\n').encode())
        self.last_write = time.monotonic()

    def finish(self, state, reason):
        self.write('exited', state=state, reason=reason, stopped_at_utc=self.utc())


def read_health(path, now=None):
    now = time.time() if now is None else now
    try:
        record = json.loads((Path(path) / 'watcher-progress.json').read_text(encoding='utf-8'))
        if record['schema'] != 1 or record['state'] not in ('running', 'stopped', 'failed'):
            raise ValueError('unrecognized progress record')
        age = now - datetime.fromisoformat(record['progress_at_utc']).timestamp()
        # A future-dated receipt must not look like recent progress.
        freshness = 'clock_uncertain' if age < 0 else 'recent' if age <= 30 else 'stale'
        return dict(record, progress_age_seconds=round(age, 3), freshness=freshness,
                    process_liveness='not_proven',
                    attention_required=record['state'] == 'failed' or
                        (record['state'] == 'running' and freshness != 'recent'))
    except (OSError, ValueError, KeyError, TypeError):
        return dict(state='unknown', freshness='unknown', process_liveness='not_proven',
                    attention_required=True, reason='progress record unavailable or invalid')
