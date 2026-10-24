"""One attempt per fixed target, read-only partial state; never a send gate.

Uses installed owner-discovery v1 / read-model-settings v1 only. No snapshots,
history, model, window, database writes, or live runtime changes. Private target
configuration is passed separately and is not suitable for public commits.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import struct
import sys
import time

RUN = Path(__file__).resolve().parent
WORKSPACE = RUN.parents[2]
CODE = WORKSPACE / 'dot-results-monitor/runs/20261021-continuous-runtime/repo'
sys.path.insert(0, str(CODE))
from desktop_ipc import IPCClient, IPCFailure, WindowsPipe, verify_installation

FRAME_CAP = 64 * 1024
RX_CAP = 1024 * 1024
RPC_SECONDS = 10
ALLOWED = {'initialize': 1, 'thread-owner-discovery': 1,
           'thread-follower-read-model-settings': 1}
assert hashlib.sha256((CODE / 'desktop_ipc.py').read_bytes()).hexdigest() == 'f11a41f9ad395a7c721fecbed006299b8be610bdfd271b6611d5d068605c150f'

def norm(path):
    if path.startswith('\\\\?\\') and len(path) > 6 and path[5:7] == ':\\':
        path = path[4:]
    return os.path.normcase(os.path.normpath(path))

class MeasuredPipe(WindowsPipe):
    def __init__(self):
        self.wire_rx = self.wire_tx = 0
        super().__init__()

    def io(self, value, deadline, write=False, before_write=None):
        result = super().io(value, deadline, write, before_write)
        if write:
            self.wire_tx += result
        else:
            self.wire_rx += len(result)
        return result

class BoundedClient(IPCClient):
    def __init__(self, pipe, installation):
        self.pipe, self.installation = pipe, installation
        self.timeout = RPC_SECONDS
        self.deadline = time.monotonic() + RPC_SECONDS
        self.client_id = 'initializing-client'
        self.rx = self.tx = 0
        self.frames = []
        self.sent = []
        self.correlation = []
        self.stage = 'initialize'
        reply = self.request('initialize', {'clientType': 'farfield'})
        self.client_id = reply['result']['clientId']
        if not isinstance(self.client_id, str) or not self.client_id:
            raise ValueError('missing_client_identity')

    def write_frame(self, item, deadline, before_write=None):
        if item.get('type') != 'request' or item.get('method') not in ALLOWED:
            raise ValueError('request_not_allowlisted')
        item['version'] = ALLOWED[item['method']]
        item['timeoutMs'] = max(1, int((self.deadline - time.monotonic()) * 1000))
        self.sent.append(item['method'])
        raw = json.dumps(item, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        if len(raw) > FRAME_CAP:
            raise ValueError('tx_limit')
        self.pipe.write(struct.pack('<I', len(raw)) + raw, min(deadline, self.deadline))
        self.tx += len(raw) + 4

    def read_frame(self, deadline):
        deadline = min(deadline, self.deadline)
        if time.monotonic() >= deadline:
            raise TimeoutError('probe_deadline')
        if self.rx + 4 > RX_CAP:
            raise ValueError('cumulative_rx_limit')
        size, = struct.unpack('<I', self.pipe.read(4, deadline))
        self.rx += 4
        entry = {'stage': self.stage, 'declared_bytes': size, 'body_read': False}
        self.frames.append(entry)
        if not 0 < size <= FRAME_CAP:
            raise ValueError('single_frame_limit')
        if self.rx + size > RX_CAP:
            raise ValueError('cumulative_rx_limit')
        raw = self.pipe.read(size, deadline)
        self.rx += len(raw)
        item = json.loads(raw)
        if not isinstance(item, dict):
            raise ValueError('frame_not_object')
        entry.update(body_read=True, type=item.get('type'), method=item.get('method'))
        if time.monotonic() >= deadline:
            raise TimeoutError('probe_deadline')
        return item

    def request(self, method, params, target=None, **kwargs):
        # Only this isolated process's module table is extended; no source edit.
        import desktop_ipc
        if method not in ALLOWED:
            raise ValueError('request_not_allowlisted')
        desktop_ipc.METHODS[method] = ALLOWED[method]
        reply = super().request(method, params, target=target, deadline=self.deadline)
        self.correlation.append({'method': method, 'request_id_matched': True,
                                 'owner_matched': target is not None,
                                 'request_id_sha256': hashlib.sha256(reply['requestId'].encode()).hexdigest()})
        return reply

def bind(target):
    dbpath = Path(target['codex_home']) / 'state_5.sqlite'
    deadline = time.monotonic() + 5
    con = sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True, timeout=2)
    try:
        con.execute('PRAGMA query_only=ON')
        con.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        row = con.execute('SELECT id,cwd,rollout_path FROM threads WHERE id=?', (target['thread_id'],)).fetchone()
    finally:
        con.close()
    if not row or row[0] != target['thread_id'] or norm(row[1]) != norm(target['cwd']):
        raise ValueError('catalog_identity_mismatch')
    with Path(row[2]).open('rb') as f:
        header = f.readline(256 * 1024 + 1)
    if len(header) > 256 * 1024 or not header.endswith(b'\n'):
        raise ValueError('header_limit')
    meta = json.loads(header)
    if meta.get('type') != 'session_meta' or meta['payload'].get('id') != target['thread_id'] or norm(meta['payload'].get('cwd', '')) != norm(target['cwd']):
        raise ValueError('rollout_identity_mismatch')
    return {'catalog_exact_id_cwd': True, 'rollout_exact_id_cwd': True, 'header_bytes': len(header),
            'header_sha256': hashlib.sha256(header).hexdigest(), 'native_cwd_proof': False}

def run(target):
    began = time.monotonic()
    result = {'target': target['alias'], 'at_utc': datetime.now(timezone.utc).isoformat(),
              'runtime_status': 'unknown', 'can_send': False, 'model_sends': 0, 'window_actions': 0}
    client = pipe = None
    rpc_started = None
    try:
        result['binding'] = bind(target)
        pipe = MeasuredPipe()
        inst = verify_installation(pipe)
        if inst['archive_sha256'] != 'a05dfd86ca508148c83c25590639cf91a52c6647733cdf200723d85357052b49':
            raise ValueError('installation_changed')
        result['installation'] = {k: inst[k] for k in ('archive_bytes', 'archive_sha256', 'protocol_sources')}
        result['signature_status'] = inst['signature']['status']
        rpc_started = time.monotonic()
        # Keep the object even if initialize fails, to preserve its measurements.
        client = BoundedClient.__new__(BoundedClient)
        client.__init__(pipe, inst)
        client.stage = 'owner_discovery'
        owner = client.owner(target['thread_id'])
        result['owner_discovered'] = True
        client.stage = 'partial_state'
        reply = client.request('thread-follower-read-model-settings', {'conversationId': target['thread_id']}, target=owner)
        settings = reply.get('result', {}).get('settings')
        if not isinstance(settings, dict):
            raise ValueError('settings_not_object')
        result['settings_keys'] = sorted(settings)
        resume = settings.get('resumeState')
        result['resume_state'] = resume if resume in ('resumed', 'resuming', 'not-resumed', 'needs-resume') else 'unknown'
        result['freshness'] = 'unique request correlated to discovered owner; partial settings only; no runtime revision'
        result['missing_state_fields'] = [k for k in ('id', 'cwd', 'threadRuntimeStatus', 'revision') if k not in settings]
        result['result'] = 'partial_only_not_G0_pass'
    except Exception as e:
        result['result'] = 'unavailable_or_blocked'
        result['error_type'] = type(e).__name__
        result['error_category'] = str(e) if isinstance(e, IPCFailure) else 'bounded_probe_failure'
    finally:
        if pipe is not None:
            pipe.close()
            result['wire_rx_bytes'] = pipe.wire_rx
            result['wire_tx_bytes'] = pipe.wire_tx
        result['total_seconds'] = round(time.monotonic() - began, 6)
        if rpc_started is not None:
            result['ipc_seconds'] = round(time.monotonic() - rpc_started, 6)
        if client is not None and hasattr(client, 'rx'):
            result.update(rx_bytes=client.rx, tx_bytes=client.tx, frames=client.frames,
                          sent_methods=client.sent, correlations=client.correlation)
    return result

if __name__ == '__main__':
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    assert len(cfg['targets']) == 2
    output = {'frame_cap_bytes': FRAME_CAP, 'cumulative_rx_cap_bytes_per_target': RX_CAP,
              'ipc_deadline_seconds_per_target': RPC_SECONDS, 'retries': 0, 'probe_kind': 'partial_state_only',
              'results': [run(t) for t in cfg['targets']]}
    (RUN / 'PARTIAL_STATE_RESULTS.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(output, ensure_ascii=False, indent=2))
