"""Bounded, read-only measurement of the existing full-snapshot IPC path.

No CLI, pipe discovery, model requests, installation changes or production hooks.
The Windows caller supplies one accurately bound target and owns the experiment.
Only aggregate sizes/timings and a small state projection leave this function.
"""
import json
import struct
import subprocess
import time

import desktop_ipc as ipc

FRAME_CAP = ipc.MAX_FRAME  # Preserve the production 32 MiB body limit.
RX_CAP = 128 * 1024 * 1024  # Includes headers and unrelated frames.
IPC_SECONDS = 10
ARCHIVE_SHA256 = 'a05dfd86ca508148c83c25590639cf91a52c6647733cdf200723d85357052b49'
REQUESTS = frozenset(('initialize', 'thread-owner-discovery',
                      'thread-follower-load-complete-history'))
FOLLOW = 'thread-stream-following-changed'


class ProbeFailure(ValueError):
    """Codes are generated locally; remote error text is never exported."""


class SnapshotMeter(ipc.IPCClient):
    def __init__(self, pipe, installation, thread_id, *, rx_cap=RX_CAP,
                 frame_cap=FRAME_CAP, seconds=IPC_SECONDS):
        if (type(rx_cap) is not int or not 4 <= rx_cap <= RX_CAP
                or type(frame_cap) is not int or not 1 <= frame_cap <= FRAME_CAP
                or type(seconds) not in (int, float) or not 0 < seconds <= IPC_SECONDS):
            raise ValueError('invalid_probe_budget')
        self.thread_id = ipc.protocol_id(thread_id, 'thread')
        self.rx_cap, self.frame_cap = rx_cap, frame_cap
        self.started = time.monotonic()
        self.deadline = self.started + seconds
        self.metrics = {
            'read_budget_debited_bytes': 0, 'completed_read_bytes': 0,
            'completed_write_bytes': 0, 'frame_headers': 0, 'complete_bodies': 0,
            'max_declared_body_bytes': 0, 'target_snapshot_bodies': 0,
            'max_target_snapshot_body_bytes': 0, 'incomplete_io': False}
        super().__init__(seconds, pipe=pipe, verifier=lambda _: installation)

    def bounded_deadline(self, supplied):
        deadline = min(supplied, self.deadline)
        if time.monotonic() >= deadline:
            raise TimeoutError('probe_deadline')
        return deadline

    def write_frame(self, item, deadline, before_write=None):
        if before_write is not None:
            raise ProbeFailure('callback_not_supported')
        method, kind = item.get('method'), item.get('type')
        if not ((kind == 'request' and method in REQUESTS)
                or (kind == 'broadcast' and method == FOLLOW)):
            raise ProbeFailure('method_not_allowed')
        params = ipc.protocol_object(item.get('params'), 'params')
        if method != 'initialize' and params.get('conversationId') != self.thread_id:
            raise ProbeFailure('wrong_request_target')
        if method == FOLLOW and type(params.get('following')) is not bool:
            raise ProbeFailure('invalid_subscription')
        deadline = self.bounded_deadline(deadline)
        item = dict(item)
        if kind == 'request':
            item['timeoutMs'] = max(1, int((deadline - time.monotonic()) * 1000))
        data = json.dumps(item, ensure_ascii=False, separators=(',', ':')).encode()
        if len(data) > 65536:
            raise ProbeFailure('request_too_large')
        frame = struct.pack('<I', len(data)) + data
        try:
            self.pipe.write(frame, deadline)
        except BaseException:
            self.metrics['incomplete_io'] = True
            raise
        self.metrics['completed_write_bytes'] += len(frame)
        self.bounded_deadline(deadline)

    def read_exact(self, size, deadline):
        deadline = self.bounded_deadline(deadline)
        if self.metrics['read_budget_debited_bytes'] + size > self.rx_cap:
            raise ProbeFailure('cumulative_receive_limit')
        # Reserve before I/O, even when a failed low-level read's partial bytes
        # are unknowable. Completed bytes are therefore not claimed as wire totals.
        self.metrics['read_budget_debited_bytes'] += size
        try:
            data = self.pipe.read(size, deadline)
            self.metrics['completed_read_bytes'] += len(data)
            if len(data) != size:
                raise EOFError()
        except BaseException:
            self.metrics['incomplete_io'] = True
            raise
        self.bounded_deadline(deadline)
        return data

    def read_frame(self, deadline):
        size, = struct.unpack('<I', self.read_exact(4, deadline))
        self.metrics['frame_headers'] += 1
        self.metrics['max_declared_body_bytes'] = max(self.metrics['max_declared_body_bytes'], size)
        if not 0 < size <= self.frame_cap:
            raise ProbeFailure('single_frame_limit')
        raw = self.read_exact(size, deadline)
        self.metrics['complete_bodies'] += 1
        item = ipc.protocol_object(json.loads(raw), 'frame')
        params = item.get('params')
        if (item.get('type') == 'broadcast' and item.get('method') == 'thread-stream-state-changed'
                and isinstance(params, dict) and params.get('conversationId') == self.thread_id
                and isinstance(params.get('change'), dict) and params['change'].get('type') == 'snapshot'):
            # This measures target-labelled frames, not proof of valid ownership
            # or freshness; inherited current_state performs those checks.
            self.metrics['target_snapshot_bodies'] += 1
            self.metrics['max_target_snapshot_body_bytes'] = max(
                self.metrics['max_target_snapshot_body_bytes'], size)
        self.bounded_deadline(deadline)
        return item


def measure_snapshot(pipe, thread_id, expected_cwd, *, verifier=ipc.verify_installation):
    """Take one sample on a supplied pipe and close it; always can_send=False.

    The caller first checks the selected catalog/rollout identity. Installation
    verification precedes the shared IPC deadline and is timed separately. Its
    existing signature/hash work is NOT a strict 10-second end-to-end guarantee.
    """
    result = {'snapshot_query_completed': False, 'runtime_status': 'unknown',
              'can_send': False, 'model_sends': 0, 'frame_cap_bytes': FRAME_CAP,
              'cumulative_receive_cap_bytes': RX_CAP, 'ipc_budget_seconds': IPC_SECONDS}
    began = time.monotonic()
    client = None
    stage = 'installation'
    try:
        ipc.protocol_id(thread_id, 'thread')
        ipc.protocol_id(expected_cwd, 'cwd')
        installation = ipc.protocol_object(verifier(pipe), 'installation')
        if installation.get('archive_sha256') != ARCHIVE_SHA256:
            raise ProbeFailure('installation_changed')
        result['installation_verified'] = True
        result['verification_seconds'] = time.monotonic() - began
        stage = 'initialize'
        client = SnapshotMeter.__new__(SnapshotMeter)
        client.__init__(pipe, installation, thread_id)
        stage = 'owner_discovery'
        owner = client.owner(thread_id)
        stage = 'current_state'
        state = client.current_state(thread_id, owner, expected_cwd)
        stage = 'owner_recheck'
        if client.owner(thread_id) != owner:
            raise ProbeFailure('owner_changed')
        result.update(snapshot_query_completed=True, runtime_status=state['status'],
                      revision=state['revision'], requested_revision=state['requested_revision'],
                      owner_same_after=True)
    except (OSError, ValueError, ipc.RPCError, EOFError, TypeError, KeyError,
            subprocess.SubprocessError, RecursionError) as error:
        result['error_stage'] = stage
        result['error_category'] = (str(error) if type(error) is ProbeFailure
                                    else ipc.ipc_failure(error, stage).category)
    finally:
        try:
            pipe.close()
        except (OSError, ValueError):
            result.update(snapshot_query_completed=False, runtime_status='unknown',
                          cleanup_failed=True)
        finally:
            if client is not None and hasattr(client, 'metrics'):
                result['measurements'] = dict(client.metrics)
                result['ipc_seconds'] = time.monotonic() - client.started
            result['total_seconds'] = time.monotonic() - began
    return result
