"""G1 Python API. No GUI, background service, automatic scheduling or model call."""
import copy
import json
from pathlib import Path
import uuid

from simple_catalog import verify_selection
from notify_state import initialize, pause_epoch, set_active, status as notification_status, validate_files
import trigger as tr

PRESETS = ('new_content_stable','ready_content_stable')


def preview(folder, condition, selection, *, state_dir=None, instruction=None, identity_reader=None, **advanced):
    """Selection comes from the bounded catalog, not a display-name lookup."""
    if condition not in PRESETS or selection.get('selection_key') != selection.get('id'):
        raise ValueError('invalid condition or catalog binding')
    allowed = {'initial_files','settle_seconds','max_pending_batches','max_state_bytes','trial_expires_at_utc'}
    if set(advanced)-allowed:
        raise ValueError('unsupported rule override')
    identity = str(uuid.UUID(selection['id']))
    verify_selection(selection, reader=identity_reader)
    rule_id = uuid.uuid4().hex
    c=json.loads((Path(__file__).parent/'example.windows.json').read_text(encoding='utf-8'))
    c.update(input_dir=folder,state_dir=state_dir or str(tr.target_registry_root()/'rules'/rule_id),
             thread_id=identity,expected_cwd=selection['cwd'],rollout_path=selection['rollout_path'],
             dispatch_mode='notify',rule_schema=2,rule_id=rule_id,rule_revision=1,
             chat_adapter='desktop_ipc',initial_files='ignore',max_pending_batches=100,
             max_state_bytes=1024**3,ready_file='READY' if condition=='ready_content_stable' else None)
    c.update(advanced)
    if instruction is not None:
        c['task_instruction']=instruction
    c=tr.validate_config(c)
    files=tr.snapshot(c,require_ready=False)
    validate_files(c,files)
    return dict(config=c,files=len(files),bytes=sum(f['size'] for f in files),
                initial_action=c['initial_files'],target_title=selection.get('display_name','(untitled)'),
                connection_status='not_queried',rule_revision=1)


def enable(config, *, adapter_factory=None, cancelled=lambda: False, _store=None):
    """Explicit action. Real callers perform a read-only native capability probe first."""
    c=tr.validate_config(copy.deepcopy(config))
    if cancelled(): raise ValueError('enable_cancelled')
    store=_store if _store is not None else tr.Store(c)
    try:
        if store.c != c: raise ValueError('enable store binding mismatch')
        expected_pause_epoch=pause_epoch(store)
        if store.db.execute("SELECT 1 FROM meta WHERE k='notify_initialized'").fetchone():
            raise ValueError('already initialized; use resume')
        adapter=(adapter_factory or (lambda c, paused: tr.make_adapter(c,paused)))(c,cancelled)
        try:
            checked=adapter.inspect(dict(state='ready'))
            if not checked['can_send']:
                raise ValueError('initial target capability/idle check did not pass')
        finally:
            adapter.close()
        if cancelled(): raise ValueError('enable_cancelled')
        c['owner_verified']=True
        # A controller supplying its own Store owns the config + marker pair.
        # Do not replace just one half before initialization can still fail.
        if _store is None:tr.atomic_write(store.path/'rule.json',(tr.encode(c)+'\n').encode())
        initialize(store,expected_pause_epoch,cancelled=cancelled)
        return c
    finally:
        if _store is None: store.close()


def pause(config):
    store=tr.Store(copy.deepcopy(config),worker=False)
    try:
        set_active(store,False)
    finally:
        store.close()


def resume(config):
    store=tr.Store(copy.deepcopy(config),worker=False)
    try:
        set_active(store,True)
    finally:
        store.close()


def status(config):
    store=tr.Store(copy.deepcopy(config),worker=False)
    try:
        return notification_status(store)
    finally:
        store.close()
