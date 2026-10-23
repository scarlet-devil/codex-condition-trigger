"""Native turn evidence must not become business acceptance."""
import json
import os
import ntpath
from types import SimpleNamespace
from unittest import mock
import unittest
import desktop_ipc as ipc
import trigger as tr
from test_trigger import Fixture
import test_native_state
import cwd_paths


class ProjectionTests(unittest.TestCase):
    def observe(self, **changes):
        fixture = test_native_state.SnapshotTests()
        state = dict(turns=[dict(turnId='exact', status='failed', error={'message':'private error'})])
        state.update(changes)
        client = fixture.client(state)
        return client.current_state('target', 'owner', test_native_state.WORK_CWD, turn_id='exact')

    def test_exact_failure_survives_thread_idle_without_error_body(self):
        result = self.observe()
        self.assertEqual(result['turn_result'], {'turn_id':'exact','status':'failed','has_error':True})
        self.assertNotIn('private error', json.dumps(result))

    def test_canonical_history_uses_referenced_exact_turn(self):
        result = self.observe(turns=[], turnHistory={'kind':'canonical','history':{
            'isComplete':True,'islands':[{'entries':[{'value':'entity'}]}],
            'entitiesByKey':{'entity':{'turnId':'exact','status':'completed','error':None}}}})
        self.assertEqual(result['turn_result']['status'], 'completed')

    def test_conflicting_native_overlay_does_not_promote_stale_success(self):
        result=self.observe(turns=[{'turnId':'exact','status':'failed','error':None}],
            turnHistory={'kind':'canonical','history':{'islands':[{'entries':[{'value':'entity'}]}],
                'entitiesByKey':{'entity':{'turnId':'exact','status':'completed','error':None}}}})
        self.assertIsNone(result['turn_result'])

    def test_unbound_duplicate_or_error_completion_remains_unknown(self):
        for turns in [[],[{'turnId':'other','status':'failed','error':None}],
                      [{'turnId':'exact','status':'completed','error':{'message':'bad'}}],
                      [{'turnId':'exact','status':'completed','error':None}]*2,
                      [{'turnId':'exact','status':'completed'}]]:
            with self.subTest(turns=turns): self.assertIsNone(self.observe(turns=turns)['turn_result'])
        self.assertIsNone(self.observe(resumeState='resuming')['turn_result'])


class CollectorTests(Fixture):
    def prepare(self):
        self.ready()
        row=self.store.rows()[0]
        self.store.update(row['id'],'ended',turn_id='exact')
        self.config['chat_adapter']='desktop_ipc'
        return self.store.rows()[0]

    def client(self, result='failed', action=None):
        store=self.store
        class Client:
            installation={'archive_sha256':'a'*64}
            def __init__(self, timeout): pass
            def owner(self, thread): return 'owner'
            def current_state(self, thread, owner, cwd, *, turn_id):
                if action: action()
                return {'thread_id':thread,'cwd':cwd,'revision':12,'requested_revision':12,
                        'request_id':'req','owner_id':owner,'turn_result':None if result is None else
                        {'turn_id':turn_id,'status':result,'has_error':result=='failed'}}
            def close(self): pass
        return Client

    def test_collection_persists_failure_and_preserves_stop_and_ack(self):
        from native_collector import collect_outcomes
        row=self.prepare(); stop=self.store.path/'STOP';stop.write_text('retain')
        result=collect_outcomes(self.store, client_factory=self.client())
        self.assertEqual(result[0]['outcome'],'failed')
        changed=self.store.rows()[0]
        self.assertEqual((changed['state'],changed['execution_outcome']),('failed','failed'))
        self.assertEqual(stop.read_text(),'retain')
        self.assertFalse(self.store.db.execute("SELECT v FROM meta WHERE k LIKE 'ack:%'").fetchall())
        self.assertEqual(collect_outcomes(self.store,client_factory=self.client()),[])

    def test_unknown_or_read_failure_does_not_relabel_ended(self):
        from native_collector import collect_outcomes
        self.prepare()
        for factory in [self.client(None), mock.Mock(side_effect=OSError('offline'))]:
            collect_outcomes(self.store,client_factory=factory)
            row=self.store.rows()[0]
            self.assertEqual((row['state'],row['execution_outcome']),('ended','unknown'))

    def test_concurrent_delivery_or_binding_change_never_overwritten(self):
        from native_collector import collect_outcomes
        row=self.prepare()
        for change in ["state='delivered'", "turn_id='other'", "manifest='changed'"]:
            def update():
                with self.store.db: self.store.db.execute('UPDATE batches SET '+change+' WHERE id=?',(row['id'],))
            result=collect_outcomes(self.store,client_factory=self.client(action=update))
            self.assertEqual(result[0]['status'],'changed')
            self.assertEqual(self.store.rows()[0]['execution_outcome'],'unknown')
            with self.store.db:self.store.db.execute("UPDATE batches SET state='ended',turn_id='exact',manifest=? WHERE id=?",(row['manifest'],row['id']))

    def test_live_cycle_collects_before_window_or_material_short_circuit(self):
        from owner_loading import cycle_tick
        self.prepare();self.config['native_result_collection']=True
        self.config['owner_loading_enabled']=True
        with self.store.db:self.store.db.execute("UPDATE batches SET state='waiting_materials'")
        with mock.patch('native_collector.collect_outcomes',return_value=[]) as collect:
            self.assertEqual(cycle_tick(self.store),'quiet')
            collect.assert_called_once()

    def test_equivalent_cwd_is_valid_after_native_verification(self):
        from native_collector import collect_outcomes
        row=self.prepare();factory=self.client();original=factory.current_state
        def variant(client,*args,**kwargs):
            value=original(client,*args,**kwargs)
            value['cwd']=(value['cwd'].upper().replace('\\','/') if os.name=='nt'
                          else os.path.join(value['cwd'],'.'))
            return value
        with mock.patch.object(factory,'current_state',variant):
            result=collect_outcomes(self.store,client_factory=factory)
        self.assertEqual(result[0]['status'],'recorded')

    def test_clean_drive_forms_match_without_accepting_different_paths(self):
        from native_collector import collect_outcomes
        self.prepare()
        self.config['expected_cwd'] = r'\\?\D:\project'
        factory = self.client()
        original = factory.current_state
        for native, expected in ((r'E:\project', 'unknown'),
                                 (r'D:\project-other', 'unknown'),
                                 (r'\\?\D:\base\..\project', 'unknown'),
                                 (r'D:\project', 'recorded')):
            def variant(client, *args, native=native, **kwargs):
                value = original(client, *args, **kwargs)
                value['cwd'] = native
                return value
            with self.subTest(native=native), mock.patch.object(factory, 'current_state', variant), \
                    mock.patch.object(cwd_paths, 'os', SimpleNamespace(name='nt', path=ntpath)):
                result = collect_outcomes(self.store, client_factory=factory)
            self.assertEqual(result[0]['status'], expected)
        self.assertEqual(self.store.rows()[0]['turn_id'], 'exact')
        self.assertFalse(self.store.db.execute("SELECT v FROM meta WHERE k LIKE 'ack:%'").fetchall())

    def test_paused_cycle_does_not_collect_or_dispatch(self):
        from owner_loading import cycle_tick
        self.prepare();self.config['native_result_collection']=True
        (self.store.path/'STOP').touch()
        with mock.patch('native_collector.collect_outcomes',side_effect=AssertionError('must not run')):
            self.assertEqual(cycle_tick(self.store),'paused')


if __name__=='__main__': unittest.main()
