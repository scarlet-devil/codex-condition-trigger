"""Two real synthetic turns under a single bounded watcher; no manual dispatch.

The one first-batch claim_open is a labelled backend probe on an already-loaded
target. All model dispatches are from the unmodified candidate watch loop.
"""
from pathlib import Path
import sys,json,time,threading,hashlib,sqlite3,traceback,uuid
from datetime import datetime,timezone
R=Path(__file__).parent;sys.path.insert(0,str(R/'repo'))
import trigger as tr
import desktop_ipc as ipc
from owner_loading import WindowCycles,CommandBackend
from watchdog.events import FileSystemEventHandler
c=tr.load_config(R/'config.json')
sha=lambda b:hashlib.sha256(b).hexdigest()
stamp=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_bytes())
initial=read(R/'initial-file-hashes.json')
assert len(read(R/'governance-verification-v08.json')['checks'])==17
assert all(x['passed'] for x in read(R/'governance-verification-v08.json')['checks'])
for key in ('business_state','hooks','binding','automation'):
    assert sha(Path(initial[key]['path']).read_bytes())==initial[key]['sha256'],key
assert (R/'state/STOP').exists()
assert not list((R/'inbox').iterdir())
assert 0<c['window_backend_options']['supervised_no_navigation_until']-time.time()<=600
(R/'trial-start-guard').open('xb').close()
start=time.monotonic();stop=threading.Event();watching=threading.Event();lock=threading.RLock()
out={'started_at':stamp(),'manual_dispatch_calls':0,'start_requests':[], 'events':[], 'window_calls':[],
     'filesystem_events':[], 'current_queries':[], 'receipts':[], 'errors':[], 'probe_reason':'explicit loaded-target backend validation'}
def save():
    with lock:
        tr.atomic_write(R/'cycle-trace.private.json',(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
def event():return {'at':stamp(),'elapsed_seconds':round(time.monotonic()-start,4)}
def halt(reason):
    out['stop_reason']=reason;(R/'state/STOP').touch();stop.set();save()
original_call=CommandBackend.call
def backend_call(self,action,**values):
    record=dict(event(),action=action)
    with lock:out['window_calls'].append(record);save()
    try:
        result=original_call(self,action,**values)
        record.update(finished_at=stamp(),result=result);save();return result
    except Exception as e:
        record.update(error_type=type(e).__name__)
        if hasattr(e,'stdout') and e.stdout:record['stdout']=e.stdout.decode('utf-8',errors='replace')
        if hasattr(e,'stderr') and e.stderr:record['stderr']=e.stderr.decode('utf-8',errors='replace')
        save();raise
CommandBackend.call=backend_call
original_emit=tr.emit
def emit(kind,**values):
    with lock:out['events'].append(dict(event(),event=kind,**values));save()
    if kind=='watching':watching.set()
    if kind=='cycle_tick' and values.get('state') in ('window_open_unknown','window_close_unknown','window_identity_unconfirmed','window_reconciliation_required','owner_check_failed'):
        halt(values['state'])
    if kind=='batch_ready' and len(store.rows())==1:
        manager=WindowCycles(store)
        row=store.rows()[0]
        inspected=manager.inspect_owner(row)
        assert inspected['can_send'], 'direct backend probe requires genuinely idle owner'
        result=manager.claim_open(row)
        out['direct_backend_probe']=dict(event(),result=result)
        save()
        if result!='owner_ready':halt('backend_probe:'+result)
    original_emit(kind,**values)
tr.emit=emit
original_event=FileSystemEventHandler.dispatch
def on_event(self,e):
    if e.event_type in ('created','modified','moved','deleted'):
        with lock:out['filesystem_events'].append(dict(event(),type=e.event_type,name=Path(e.src_path).name));save()
    return original_event(self,e)
FileSystemEventHandler.dispatch=on_event
original_write=ipc.IPCClient.write_frame
def write(self,item,deadline):
    if item['method']=='thread-follower-start-turn':
        assert not stop.is_set() and not store.paused()
        rows=[r for r in store.rows() if r['state']=='sending'];assert len(rows)==1
        row=rows[0]; request=item['params']['turnStart']['request']
        assert item['params']['conversationId']==c['thread_id'] and not item['params']['isSteering']
        assert set(request)=={'threadId','clientUserMessageId','input','additionalContext'}
        assert request['input'][0]['text']==row['dispatch_text'] and request['clientUserMessageId']==row['client_id']
        assert len(out['start_requests'])<2
        (R/('send-guard-'+row['id'])).open('xb').close()
        backup=sqlite3.connect(R/('pre-send-'+row['id']+'.sqlite'));store.db.backup(backup);backup.close()
        with lock:out['start_requests'].append(dict(event(),batch_id=row['id'],request_sha256=sha(json.dumps(item,sort_keys=True).encode())));save()
    return original_write(self,item,deadline)
ipc.IPCClient.write_frame=write
original_current=ipc.IPCClient.current_state
def current(self,*args,**kwargs):
    value=original_current(self,*args,**kwargs)
    with lock:out['current_queries'].append(dict(event(),state=value));save()
    return value
ipc.IPCClient.current_state=current
expected={}
def inject(number):
    payload={'marker':'window-cycle-'+str(number)+'-'+str(uuid.uuid4()),'left':173+number,'right':284+number}
    data=(json.dumps(payload,sort_keys=True)+'\n').encode()
    expected[payload['marker']]=dict(payload,result=payload['left']+payload['right'],sha256=sha(data),bytes=len(data))
    tr.atomic_write(R/'expected.private.json',(json.dumps(expected,indent=2)+'\n').encode())
    with (R/'inbox/synthetic.json').open('wb') as f:f.write(data);f.flush()
    with lock:out.setdefault('input_writes',[]).append(dict(event(),number=number,sha256=sha(data)));save()
def verify(row):
    meta=json.loads(row['dispatch_meta'])
    parsed=ipc.rollout_state(Path(c['rollout_path']),c['thread_id'],c['expected_cwd'],baseline=meta['baseline'])
    turn=parsed['turns'][row['turn_id']];assert turn['state']=='completed'
    records=turn['records'];ps=[r.get('payload',{}) for r in records]
    final=[p for p in ps if p.get('type')=='message' and p.get('role')=='assistant' and p.get('phase')=='final_answer']
    assert len(final)==1
    value=json.loads(''.join(x.get('text','') for x in final[0]['content']))
    e=expected[value['marker']]
    assert all(value[k]==e[k] for k in ('marker','left','right','result'))
    manifest_bytes=(R/'state/batches'/f'{row["id"]}.json').read_bytes();m=json.loads(manifest_bytes)
    assert m['batch_id']==row['id'] and m['thread_id']==c['thread_id'] and len(m['files'])==1
    assert m['files'][0]['sha256']==e['sha256'] and m['files'][0]['size']==e['bytes']
    blob=(Path(m['blob_dir'])/e['sha256']).read_bytes()
    assert sha(blob)==e['sha256'] and len(blob)==e['bytes']
    assert value['blob_sha256'].lower()==sha(blob) and value['blob_bytes']==len(blob)
    assert value['manifest_sha256'].lower()==sha(manifest_bytes) and value['manifest_bytes']==len(manifest_bytes)
    calls={p['call_id']:p for p in ps if p.get('type')=='custom_tool_call'}
    outputs=[p for p in ps if p.get('type')=='custom_tool_call_output']
    assert calls and outputs and all(p['call_id'] in calls for p in outputs)
    output_text=json.dumps(outputs,ensure_ascii=False)
    assert value['marker'] in output_text and sha(blob).lower() in output_text.lower() and sha(manifest_bytes).lower() in output_text.lower()
    assert any(p.get('name')=='exec' for p in calls.values())
    contexts=[p for r,p in zip(records,ps) if r['type']=='turn_context']
    assert contexts and all(contexts[0].get(k)==v for k,v in meta['settings'].items())
    assert any(p.get('role')=='user' and any(x.get('text')==row['dispatch_text'] for x in p.get('content',[])) for p in ps)
    assert len([x for x in out['start_requests'] if x['batch_id']==row['id']])==1
    client=ipc.IPCClient(10)
    try:
        native=client.current_state(c['thread_id'],client.owner(c['thread_id']),c['expected_cwd'])
        assert native['status']=='idle'
    finally:client.close()
    raw=R/('turn-'+row['id']+'.private.json')
    tr.atomic_write(raw,(json.dumps({'row':row,'turn':turn,'native':native},ensure_ascii=False,indent=2)+'\n').encode())
    receipt=dict(verified_at=stamp(),kind='caller_verified_synthetic_only',batch_id=row['id'],turn_id=row['turn_id'],
        result=value,actual_tool_calls=len(calls),exact_input_and_hashes=True,settings_inherited=True,
        correlated_completed=True,native_idle=True,manual_dispatch_calls=0,start_requests=1,
        raw_evidence_sha256=sha(raw.read_bytes()),business_delivery=False)
    path=R/('receipt-'+row['id']+'.private.json');tr.atomic_write(path,(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode())
    return path,receipt
def supervise():
    observer=None
    try:
        assert watching.wait(15)
        observer=tr.Store(c,worker=False)
        if stop.wait(5):return
        inject(1);injected=1
        while not stop.wait(.5):
            assert time.monotonic()-start<420,'supervised deadline'
            rows=observer.rows();assert len(rows)<=2
            for row in rows:
                if row['state'] in ('failed','blocked','uncertain'):raise RuntimeError('terminal:'+row['state'])
                if row['state']=='completed':
                    path,receipt=verify(row)
                    observer.acknowledge(row['id'],path)
                    with lock:out['receipts'].append(receipt);save()
            cycles=[json.loads(r[0]) for r in observer.db.execute("SELECT v FROM meta WHERE k LIKE 'window_cycle:%'")]
            if len(rows)==injected and all(r['state']=='delivered' for r in observer.rows()) and len(cycles)==len(rows) and all(x['phase']=='closed' for x in cycles):
                if injected==1:inject(2);injected=2
                else:halt('two_verified_cycles_closed');break
    except BaseException:
        out['errors'].append(traceback.format_exc());halt('supervisor_failed')
    finally:
        if observer:observer.close()
store=tr.Store(c)
try:
    assert store.rows()==[]
    (R/'state/STOP').unlink() # Only this newly prepared, bounded trial state.
    supervisor=threading.Thread(target=supervise,daemon=True);supervisor.start()
    tr.run(store,live=True,stop_event=stop)
except BaseException:
    out['errors'].append(traceback.format_exc());halt('worker_failed')
finally:
    stop.set();(R/'state/STOP').touch()
    if 'supervisor' in globals():supervisor.join(timeout=15)
    out.update(finished_at=stamp(),elapsed_seconds=round(time.monotonic()-start,3),rows=store.rows(),cycles=WindowCycles(store).records())
    store.close();save()
    print(json.dumps({'stop_reason':out.get('stop_reason'),'sends':len(out['start_requests']),'receipts':len(out['receipts']),'errors':len(out['errors']),'elapsed':out['elapsed_seconds']},ensure_ascii=False))
