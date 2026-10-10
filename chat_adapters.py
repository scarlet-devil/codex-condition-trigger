"""Small chat boundary. Core owns intent, retry decisions and delivery ACK."""
import json
import os
import queue
import subprocess
import threading
import time


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


class RPCError(Exception):
    pass


class StdioRPC:
    """JSONL client for a *verified existing-owner proxy*, not a new app-server."""
    def __init__(self, c):
        if not c["transport_command"]:
            raise ValueError("configure the verified existing-owner JSONL proxy command first")
        self.timeout = c["rpc_timeout_seconds"]
        self.serial = 0
        self.inbox = queue.Queue()
        self.child = subprocess.Popen(c["transport_command"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1,
                                      shell=False)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self.request("initialize", {"clientInfo": {"name": "codex_condition_trigger", "version": "0.1.0"},
                                        "capabilities": {"experimentalApi": True}})
            self._write({"method": "initialized"})
        except Exception:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.child.stdout:
                self.inbox.put(json.loads(line))
        except Exception as e:
            self.inbox.put(e)
        finally:
            self.inbox.put(EOFError("proxy closed"))

    def _write(self, message):
        self.child.stdin.write(encode(message) + "\n")
        self.child.stdin.flush()

    def request(self, method, params):
        self.serial += 1
        serial = self.serial
        self._write({"id": serial, "method": method, "params": params})
        end = time.monotonic() + self.timeout
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"RPC timeout: {method}")
            try:
                item = self.inbox.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError(f"RPC timeout: {method}") from None
            if time.monotonic() >= end:
                raise TimeoutError(f"RPC timeout: {method}")
            if isinstance(item, Exception):
                raise item
            if "method" in item:
                if "id" in item:
                    # Never grant permissions or impersonate Desktop-only tools.
                    self._write({"id": item["id"], "error": {"code": -32601,
                                 "message": "trigger does not implement owner tools or approvals"}})
                continue
            if item.get("id") != serial:
                continue
            if "error" in item:
                raise RPCError(encode(item["error"]))
            return item["result"]

    def close(self):
        if self.child.poll() is None:
            self.child.terminate()  # only this proxy child; never its shared owner
            try:
                self.child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.child.kill()
                self.child.wait()
        if self.child.stdin:
            self.child.stdin.close()
        if self.child.stdout:
            self.child.stdout.close()


def read_thread(rpc, c):
    t = rpc.request("thread/read", {"threadId": c["thread_id"], "includeTurns": True})["thread"]
    if t.get("id") != c["thread_id"]:
        raise ValueError("server returned a different thread")
    if os.path.normcase(os.path.normpath(t.get("cwd", ""))) != os.path.normcase(os.path.normpath(c["expected_cwd"])):
        raise ValueError("thread cwd differs from expected_cwd")
    return t


def list_queue(rpc, c):
    result, cursor, seen = [], None, set()
    while True:
        p = {"threadId": c["thread_id"], "limit": 100}
        if cursor:
            p["cursor"] = cursor
        page = rpc.request("thread/queue/list", p)
        result.extend(page["data"])
        cursor = page.get("nextCursor")
        if not cursor:
            return result
        if cursor in seen:
            raise ValueError("repeated queue cursor")
        seen.add(cursor)


def history_match(thread, row):
    # This fallback is exact text correlation, not authenticated provenance.
    # A ready batch or legacy row has no persisted send intent to reconcile.
    if row["state"] not in ("sending", "queued", "running", "uncertain") or not row.get("dispatch_text"):
        return None
    matches = []
    for turn in thread.get("turns", []):
        for item in turn.get("items", []):
            content = item.get("content", [])
            if (item.get("type") == "userMessage" and len(content) == 1
                    and content[0].get("type") == "text"
                    and content[0].get("text") == row["dispatch_text"]):
                matches.append(turn)
    return matches[0] if len(matches) == 1 else None


class NotDispatched(Exception):
    """The adapter proves no start/queue request was written."""


class QueueAdapter:
    def __init__(self, c, paused, rpc_factory=StdioRPC):
        self.c, self.paused = c, paused
        self.rpc = rpc_factory(c)

    def inspect(self, row):
        self.thread = read_thread(self.rpc, self.c)
        self.pending = list_queue(self.rpc, self.c)
        self.existing = next((q for q in self.pending if q.get('clientUserMessageId') == row['client_id']), None)
        return {'can_send': True, 'reason': 'inspected'}

    def observe(self, row):
        turn = history_match(self.thread, row)
        if turn:
            state = {'completed': 'completed', 'failed': 'failed', 'interrupted': 'failed'}.get(turn.get('status'), 'running')
            return dict(state=state, turn_id=turn['id'], detail='matched exact persisted dispatch text')
        if self.existing:
            return dict(state='queued', submission=self.existing['id'], detail='queue readback matched client ID')
        return None

    def prepare(self, row):
        t = self.thread
        status = t.get('status', {}).get('type')
        turns = t.get('turns', [])
        if turns and turns[-1].get('status') == 'interrupted':
            raise NotDispatched('waiting_owner_after_interrupt')
        if status == 'notLoaded':
            if not self.c['resume_unloaded'] or self.pending:
                raise NotDispatched('waiting_owner_resume')
            if self.paused():
                raise NotDispatched('paused')
            self.rpc.request('thread/resume', {'threadId': self.c['thread_id']})
            status = read_thread(self.rpc, self.c).get('status', {}).get('type')
        if status not in ('idle', 'active'):
            raise NotDispatched('waiting_owner')
        return {}

    def send(self, row, text, metadata):
        if self.paused():
            raise NotDispatched('paused')
        reply = self.rpc.request('thread/queue/add', {
            'threadId': self.c['thread_id'], 'input': [{'type': 'text', 'text': text, 'textElements': []}],
            'clientUserMessageId': row['client_id']})['queuedSubmission']
        if reply.get('clientUserMessageId') != row['client_id']:
            raise ValueError('queue response client ID mismatch')
        return dict(state='queued', submission=reply['id'], detail='accepted, not proof of wake or business delivery')

    def close(self):
        self.rpc.close()
