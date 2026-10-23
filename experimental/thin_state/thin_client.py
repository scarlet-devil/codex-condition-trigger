"""Copy-test caller. No transport factory, live CLI or production adapter import.

A future live entry must verify the reviewed installation and original pipe/process
identity BEFORE calling this helper. A supplied pipe alone is not that proof.
"""
import json
import ntpath
import struct
import time
import uuid


def _identifier(value):
    if not isinstance(value, str) or not value or len(value) > 256 or any(ord(c) < 32 for c in value):
        raise ValueError('invalid identifier')
    return value


def _cwd(value):
    if not isinstance(value, str) or not value or len(value) > 8192 or any(ord(c) < 32 for c in value):
        raise ValueError('invalid cwd')
    if value.startswith('\\\\?\\UNC\\'):
        value = '\\\\' + value[8:]
    elif value.startswith('\\\\?\\'):
        value = value[4:]
    if not ntpath.isabs(value) or not ntpath.splitdrive(value)[0]:
        raise ValueError('cwd is not absolute')
    return ntpath.normcase(ntpath.normpath(value))


def query_status(pipe, *, thread_id, owner_id, expected_cwd, enabled=False, clock=time.monotonic):
    """Consume and close an already verified pipe; one initialize + one status RPC.

    No retry, discovery, follow, history, resume, send, installation bypass or ACK.
    Idle remains an observation; this candidate never grants can_send.
    """
    if enabled is not True:
        raise ValueError('thin-state experiment disabled')
    deadline = clock() + 10.0
    received = 0
    client_id = 'initializing-client'

    def check():
        if clock() >= deadline:
            raise TimeoutError('shared IPC deadline')

    def read_exact(size):
        nonlocal received
        check()
        if received + size > 1048576:
            raise ValueError('cumulative receive limit')
        result = pipe.read(size, deadline)
        received += len(result)
        check()
        if len(result) != size:
            raise EOFError('truncated frame')
        return result

    def rpc(method, params, target=None):
        check()
        request_id = str(uuid.uuid4())
        request = {'type': 'request', 'method': method, 'version': 1, 'requestId': request_id,
                   'sourceClientId': client_id, 'params': params,
                   'timeoutMs': max(1, int((deadline-clock())*1000))}
        if target is not None:
            request['targetClientId'] = target
            # Native je/Me use version+1 when hostId is explicit. Local v1 omits it.
        data = json.dumps(request, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        if len(data) > 65536:
            raise ValueError('request limit')
        check()
        pipe.write(struct.pack('<I', len(data)) + data, deadline)
        while True:
            size, = struct.unpack('<I', read_exact(4))
            if not 0 < size <= 65536:
                raise ValueError('frame limit')
            item = json.loads(read_exact(size))
            check()
            if not isinstance(item, dict):
                raise TypeError('invalid envelope')
            if item.get('type') != 'response' or item.get('requestId') != request_id:
                continue
            if item.get('resultType') != 'success':
                raise ValueError('thin-state unavailable or unsupported')
            if item.get('method') != method or (target and item.get('handledByClientId') != target):
                raise ValueError('method or owner mismatch')
            result = item.get('result')
            if not isinstance(result, dict):
                raise TypeError('invalid result')
            return result

    try:
        _identifier(thread_id)
        _identifier(owner_id)
        wanted_cwd = _cwd(expected_cwd)
        client_id = _identifier(rpc('initialize', {'clientType': 'farfield'}).get('clientId'))
        check()
        budget = max(1, min(9000, int((deadline-clock())*1000)))
        value = rpc('thread-follower-read-thread-status',
                    {'conversationId': thread_id, 'budgetMs': budget}, owner_id)
        generation = value.get('connectionGeneration')
        if (set(value) != {'schema', 'hostId', 'threadId', 'cwd', 'status', 'connectionGeneration'}
                or type(value.get('schema')) is not int or value['schema'] != 1
                or value.get('hostId') != 'local' or value.get('threadId') != thread_id
                or _cwd(value.get('cwd')) != wanted_cwd or type(generation) is not int or generation < 0
                or value.get('status') not in ('idle', 'active', 'notLoaded', 'systemError')):
            raise ValueError('native identity or status mismatch')
        check()
        observation = {'idle': 'idle', 'active': 'busy', 'notLoaded': 'waiting_connection',
                       'systemError': 'unknown'}[value['status']]
        return dict(value, observation=observation, can_send=False, owner_id=owner_id,
                    received_bytes=received, freshness='one_current_summary_same_owner_and_connection')
    finally:
        pipe.close()
