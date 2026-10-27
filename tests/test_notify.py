"""G1 user contracts: real Store/cycle_tick with deterministic fake transport."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import trigger as tr
from owner_loading import cycle_tick


class FakeDesktop:
    """A native receipt/rollout contract fake, never opens Desktop."""
    def __init__(self):
        self.sent = []
        self.turns = {}
        self.idle = True
        self.loss = False
        self.before_write = False

    def factory(self, config, paused):
        self.c, self.paused = config, paused
        return self

    def inspect(self, row):
        return dict(can_send=self.idle, reason='idle' if self.idle else 'waiting_owner_busy',
            fresh_state=dict(status='idle' if self.idle else 'busy',thread_id=self.c['thread_id'],cwd=self.c['expected_cwd'],
                owner_id='synthetic-owner',revision=1,requested_revision=1,request_id='fresh-query'))

    def prepare(self, row):
        return dict(request_id='request-' + row['client_id'],
                    baseline=dict(bytes=10, inode=1, sha256='a'*64))

    def evidence(self, row, metadata, turn, phase):
        return dict(phase=phase, source='native_ipc' if phase=='accepted' else 'native_turn_rollout',
                    thread_id=self.c['thread_id'], cwd=self.c['expected_cwd'],
                    batch_id=row['id'], manifest_sha256=tr.digest((row['manifest']+'\n').encode()),
                    request_id=metadata['request_id'], client_id=row['client_id'], turn_id=turn,
                    baseline=metadata['baseline'], text_sha256=tr.digest(row['dispatch_text'].encode()),
                    exact_text=True, post_intent=True)

    def send(self, row, text, metadata):
        if self.before_write:
            raise tr.NotDispatched('known_no_write')
        self.sent.append(row['id'])
        if self.loss:
            raise TimeoutError('receipt lost')
        turn='turn-'+row['id']
        self.idle=False
        self.turns[turn]=('running','unknown')
        row=dict(row,dispatch_text=text)
        receipt=dict(state='accepted',turn_id=turn,detail='native receipt')
        if self.c.get('dispatch_mode')=='notify':
            receipt['notify_evidence']=self.evidence(row,metadata,turn,'accepted')
        return receipt

    def observe(self,row):
        if row['state']=='ready' or not row.get('turn_id'):
            return None
        state,outcome=self.turns[row['turn_id']]
        receipt=dict(state=state,execution_outcome=outcome,turn_id=row['turn_id'])
        if self.c.get('dispatch_mode')=='notify' and state in ('ended','failed'):
            receipt['notify_evidence']=self.evidence(row,json.loads(row['dispatch_meta']),row['turn_id'],'terminal')
        return receipt

    def close(self):
        pass


class NotifyFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.input=self.root/'input'; self.input.mkdir()
        self.patch=mock.patch.object(tr,'target_registry_root',return_value=self.root/'registry',create=True)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.config=json.loads((Path(__file__).parents[1]/'example.windows.json').read_bytes())
        self.config.update(input_dir=str(self.input),state_dir=str(self.root/'state'),expected_cwd=str(self.root),
            chat_adapter='desktop_ipc',rollout_path=str(self.root/'rollout.jsonl'),resume_unloaded=False,
            owner_verified=True,settle_seconds=0.1,dispatch_mode='notify',rule_schema=2,
            rule_id='rule-one',rule_revision=1,initial_files='ignore',max_pending_batches=100,
            max_state_bytes=1024**3,owner_loading_enabled=False,native_result_collection=False)
        self.fake=FakeDesktop()
        self.store=None
        self.addCleanup(lambda: self.store.close() if self.store else None)

    def open(self,mode='notify',initial=True):
        self.config['dispatch_mode']=mode
        self.store=tr.Store(self.config)
        if mode=='notify' and initial:
            from notify_state import initialize
            initialize(self.store)
        return self.store

    def batch(self,text):
        (self.input/'file.txt').write_text(text)
        return self.store.plan(tr.snapshot(self.config))

    def tick(self):
        return cycle_tick(self.store,adapter_factory=self.fake.factory)

    def finish(self,outcome='unknown'):
        turn=self.store.rows()[0]['turn_id']
        self.fake.turns[turn]=('ended' if outcome=='unknown' else 'failed',outcome)
        self.fake.idle=True


class NotifyTests(NotifyFixture):
    def test_two_notify_batches_wait_then_advance_without_ack(self):
        self.open(); a=self.batch('A'); self.tick(); b=self.batch('B')
        self.tick(); self.assertEqual(self.fake.sent,[a])
        self.finish()
        for _ in range(4): self.tick()
        self.assertEqual(self.fake.sent,[a,b])
        self.assertNotIn('delivered',[r['state'] for r in self.store.rows()])

    def test_strict_keeps_waiting_without_ack(self):
        self.open('verified_delivery'); a=self.batch('A'); self.tick(); self.batch('B')
        self.finish()
        for _ in range(4): self.tick()
        self.assertEqual(self.fake.sent,[a])
        self.assertEqual(self.store.rows()[0]['state'],'ended')

    def test_idle_or_state_string_cannot_release(self):
        self.open(); a=self.batch('A'); self.tick(); self.batch('B')
        self.fake.idle=True; self.store.update(a,'ended')
        self.fake.turns[self.store.rows()[0]['turn_id']]=('ended','unknown')
        self.fake.observe=lambda row: dict(state='ended',turn_id=row['turn_id'])
        for _ in range(3): self.tick()
        self.assertEqual(self.fake.sent,[a])

    def test_failed_and_interrupted_are_not_business_success(self):
        self.open(); a=self.batch('A'); self.tick(); b=self.batch('B'); self.finish('interrupted')
        for _ in range(4): self.tick()
        self.assertEqual(self.fake.sent,[a,b])
        self.assertEqual(self.store.rows()[0]['execution_outcome'],'interrupted')
        self.assertNotEqual(self.store.rows()[0]['state'],'delivered')

    def test_lost_receipt_stays_uncertain_across_restart(self):
        self.open(); a=self.batch('A'); self.fake.loss=True; self.tick(); self.batch('B')
        self.store.close(); self.open(initial=False); self.fake.loss=False
        for _ in range(3): self.tick()
        self.assertEqual(self.fake.sent,[a])
        self.assertEqual(self.store.rows()[0]['state'],'uncertain')

    def test_restart_release_preserves_history(self):
        self.open(); a=self.batch('A'); self.tick(); b=self.batch('B'); self.finish()
        self.tick(); self.store.close(); self.open(initial=False)
        for _ in range(4): self.tick()
        self.assertEqual(self.fake.sent,[a,b]); self.assertEqual(len(self.store.rows()),2)

    def test_baseline_atomic_and_not_fake_delivered(self):
        (self.input/'old.txt').write_text('old'); self.open()
        self.assertEqual(self.store.rows(),[])
        self.assertIsNone(self.store.plan(tr.snapshot(self.config)))
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM versions').fetchone()[0],0)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM baseline_versions').fetchone()[0],1)
        (self.input/'old.txt').rename(self.input/'moved.txt')
        self.assertIsNone(self.store.plan(tr.snapshot(self.config)))

    def test_same_target_other_state_rejected_and_mode_change_rejected(self):
        self.open(); other=dict(self.config,state_dir=str(self.root/'another'))
        with self.assertRaises((ValueError,RuntimeError)):
            tr.Store(other)
        self.store.close(); self.store=None
        with self.assertRaises(ValueError):
            tr.Store(dict(self.config,dispatch_mode='verified_delivery'))

    def test_batch_limit_allows_existing_release_capacity_blocks_sends(self):
        self.config['max_pending_batches']=1; self.open()
        a=self.batch('A'); self.assertIsNone(self.batch('B')); self.tick(); self.finish()
        for _ in range(3): self.tick()
        b=self.batch('B'); self.assertIsNotNone(b)
        self.assertEqual(self.fake.sent,[a])
        self.store.c['max_state_bytes']=1
        self.tick(); self.assertEqual(self.fake.sent,[a])

    def test_stop_blocks_release_and_send(self):
        self.open(); a=self.batch('A'); self.tick(); self.batch('B'); self.finish()
        (self.store.path/'STOP').touch()
        for _ in range(3): self.tick()
        self.assertEqual(self.fake.sent,[a])

    def test_missing_new_fields_defaults_to_strict(self):
        c=copy.deepcopy(self.config); c.pop('dispatch_mode')
        path=self.root/'config.json'; path.write_text(json.dumps(c))
        self.assertEqual(tr.load_config(path)['dispatch_mode'],'verified_delivery')

    def test_other_adapter_notify_rejected(self):
        self.config['chat_adapter']='jsonl_queue'
        with self.assertRaises(ValueError): tr.Store(self.config)


if __name__=='__main__': unittest.main()
