import json
import sqlite3
from test_notify import NotifyFixture
from unittest import mock
import trigger as tr


class RuleServiceTests(NotifyFixture):
    def test_pause_during_initial_scan_cancels_enable(self):
        import notify_state as ns
        import rule_service as rs
        c=self.preview()['config']
        original=tr.snapshot
        paused=[]
        def pause_after_snapshot(*args,**kwargs):
            value=original(*args,**kwargs)
            if not paused:
                rs.pause(c);paused.append(True)
            return value
        with mock.patch.object(tr,'snapshot',side_effect=pause_after_snapshot):
            with self.assertRaises(ValueError):rs.enable(c,adapter_factory=self.fake.factory)
        self.assertFalse(rs.status(c)['enabled'])
        self.store=tr.Store(c)
        self.assertFalse(ns.active(self.store))
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM baseline_versions').fetchone()[0],0)

    def test_pause_during_capability_probe_cancels_enable(self):
        import rule_service as rs
        c=self.preview()['config']
        original=self.fake.inspect
        def pause_then_inspect(row):
            rs.pause(c)
            return original(row)
        self.fake.inspect=pause_then_inspect
        with self.assertRaises(ValueError):rs.enable(c,adapter_factory=self.fake.factory)
        self.assertFalse(rs.status(c)['enabled'])

    # Reuse isolated fixture only, not the lifecycle tests on the subclass.
    def selection(self):
        path=self.root/'rollout.jsonl'
        path.write_text(json.dumps(dict(type='session_meta',payload=dict(id=self.config['thread_id'],cwd=str(self.root))))+'\n')
        return dict(id=self.config['thread_id'],selection_key=self.config['thread_id'],cwd=str(self.root),rollout_path=str(path))

    def preview(self,preset='new_content_stable',**advanced):
        import rule_service as rs
        return rs.preview(str(self.input),preset,self.selection(),state_dir=str(self.root/'state'),**advanced)

    def test_preview_is_side_effect_free_and_enable_ignores_initial(self):
        import rule_service as rs
        (self.input/'initial.txt').write_text('initial')
        for _ in range(2):
            p=self.preview()
            self.assertEqual(p['files'],1)
        self.assertFalse((self.root/'state').exists())
        c=rs.enable(p['config'],adapter_factory=self.fake.factory)
        self.store=tr.Store(c)
        self.assertTrue(c['owner_verified']);self.assertEqual(self.store.rows(),[])
        self.assertIsNone(self.store.plan(tr.snapshot(c)))

    def test_initialization_failure_is_atomic_and_retry_keeps_new_content(self):
        import notify_state as ns
        self.open(initial=False)
        (self.input/'old.txt').write_text('old')
        self.store.db.execute("CREATE TRIGGER fail_init BEFORE INSERT ON meta WHEN NEW.k='notify_initialized' BEGIN SELECT RAISE(ABORT,'synthetic crash'); END")
        with self.assertRaises(sqlite3.IntegrityError): ns.initialize(self.store)
        self.assertFalse(ns.active(self.store))
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM baseline_versions').fetchone()[0],0)
        self.assertEqual(self.store.rows(),[])
        self.store.db.execute('DROP TRIGGER fail_init')
        ns.initialize(self.store);self.assertTrue(ns.active(self.store))

    def test_pause_resume_reuses_baseline(self):
        import rule_service as rs
        c=rs.enable(self.preview()['config'],adapter_factory=self.fake.factory)
        rs.pause(c);(self.input/'later.txt').write_text('later')
        rs.resume(c)
        self.store=tr.Store(c)
        self.assertIsNotNone(self.store.plan(tr.snapshot(c)))
        self.assertTrue(rs.status(c)['enabled'])

    def test_invalid_selection_and_nested_tree_rejected_before_state(self):
        import rule_service as rs
        wrong=self.selection();wrong['id']='11111111-1111-1111-1111-111111111111'
        with self.assertRaises(ValueError): rs.preview(str(self.input),'new_content_stable',wrong)
        with self.assertRaises(ValueError): rs.preview(str(self.input),'new_content_stable',self.selection(),state_dir=str(self.input/'state'))
        self.assertFalse((self.input/'state').exists())

    def test_ready_preset_baseline_absent_then_new_versions_stable(self):
        import rule_service as rs
        (self.input/'old.txt').write_text('old')
        c=rs.enable(self.preview('ready_content_stable',settle_seconds=0.1)['config'],adapter_factory=self.fake.factory)
        self.store=tr.Store(c);scanner=tr.StableScanner(self.store)
        (self.input/'new.txt').write_text('part')
        with self.assertRaises(ValueError): scanner.scan(0)
        (self.input/'READY').touch();scanner.scan(1)
        (self.input/'new.txt').write_text('complete');scanner.scan(1.05)
        self.assertIsNone(scanner.scan(1.1))
        self.assertIsNotNone(scanner.scan(1.2))
        files=json.loads(self.store.rows()[0]['manifest'])['files']
        self.assertEqual([f['path'] for f in files],['new.txt'])

    def test_enabled_claim_survives_worker_exit(self):
        import rule_service as rs
        first=rs.enable(self.preview()['config'],adapter_factory=self.fake.factory)
        other=self.preview()['config'];other['state_dir']=str(self.root/'other');other['rule_id']='rule-two'
        with self.assertRaises(ValueError): rs.enable(other,adapter_factory=self.fake.factory)
        rs.pause(first)
        second=rs.enable(other,adapter_factory=self.fake.factory)
        with self.assertRaises(ValueError): rs.resume(first)
        rs.pause(second);rs.resume(first)

    def test_resource_status_and_revision_retained(self):
        import rule_service as rs
        c=rs.enable(self.preview(max_pending_batches=1)['config'],adapter_factory=self.fake.factory)
        self.store=tr.Store(c);self.config=c
        self.batch('A');self.assertIsNone(self.batch('B'))
        view=rs.status(c)
        self.assertEqual(view['resource_reason'],'batch_capacity')
        self.assertEqual(view['backlog']['batches'],1)
        self.assertEqual(view['batches'][0]['rule_revision'],1)


