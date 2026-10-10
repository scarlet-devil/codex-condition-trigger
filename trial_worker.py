"""Restartable entry point for an explicitly bounded trial.

Each invocation retains its own receipts and logs. OS logon/restart policy is
configured separately; this process never clears STOP or extends a deadline.
"""
import argparse
import contextlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import traceback
import time
import uuid

import trigger
from trial_limits import trial_deadline


def now():
    return datetime.now(timezone.utc).isoformat()


def run_worker(config_path, live=True, config=None, authorization_deadline=None):
    c = trigger.load_config(config_path) if config is None else config
    if trial_deadline(c) is None:
        raise ValueError('recovery worker requires an explicit fixed trial deadline')
    root = Path(c['state_dir']) / 'worker-runs'
    run = root / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12])
    run.mkdir(parents=True)
    info = dict(pid=os.getpid(), started_at_utc=now(), live=live,
                deadline_utc=c['trial_expires_at_utc'], run_dir=str(run),
                config_sha256=trigger.digest(Path(config_path).read_bytes()),
                effective_config_sha256=trigger.digest(trigger.encode(c).encode()),
                source_sha256={name: trigger.digest((Path(__file__).parent / name).read_bytes())
                    for name in ('trial_worker.py', 'trigger.py', 'owner_loading.py',
                                 'desktop_ipc.py', 'chat_adapters.py', 'trial_limits.py')})
    def save(name, record):
        trigger.atomic_write(run / name, (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode())
    store = None
    code = 0
    with (run / 'stdout.jsonl').open('a', encoding='utf-8', buffering=1) as out, \
            (run / 'stderr.txt').open('a', encoding='utf-8', buffering=1) as err, \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        save('start.json', info)
        try:
            store = trigger.Store(c)
            if authorization_deadline is not None:
                store.monotonic_deadline = min(store.monotonic_deadline, authorization_deadline)
            trigger.atomic_write(Path(c['state_dir']) / 'latest-worker.json',
                                 (json.dumps(info, ensure_ascii=False, indent=2) + '\n').encode())
            trigger.run(store, live=live)
            info.update(result='stopped', expiry_observed=(store.path / 'TRIAL_EXPIRED.json').exists())
        except Exception as error:
            # A second launcher does not terminate the existing worker. A
            # recorded worker exception is retried by the bounded entry loop.
            duplicate = isinstance(error, RuntimeError) and str(error) == 'another command owns this trigger state'
            info.update(result='already_running' if duplicate else 'failed', error_type=type(error).__name__)
            code = 0 if duplicate else 1
            traceback.print_exc()
        finally:
            if store is not None:
                store.close()
            info.update(stopped_at_utc=now(), exit_code=code)
            save('exit.json', info)
    return code


def run_bounded(config_path, live=True, retry_seconds=30):
    """Up to three retries inside the authorized entry process.

    Windows task RestartOnFailure was not effective in the local smoke test.
    This path handles recorded worker exceptions, not process termination or
    power loss; the independently registered logon trigger covers the latter.
    """
    initial = trigger.load_config(config_path)
    expiry = trial_deadline(initial)
    if expiry is None:
        raise ValueError('recovery worker requires an explicit fixed trial deadline')
    budget = time.monotonic() + max(0, expiry - time.time())
    state = Path(initial['state_dir'])
    for attempt in range(4):
        if attempt:
            until = time.monotonic() + retry_seconds
            while time.monotonic() < until:
                if ((state / 'STOP').exists() or (state / 'TRIAL_EXPIRED.json').exists()
                        or time.time() >= expiry or time.monotonic() >= budget):
                    return 0
                time.sleep(min(.1, max(0, until - time.monotonic())))
            if (time.time() >= expiry or time.monotonic() >= budget
                    or (state / 'STOP').exists() or (state / 'TRIAL_EXPIRED.json').exists()):
                return 0
        current = trigger.load_config(config_path)
        if (trial_deadline(current) != expiry or any(current[k] != initial[k]
                for k in ('input_dir', 'state_dir', 'thread_id', 'expected_cwd'))):
            return 1  # a retry cannot silently move or renew this instance
        result = run_worker(config_path, live=live, config=current, authorization_deadline=budget)
        if result == 0:
            return 0
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--dry', action='store_true', help='observe files only; no IPC')
    args = parser.parse_args()
    raise SystemExit(run_bounded(args.config, live=not args.dry))
