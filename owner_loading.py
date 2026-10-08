"""Explicit, default-off owner preparation. No window backend is bundled yet.

A reviewed backend must open only the supplied existing chat, honor its timeout,
and verify window identity before minimizing. It receives no task or prompt.
This function never sends a turn and is not called by the watcher/dispatch loop.
"""
import json
import time

from desktop_ipc import DesktopAdapter, IPCFailure


def prepare_owner(store, loader=None, client_factory=None):
    """At most one claimed load per target/state store, even after a crash.

    A failed/unknown action consumes the budget. No automatic reset or replay.
    The caller owns the Store worker lock. Backend availability is intentionally
    separate from enabling the interface; an unavailable backend opens nothing.
    """
    if store.paused():
        return 'paused'
    if not store.c.get('owner_loading_enabled', False):
        return 'loader_disabled'
    if not store.c['owner_verified'] or store.c.get('chat_adapter') != 'desktop_ipc':
        return 'owner_not_verified'
    rows = [r for r in store.rows() if r['state'] != 'delivered']
    if not rows:
        return 'quiet'
    row = rows[0]
    if row['state'] != 'ready' or row.get('dispatch_text') or row.get('dispatch_meta'):
        return 'receipt_only'
    adapter = DesktopAdapter(store.c, store.paused, client_factory)
    try:
        inspection = adapter.inspect(row)  # strictly read-only
        if inspection['reason'] != 'waiting_owner':
            return 'owner_ready' if inspection['can_send'] else inspection['reason']
        if loader is None:
            return 'loader_unavailable'
        if store.paused():
            return 'paused'
        # Claim before the external action. A new file/batch cannot reset it.
        key = 'owner_load_attempt:' + store.c['thread_id']
        with store.db:
            claimed = store.db.execute("INSERT OR IGNORE INTO meta(k,v) "
                "SELECT ?,? WHERE EXISTS (SELECT 1 FROM batches WHERE id=? AND state='ready' "
                "AND dispatch_text IS NULL AND dispatch_meta IS NULL)",
                (key, json.dumps({'claimed_at': time.time(), 'batch_id': row['id']}), row['id']))
        if claimed.rowcount != 1:
            return 'loader_budget_exhausted'
        if store.paused():
            return 'paused'
        try:
            loader(thread_id=store.c['thread_id'], expected_cwd=store.c['expected_cwd'],
                   timeout_seconds=store.c['rpc_timeout_seconds'])
        except Exception:
            return 'loader_failed'  # uncertain window outcome; never replay
        if store.paused():
            return 'paused'
        adapter.close()
        adapter = DesktopAdapter(store.c, store.paused, client_factory)
        inspection = adapter.inspect(row)  # fresh owner + thread/cwd + idle
        return 'owner_ready' if inspection['can_send'] else inspection['reason']
    except IPCFailure:
        return 'owner_check_failed'
    finally:
        adapter.close()
