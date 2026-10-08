"""Experimental Windows Desktop IPC; bounded target only, no settings overrides.

Protocol reference: Destiny-Rul/CodexAgentControl @ 76408870888198f7ee3973b807d2302a86236143.
See THIRD_PARTY_NOTICES.md. Implementation is independent Python, not official API.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import time
import uuid

from chat_adapters import NotDispatched, RPCError

MAX_FRAME = 32 * 1024 * 1024
MAX_ROLLOUT = 64 * 1024 * 1024
METHODS = {'initialize': 1, 'thread-owner-discovery': 1, 'thread-follower-start-turn': 2,
           'thread-stream-following-changed': 1, 'thread-stream-state-changed': 11,
           'thread-follower-load-complete-history': 1}


class IPCFailure(RPCError):
    """Fixed diagnostic fields only; never retain arbitrary remote error text."""
    def __init__(self, stage, category):
        self.stage = stage if stage in ('transport', 'installation', 'initialize',
            'owner_discovery', 'current_state', 'start_turn') else 'protocol'
        self.category = category if category in ('transport', 'timeout', 'protocol',
            'owner_unavailable', 'remote_rejected') else 'protocol'
        super().__init__(self.stage + ':' + self.category)


def ipc_failure(error, stage):
    if isinstance(error, IPCFailure):
        return error
    category = ('timeout' if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)) else
                'transport' if isinstance(error, (OSError, EOFError, subprocess.SubprocessError)) else 'protocol')
    return IPCFailure(stage, category)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def protocol_object(value, where):
    if not isinstance(value, dict):
        raise RPCError('expected protocol object: ' + where)
    return value


def protocol_id(value, where):
    if not isinstance(value, str) or not value:
        raise RPCError('missing protocol identifier: ' + where)
    return value


def start_params(thread_id, client_id, text):
    return {'conversationId': thread_id, 'turnStart': {
        'request': {'threadId': thread_id, 'clientUserMessageId': client_id,
                    'input': [{'type': 'text', 'text': text, 'text_elements': []}], 'additionalContext': {}},
        'context': {'attachments': [], 'commentAttachments': [], 'inheritThreadSettings': True,
                    'mcpAppModelContextAttachments': []}}, 'isSteering': False}


def rollout_state(path, thread_id, expected_cwd, *, baseline=None, lifecycle=True):
    """Read only the explicitly configured rollout. Preserve tool records verbatim.

    Missing/partial/changed history is unknown, never evidence of an idle target.
    This is a private-file compatibility fallback, not authenticated provenance.
    """
    path = Path(path)
    before = path.stat()
    if before.st_size > MAX_ROLLOUT:
        raise ValueError('target rollout exceeds bounded observer limit')
    data = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('target rollout changed while reading')
    if not data or not data.endswith(b'\n'):
        raise ValueError('incomplete target rollout')
    lines = data.splitlines(keepends=True)
    rows = [protocol_object(json.loads(line), 'rollout row') for line in lines]
    meta = rows[0]
    if meta.get('type') != 'session_meta' or meta.get('payload', {}).get('id') != thread_id:
        raise ValueError('wrong target rollout identity')
    norm = lambda p: os.path.normcase(os.path.normpath(p))
    if norm(meta['payload'].get('cwd', '')) != norm(expected_cwd):
        raise ValueError('wrong target cwd')
    offset = len(lines[0])
    if baseline and (before.st_ino != baseline['inode'] or len(data) < baseline['bytes']
                     or sha(data[:baseline['bytes']]) != baseline['sha256']
                     or data[baseline['bytes']-1:baseline['bytes']] != b'\n'):
        raise ValueError('target rollout baseline was replaced, truncated or rewritten')
    turns, active, status, settings = {}, None, 'unknown', {}
    for row, line in zip(rows[1:], lines[1:]):
        after_baseline = baseline is None or offset >= baseline['bytes']
        offset += len(line)
        kind, p = row.get('type'), protocol_object(row.get('payload', {}), 'rollout payload')
        if kind == 'turn_context':
            if p.get('cwd') and norm(p['cwd']) != norm(expected_cwd):
                raise ValueError('turn context cwd changed')
            settings = {k: p[k] for k in ('model', 'effort', 'approval_policy', 'sandbox_policy', 'cwd') if k in p}
        if not lifecycle or not after_baseline:
            continue
        if kind == 'event_msg' and p.get('type') == 'task_started':
            turn = p.get('turn_id')
            if not isinstance(turn, str) or not turn:
                raise ValueError('missing native turn identity')
            if active is not None or turn in turns:
                raise ValueError('overlapping or duplicate lifecycle; native idle evidence required')
            active, status = turn, 'busy'
            turns.setdefault(turn, {'state': 'running', 'records': []})
        if active is not None:
            # Includes action, tool output, context and final; no schema whitelist
            # that silently discards the evidence needed for acceptance.
            turns[active]['records'].append(row)
        if kind == 'event_msg' and p.get('type') in ('task_complete', 'turn_aborted', 'task_failed'):
            if active is None or p.get('turn_id') != active:
                raise ValueError('unmatched lifecycle completion')
            turns[active]['state'] = 'completed' if p['type'] == 'task_complete' else 'failed'
            status = 'idle' if p['type'] == 'task_complete' else 'interrupted'
            active = None
    return {'status': status, 'turns': turns, 'settings': settings,
            'baseline': {'bytes': len(data), 'sha256': sha(data), 'inode': before.st_ino}}


class WindowsPipe:
    """Overlapped I/O: a quiet or noisy peer cannot escape the RPC deadline."""
    def __init__(self):
        if os.name != 'nt':
            raise OSError('Desktop IPC backend requires Windows')
        import ctypes as ct
        from ctypes import wintypes as wt
        self.ct, self.wt = ct, wt
        class Overlapped(ct.Structure):
            _fields_ = [('Internal', ct.c_size_t), ('InternalHigh', ct.c_size_t),
                        ('Offset', wt.DWORD), ('OffsetHigh', wt.DWORD), ('hEvent', wt.HANDLE)]
        self.Overlapped = Overlapped
        k = self.k = ct.WinDLL('kernel32', use_last_error=True)
        specs = {
            'CreateFileW': ([wt.LPCWSTR, wt.DWORD, wt.DWORD, ct.c_void_p, wt.DWORD, wt.DWORD, wt.HANDLE], wt.HANDLE),
            'CreateEventW': ([ct.c_void_p, wt.BOOL, wt.BOOL, wt.LPCWSTR], wt.HANDLE),
            'CloseHandle': ([wt.HANDLE], wt.BOOL),
            'ReadFile': ([wt.HANDLE, ct.c_void_p, wt.DWORD, ct.POINTER(wt.DWORD), ct.POINTER(Overlapped)], wt.BOOL),
            'WriteFile': ([wt.HANDLE, ct.c_void_p, wt.DWORD, ct.POINTER(wt.DWORD), ct.POINTER(Overlapped)], wt.BOOL),
            'WaitForSingleObject': ([wt.HANDLE, wt.DWORD], wt.DWORD),
            'CancelIoEx': ([wt.HANDLE, ct.POINTER(Overlapped)], wt.BOOL),
            'GetOverlappedResult': ([wt.HANDLE, ct.POINTER(Overlapped), ct.POINTER(wt.DWORD), wt.BOOL], wt.BOOL),
            'GetNamedPipeServerProcessId': ([wt.HANDLE, ct.POINTER(wt.ULONG)], wt.BOOL),
            'OpenProcess': ([wt.DWORD, wt.BOOL, wt.DWORD], wt.HANDLE),
            'QueryFullProcessImageNameW': ([wt.HANDLE, wt.DWORD, wt.LPWSTR, ct.POINTER(wt.DWORD)], wt.BOOL),
        }
        for name, (args, restype) in specs.items():
            getattr(k, name).argtypes, getattr(k, name).restype = args, restype
        self.handle = k.CreateFileW(r'\\.\pipe\codex-ipc', 0xC0000000, 0, None, 3, 0x40000000, None)
        if self.handle == ct.c_void_p(-1).value:
            raise ct.WinError(ct.get_last_error())

    def server_image(self):
        ct, wt, k = self.ct, self.wt, self.k
        pid = wt.ULONG()
        if not k.GetNamedPipeServerProcessId(self.handle, ct.byref(pid)):
            raise ct.WinError(ct.get_last_error())
        process = k.OpenProcess(0x1000, False, pid.value)
        if not process:
            raise ct.WinError(ct.get_last_error())
        try:
            size = wt.DWORD(32768)
            name = ct.create_unicode_buffer(size.value)
            if not k.QueryFullProcessImageNameW(process, 0, name, ct.byref(size)):
                raise ct.WinError(ct.get_last_error())
            return pid.value, Path(name.value)
        finally:
            k.CloseHandle(process)

    def io(self, value, deadline, write=False):
        ct, wt, k = self.ct, self.wt, self.k
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('pipe deadline')
        buffer = ct.create_string_buffer(value if write else value)
        length = len(value) if write else value
        event = k.CreateEventW(None, True, False, None)
        if not event:
            raise ct.WinError(ct.get_last_error())
        overlapped, count = self.Overlapped(), wt.DWORD()
        overlapped.hEvent = event
        pending = False
        try:
            ok = (k.WriteFile if write else k.ReadFile)(self.handle, buffer, length, ct.byref(count), ct.byref(overlapped))
            if not ok:
                error = ct.get_last_error()
                if error != 997:  # ERROR_IO_PENDING
                    raise ct.WinError(error)
                pending = True
                wait = k.WaitForSingleObject(event, max(1, math.ceil(remaining * 1000)))
                if wait != 0:
                    raise TimeoutError('pipe deadline')
                if not k.GetOverlappedResult(self.handle, ct.byref(overlapped), ct.byref(count), False):
                    raise ct.WinError(ct.get_last_error())
                pending = False
            if time.monotonic() >= deadline:
                raise TimeoutError('pipe deadline')
            if count.value == 0:
                raise EOFError('pipe closed')
            return count.value if write else buffer.raw[:count.value]
        finally:
            if pending:
                k.CancelIoEx(self.handle, ct.byref(overlapped))
                # Also covers KeyboardInterrupt/SystemExit. Cancellation is not
                # completion; keep buffer/OVERLAPPED alive until kernel release.
                # Drain latency is outside the normal RPC deadline guarantee.
                k.GetOverlappedResult(self.handle, ct.byref(overlapped), ct.byref(count), True)
            k.CloseHandle(event)

    def write(self, data, deadline):
        offset = 0
        while offset < len(data):
            offset += self.io(data[offset:], deadline, True)

    def read(self, size, deadline):
        data = bytearray()
        while len(data) < size:
            data.extend(self.io(size - len(data), deadline))
        return bytes(data)

    def close(self):
        if self.handle is not None:
            self.k.CloseHandle(self.handle)
            self.handle = None


def verify_installation(pipe):
    pid, exe = pipe.server_image()
    if exe.name.lower() != 'chatgpt.exe':
        raise ValueError('named pipe is not served by Desktop')
    # Path is data in the environment, never interpolated shell code.
    command = ("$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new(); "
               "Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Security/Microsoft.PowerShell.Security.psd1'); "
               "$s=Get-AuthenticodeSignature -LiteralPath $env:TRIGGER_DESKTOP_EXE; "
               "@{status=[string]$s.Status;subject=$s.SignerCertificate.Subject}|ConvertTo-Json -Compress")
    env = dict(os.environ, TRIGGER_DESKTOP_EXE=str(exe))
    ps = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
    result = subprocess.run([ps, '-NoProfile', '-NonInteractive', '-Command', command], env=env,
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20, check=True,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    signed = json.loads(result.stdout)
    if signed.get('status') != 'Valid' or 'O="OpenAI OpCo, LLC"' not in (signed.get('subject') or ''):
        raise ValueError('Desktop signature is not trusted OpenAI')
    archive = exe.parent / 'resources/app.asar'
    source_matches = []
    with archive.open('rb') as f:
        prefix = f.read(16)
        magic, header_size, _, size = struct.unpack('<4I', prefix)
        if magic != 4 or not 0 < size < 50_000_000:
            raise ValueError('unknown ASAR header')
        tree = json.loads(f.read(size))['files']['.vite']['files']['build']['files']
        required = {k: v for k, v in METHODS.items() if k != 'initialize'}
        for name, entry in tree.items():
            if not name.endswith('.js') or entry.get('unpacked') or entry.get('size', 0) > MAX_FRAME:
                continue
            f.seek(8 + header_size + int(entry['offset']))
            raw = f.read(entry['size'])
            text = raw.decode('utf-8')
            if all(re.search('"' + re.escape(method) + r'"\s*:\s*' + str(version) + r'\b', text) for method, version in required.items()):
                source_matches.append({'path': '.vite/build/' + name, 'sha256': sha(raw)})
        f.seek(0)
        h = hashlib.sha256()
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    if not source_matches:
        raise ValueError('required IPC method versions are not present')
    return {'server_pid': pid, 'exe': str(exe), 'signature': signed, 'archive_bytes': archive.stat().st_size,
            'archive_sha256': h.hexdigest(), 'protocol_sources': source_matches, 'methods': METHODS}


class IPCClient:
    def __init__(self, timeout, pipe=None, verifier=verify_installation):
        try:
            self.pipe, self.timeout = pipe or WindowsPipe(), timeout
        except (OSError, TimeoutError) as error:
            raise ipc_failure(error, 'transport') from None
        self.client_id = 'initializing-client'
        stage = 'installation'
        try:
            self.installation = verifier(self.pipe)
            stage = 'initialize'
            reply = self.request('initialize', {'clientType': 'farfield'})
            self.client_id = protocol_id(protocol_object(reply.get('result'), 'initialize.result').get('clientId'), 'clientId')
        except (OSError, ValueError, RPCError, TimeoutError, EOFError, KeyError, subprocess.SubprocessError) as error:
            self.close()
            raise ipc_failure(error, stage) from None
        except BaseException:
            self.close()
            raise

    def write_frame(self, item, deadline):
        data = json.dumps(item, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        if len(data) > MAX_FRAME:
            raise ValueError('oversized IPC request')
        self.pipe.write(struct.pack('<I', len(data)) + data, deadline)

    def read_frame(self, deadline):
        if time.monotonic() >= deadline:
            raise TimeoutError('IPC response deadline')
        size, = struct.unpack('<I', self.pipe.read(4, deadline))
        if not 0 < size <= MAX_FRAME:
            raise ValueError('invalid IPC frame size')
        item = protocol_object(json.loads(self.pipe.read(size, deadline)), 'frame')
        if time.monotonic() >= deadline:
            raise TimeoutError('IPC response deadline')
        return item

    def request(self, method, params, target=None, request_id=None, deadline=None):
        request_id = request_id or str(uuid.uuid4())
        deadline = deadline if deadline is not None else time.monotonic() + self.timeout
        request = {'type': 'request', 'requestId': request_id, 'sourceClientId': self.client_id,
                   'version': METHODS[method], 'method': method, 'params': params,
                   'timeoutMs': max(1, int(self.timeout * 1000))}
        if target:
            request['targetClientId'] = target
        self.write_frame(request, deadline)
        while True:
            item = self.read_frame(deadline)
            if item.get('type') != 'response' or item.get('requestId') != request_id:
                continue
            # Router-level negative envelopes omit method/handledByClientId.
            # Correlate the request first. This is a rejection, never success.
            if item.get('resultType') == 'error':
                stage = {'initialize': 'initialize', 'thread-owner-discovery': 'owner_discovery',
                         'thread-follower-start-turn': 'start_turn'}.get(method, 'current_state')
                category = ('owner_unavailable' if item.get('error') == 'no-client-found'
                            else 'remote_rejected')
                raise IPCFailure(stage, category)
            if item.get('method') != method or (target and item.get('handledByClientId') != target):
                raise ValueError('IPC response method or owner mismatch')
            if item.get('resultType') != 'success':
                raise RPCError('IPC request was not acknowledged as successful')
            return item

    def owner(self, thread_id):
        reply = self.request('thread-owner-discovery', {'hostId': 'local', 'conversationId': thread_id})
        return protocol_id(reply.get('handledByClientId'), 'owner')

    def current_state(self, thread_id, owner, expected_cwd):
        """One target, one revision-correlated snapshot; no patch replay/cache.

        The native history method requires an already resumed owner and returns
        its stream revision. It does not resume/start a turn. Following again
        requests a full snapshot at that revision or newer; earlier snapshots
        consumed during the RPC are discarded. Only the small projection leaves
        this function. Disconnect also removes the temporary follower.
        """
        deadline = time.monotonic() + self.timeout
        def following(value, until):
            self.write_frame(dict(type='broadcast', method='thread-stream-following-changed',
                version=METHODS['thread-stream-following-changed'], sourceClientId=self.client_id,
                targetClientIds=[owner], params=dict(conversationId=thread_id, hostId='local', following=value)), until)
        try:
            following(True, deadline)
            reply = self.request('thread-follower-load-complete-history', {'conversationId': thread_id},
                                 target=owner, deadline=deadline)
            revision = protocol_object(reply.get('result'), 'history.result').get('revision')
            if type(revision) is not int or revision < 0:
                raise RPCError('missing current stream revision')
            following(True, deadline)
            while True:
                item = self.read_frame(deadline)
                if (item.get('type') != 'broadcast' or item.get('method') != 'thread-stream-state-changed'
                        or item.get('version') != METHODS['thread-stream-state-changed']
                        or item.get('sourceClientId') != owner
                        or not isinstance(item.get('targetClientIds'), list)
                        or self.client_id not in item['targetClientIds']):
                    continue
                p = protocol_object(item.get('params'), 'snapshot.params')
                if p.get('conversationId') != thread_id or p.get('hostId') != 'local':
                    continue
                change = protocol_object(p.get('change'), 'snapshot.change')
                current_revision = change.get('revision')
                if (change.get('type') != 'snapshot' or type(current_revision) is not int
                        or current_revision < revision):
                    continue
                state = protocol_object(change.get('conversationState'), 'snapshot.state')
                norm = lambda p: os.path.normcase(os.path.normpath(p))
                if (state.get('id') != thread_id or not isinstance(state.get('cwd'), str)
                        or norm(state['cwd']) != norm(expected_cwd)):
                    raise RPCError('native snapshot identity or cwd mismatch')
                runtime = state.get('threadRuntimeStatus')
                status = runtime.get('type') if isinstance(runtime, dict) else None
                status = {'active': 'busy', 'idle': 'idle'}.get(status, 'unknown') if isinstance(status, str) else 'unknown'
                if state.get('resumeState') != 'resumed':
                    status = 'unknown'
                return dict(status=status, owner_id=owner, thread_id=thread_id, cwd=state['cwd'],
                            revision=current_revision, requested_revision=revision, request_id=reply['requestId'])
        finally:
            try:
                following(False, time.monotonic() + min(self.timeout, 1))
            except (OSError, TimeoutError, EOFError):
                pass  # Adapter.close disconnects; do not mask the primary result.

    def close(self):
        self.pipe.close()


class DesktopAdapter:
    def __init__(self, c, paused, client_factory=None):
        self.c, self.paused = c, paused
        self.client_factory, self.client = client_factory or IPCClient, None

    def scan(self, **kwargs):
        return rollout_state(self.c['rollout_path'], self.c['thread_id'], self.c['expected_cwd'], **kwargs)

    def inspect(self, row):
        if row.get('state', 'ready') != 'ready':
            return {'can_send': False, 'reason': 'receipt_only'}
        stage = 'initialize'
        try:
            self.client = self.client_factory(self.c['rpc_timeout_seconds'])
            stage = 'owner_discovery'
            self.owner_id = self.client.owner(self.c['thread_id'])
            stage = 'current_state'
            self.native = self.client.current_state(self.c['thread_id'], self.owner_id, self.c['expected_cwd'])
            self.current = self.scan(lifecycle=False)
        except (OSError, ValueError, RPCError, TimeoutError, EOFError, KeyError, subprocess.SubprocessError) as error:
            failure = ipc_failure(error, stage)
            if failure.stage in ('owner_discovery', 'current_state') and failure.category == 'owner_unavailable':
                return {'can_send': False, 'reason': 'waiting_owner'}
            raise failure from None
        return {'can_send': self.native['status'] == 'idle', 'reason': 'waiting_owner_' + self.native['status']}

    def observe(self, row):
        if row['state'] == 'ready' or not row.get('dispatch_meta') or not row.get('dispatch_text'):
            return None
        meta = json.loads(row['dispatch_meta'])
        # An old lifecycle gap is irrelevant after a verified immutable baseline.
        # Replacement/rewrites and new ambiguous lifecycle still fail closed.
        candidates = self.scan(baseline=meta['baseline'])['turns']
        if row.get('turn_id'):
            turn = candidates.get(row['turn_id'])
            if turn:
                return dict(state=turn['state'], turn_id=row['turn_id'], detail='native accepted turn observed in target rollout')
            return dict(state='accepted', turn_id=row['turn_id'], detail='native acceptance retained; lifecycle not visible yet')
        matches = []
        for key, turn in candidates.items():
            for record in turn['records']:
                p = record.get('payload', {})
                content = p.get('content', [])
                if (record.get('type') == 'response_item' and p.get('type') == 'message' and p.get('role') == 'user'
                        and len(content) == 1 and content[0].get('type') == 'input_text'
                        and content[0].get('text') == row['dispatch_text']):
                    matches.append((key, turn))
        if len(matches) == 1:
            key, turn = matches[0]
            return dict(state=turn['state'], turn_id=key, detail='exact post-intent text fallback; not authenticated provenance')
        return None

    def prepare(self, row):
        if self.native['status'] != 'idle':
            raise NotDispatched('waiting_owner_' + self.native['status'])
        return {'baseline': self.current['baseline'], 'native_current': self.native,
                'settings': self.current['settings'], 'owner_id': self.owner_id,
                'source_client_id': self.client.client_id, 'request_id': str(uuid.uuid4()),
                'installation': self.client.installation}

    def send(self, row, text, metadata):
        # No atomic Desktop idle-CAS exists. Narrow, record and disclose the
        # residual concurrent-writer race; never steer an observed busy target.
        try:
            if self.client.owner(self.c['thread_id']) != metadata['owner_id']:
                raise NotDispatched('waiting_owner_changed')
            native = self.client.current_state(self.c['thread_id'], metadata['owner_id'], self.c['expected_cwd'])
            current = self.scan(lifecycle=False)
        except (OSError, ValueError, RPCError, TimeoutError, EOFError, KeyError) as error:
            # Only read-only requests have happened here. The start write below
            # deliberately remains outside this conversion (uncertain on error).
            raise NotDispatched('waiting_owner_unverified') from error
        if native['status'] != 'idle' or current['baseline'] != metadata['baseline']:
            raise NotDispatched('waiting_owner_changed')
        if self.paused():
            raise NotDispatched('paused')
        reply = self.client.request('thread-follower-start-turn', start_params(self.c['thread_id'], row['client_id'], text),
                                    target=metadata['owner_id'], request_id=metadata['request_id'])
        result = protocol_object(protocol_object(reply, 'start.reply').get('result'), 'start.result')
        native = protocol_object(result.get('result'), 'start.native')
        turn_id = protocol_id(protocol_object(native.get('turn'), 'start.turn').get('id'), 'turn.id')
        return dict(state='accepted', turn_id=turn_id, detail='native IPC accepted; lifecycle and business delivery pending')

    def close(self):
        if self.client is not None:
            self.client.close()
