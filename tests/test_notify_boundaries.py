"""Failure boundaries using real SQLite transactions and synthetic native IPC."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from unittest import mock

import desktop_ipc as ipc
import notify_state as ns
from test_notify import NotifyFixture
import trigger as tr


class Boundaries(NotifyFixture):
    def test_strict_and_notify_cannot_dispatch_same_target_from_two_states(self):
        self.open();self.batch('A')
        other=dict(self.config,dispatch_mode='verified_delivery',state_dir=str(self.root/'strict'))
        with self.assertRaises((RuntimeError,ValueError)):
            candidate=tr.Store(other);candidate.close()
        self.store.close()
        # The notify rule remains enabled even after the worker exits.
        with self.assertRaises(ValueError):
            candidate=tr.Store(other);candidate.close()

    def test_rule_instruction_edit_requires_a_new_bound_revision(self):
        self.open();self.batch('A');self.store.close()
        changed=dict(self.config,task_instruction='different instruction')
        with self.assertRaises(ValueError):
            candidate=tr.Store(changed);candidate.close()

    def test_each_terminal_binding_is_required(self):
        self.open();a=self.batch('A');self.tick();self.batch('B');self.finish()
        row=self.store.rows()[0];receipt=self.fake.observe(row)
        for key in receipt['notify_evidence']:
            with self.subTest(key=key):
                bad=copy.deepcopy(receipt);bad['notify_evidence'].pop(key)
                self.assertEqual(ns.commit(self.store,a,bad),'needs_reconciliation')
                self.assertEqual(ns.pending(self.store)[0]['id'],a)
        for state in ('queued','completed','ended','failed'):
            with self.subTest(state=state):
                bad=dict(state=state,turn_id='wrong')
                ns.commit(self.store,a,bad)
                self.assertIsNone(self.store.db.execute('SELECT terminal FROM notifications WHERE batch_id=?',(a,)).fetchone()[0])

    def test_crash_before_acceptance_commit_has_no_partial_proof(self):
        self.open();a=self.batch('A')
        self.store.db.execute("CREATE TRIGGER fail_receipt BEFORE UPDATE ON batches WHEN NEW.state='accepted' BEGIN SELECT RAISE(ABORT,'crash'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.tick()
        self.assertEqual(self.fake.sent,[a])
        self.assertIsNone(self.store.db.execute('SELECT acceptance FROM notifications').fetchone()[0])
        self.store.close();self.store=tr.Store(self.config)
        self.assertEqual(self.store.rows()[0]['state'],'uncertain')
        self.tick();self.assertEqual(self.fake.sent,[a])

    def test_known_not_written_can_retry(self):
        self.open();a=self.batch('A');self.fake.before_write=True
        self.assertEqual(self.tick(),'known_no_write')
        self.assertEqual(self.store.rows()[0]['state'],'ready')
        self.fake.before_write=False;self.tick();self.assertEqual(self.fake.sent,[a])

    def test_terminal_duplicate_and_late_running_preserve_outcome(self):
        self.open();a=self.batch('A');self.tick();self.finish('failed');self.tick()
        row=self.store.rows()[0]
        ns.commit(self.store,a,dict(state='running',turn_id=row['turn_id']))
        self.assertEqual(self.store.rows()[0]['execution_outcome'],'failed')
        self.assertEqual(self.store.rows()[0]['state'],'failed')

    def test_verified_ack_is_not_overwritten_by_native_observation(self):
        self.open();a=self.batch('A');self.tick();self.finish()
        receipt=self.root/'ack.json';receipt.write_text('{"verified":true}')
        self.store.acknowledge(a,receipt)
        before=dict(self.store.rows()[0])
        self.tick()
        after=self.store.rows()[0]
        self.assertEqual(after['state'],'delivered')
        self.assertEqual(after['detail'],before['detail'])

    def test_another_process_cannot_own_same_target(self):
        self.open()
        c=dict(self.config,state_dir=str(self.root/'second'))
        config=self.root/'child.json';config.write_text(json.dumps(c))
        code="import json,sys,pathlib;sys.path.insert(0,sys.argv[1]);import trigger as t;t.target_registry_root=lambda:pathlib.Path(sys.argv[3]);s=t.Store(json.load(open(sys.argv[2])));s.close()"
        result=subprocess.run([sys.executable,'-B','-c',code,str(Path(tr.__file__).parent),str(config),str(self.root/'registry')],capture_output=True,timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'another command owns',result.stderr)

    def test_old_program_rejects_notify_state_without_mutation(self):
        self.open();self.batch('A');self.store.close()
        path=Path(__file__).parent/'fixtures'/'legacy_trigger_db69330f.py'
        expected=json.loads((path.with_suffix('.json')).read_text())['sha256']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),expected)
        spec=importlib.util.spec_from_file_location('legacy_trigger',path)
        legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
        db=Path(self.config['state_dir'])/'state.sqlite'
        before=db.read_bytes()
        with self.assertRaisesRegex(ValueError,'different root/thread/cwd'):
            legacy.Store(self.config)
        self.assertEqual(db.read_bytes(),before)

    def test_expiry_blocks_next_batch_even_when_idle(self):
        self.open();a=self.batch('A');self.tick();self.batch('B');self.finish();self.tick()
        with mock.patch.object(self.store,'trial_expired',return_value=True):
            self.assertEqual(self.tick(),'paused')
        self.assertEqual(self.fake.sent,[a]);self.assertEqual(len(ns.pending(self.store)),2)

    def test_monotonic_expiry_is_preserved_after_restart(self):
        self.config['trial_expires_at_utc']=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat()
        self.open();a=self.batch('A');self.tick();self.batch('B');self.finish();self.tick()
        with mock.patch.object(tr.time,'monotonic',return_value=self.store.monotonic_deadline+1):
            self.assertEqual(self.tick(),'paused')
        self.store.close();self.store=tr.Store(self.config)
        self.assertTrue(self.store.paused());self.assertEqual(self.fake.sent,[a])

    def test_idle_boolean_without_fresh_bound_state_cannot_release(self):
        self.open();self.batch('A');self.tick();self.finish();self.tick()
        self.fake.inspect=lambda _:dict(can_send=True,reason='idle')
        self.assertEqual(self.tick(),'needs_fresh_idle_evidence')
        self.assertEqual(len(ns.pending(self.store)),1)


class NativeNotify(NotifyFixture):
    def setUp(self):
        super().setUp()
        self.path=Path(self.config['rollout_path'])
        self.path.write_text(json.dumps(dict(type='session_meta',payload=dict(id=self.config['thread_id'],cwd=self.config['expected_cwd'])))+'\n')
        self.append('event_msg',type='task_started',turn_id='old')
        self.append('event_msg',type='task_complete',turn_id='old')
        self.calls=[];self.lost=False;self.wrong_text=False
        test=self
        class Client:
            client_id,installation='fake-client',{'synthetic':True}
            def owner(self,thread):return 'owner'
            def current_state(self,thread,owner,cwd):
                return dict(status=ipc.rollout_state(test.path,thread,cwd)['status'],revision=1,owner_id=owner,
                    requested_revision=1,thread_id=thread,cwd=cwd,request_id='synthetic-query')
            def request(self,method,params,**kwargs):
                if kwargs.get('before_write',lambda:False)():raise tr.NotDispatched('paused')
                test.calls.append(params);turn='native-'+str(len(test.calls))
                test.append('event_msg',type='task_started',turn_id=turn)
                text=params['turnStart']['request']['input'][0]['text']
                test.append('response_item',type='message',role='user',content=[dict(type='input_text',text='wrong' if test.wrong_text else text)])
                if test.lost:raise TimeoutError('native response lost')
                return dict(result=dict(result=dict(turn=dict(id=turn))))
            def close(self):pass
        self.client=Client

    def append(self,kind,**payload):
        with self.path.open('a') as f:f.write(json.dumps(dict(type=kind,payload=payload))+'\n')

    def native_tick(self):
        from owner_loading import cycle_tick
        return cycle_tick(self.store,adapter_factory=lambda c,p:ipc.DesktopAdapter(c,p,lambda _:self.client()))

    def test_real_adapter_releases_exact_turn_and_sends_second(self):
        self.open();self.batch('A');self.assertEqual(self.native_tick(),'accepted');self.batch('B')
        self.native_tick();self.assertEqual(len(self.calls),1)
        self.append('event_msg',type='task_complete',turn_id='native-1')
        for _ in range(4):self.native_tick()
        self.assertEqual(len(self.calls),2)
        self.assertEqual(self.store.rows()[0]['state'],'ended')
        self.assertEqual(self.store.rows()[0]['execution_outcome'],'unknown')

    def test_lost_native_receipt_does_not_use_text_fallback(self):
        self.open();self.batch('A');self.lost=True;self.native_tick();self.batch('B')
        self.append('event_msg',type='task_complete',turn_id='native-1')
        for _ in range(3):self.native_tick()
        self.assertEqual(len(self.calls),1);self.assertEqual(self.store.rows()[0]['state'],'uncertain')

    def test_wrong_full_text_never_releases_known_native_turn(self):
        self.open();self.batch('A');self.wrong_text=True;self.native_tick();self.batch('B')
        self.append('event_msg',type='task_complete',turn_id='native-1')
        for _ in range(3):self.native_tick()
        self.assertEqual(len(self.calls),1);self.assertEqual(len(ns.pending(self.store)),2)
