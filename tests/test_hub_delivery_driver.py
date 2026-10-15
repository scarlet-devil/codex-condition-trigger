"""Optional Hub dependency: real boundary and outbox, synthetic remote provider."""
import base64
import gc
import json
import unittest
from pathlib import Path
import delivery_outbox as outbox
import hub_delivery_driver as driver
from test_trigger import Fixture

try:
    from drive_exchange_local_hub import HubStore, LocalHub, FakeDriveConnector
    HUB_AVAILABLE=True
except ImportError:
    HUB_AVAILABLE=False


class Provider:
    def __init__(self): self.objects={}; self.reserves=0; self.creates=0; self.drop=True
    def reserve_material_id(self,identity): self.reserves+=1; return 'file-'+str(self.reserves)
    def material_action(self,action,identity,remote_id,d,body):
        if action=='upload' and remote_id not in self.objects:
            self.objects[remote_id]=(dict(d),body); self.creates+=1
            if self.drop: raise TimeoutError('synthetic loss after create')
        if remote_id not in self.objects:return None
        d,body=self.objects[remote_id]
        return dict(id=remote_id,name=d['name'],parents=[d['parent_id']],trashed=False,
            appProperties={'condition_key':d['key'],'source_sha256':d['sha256']},
            content_base64=base64.b64encode(body).decode())


@unittest.skipUnless(HUB_AVAILABLE, 'isolated Hub dependency is required')
class HubDeliveryTests(Fixture):
    def setUp(self):
        super().setUp(); self.ready(); self.row=self.store.rows()[0]
        self.store.update(self.row['id'],'ended'); self.before=self.store.rows()[0]
        (self.root/'.drive-exchange').mkdir()
        (self.root/'.drive-exchange/project.json').write_text(json.dumps(dict(project_id='synthetic',route='standard')))
        self.hubstore=HubStore(self.root/'hub.sqlite');self.hubstore.register_project(root=self.root,display_name='Synthetic')
        fake=FakeDriveConnector(folders={'folder'})
        self.hubstore.bind_route(project_id='synthetic',route_name='standard',folder_id='folder',verification=fake.verify_folder('folder'))
        self.provider=Provider(); self.hub=LocalHub(store=self.hubstore,connector=self.provider)
        self.artifact=self.root/'canary.txt'; self.artifact.write_bytes(b'canary result\n')
        self.job=outbox.stage(self.store,self.row['id'],'folder',[str(self.artifact)])
        self.binding=dict(project_root=str(self.root),project_id='synthetic',route_name='standard',
                          frozen_root=str(self.store.path/'delivery-outbox'))
    def tearDown(self):
        gc.collect(); super().tearDown()
    def call(self,request):return driver.exchange(request,self.binding,self.hub)
    def test_response_loss_reopen_outbox_and_hub_no_reexecution(self):
        stop=self.store.path/'STOP';stop.write_text('preserve')
        first=outbox.resume(self.store,self.job,self.call)
        self.assertEqual(first['state'],'upload_uncertain')
        self.reopen();self.hub=LocalHub(store=HubStore(self.root/'hub.sqlite'),connector=self.provider)
        recovered=outbox.resume(self.store,self.job,self.call)
        self.assertEqual(recovered['state'],'uploaded_verified')
        self.assertEqual((self.provider.reserves,self.provider.creates),(1,1))
        self.assertEqual(self.store.rows()[0],self.before)
        self.assertEqual(stop.read_text(),'preserve')
    def test_changed_frozen_bytes_and_project_binding_fail_before_cloud(self):
        request=dict(outbox.jobs(self.store)[0]['artifacts'][0],schema=1,action='lookup',
            batch_id=self.row['id'],manifest_sha256='b'*64,parent_id='folder')
        Path(request['path']).write_bytes(b'tampered')
        with self.assertRaises(ValueError):self.call(request)
        self.assertEqual(self.provider.reserves,0)
    def test_outside_frozen_root_is_rejected(self):
        item=outbox.jobs(self.store)[0]['artifacts'][0]
        request=dict(item,schema=1,action='lookup',batch_id=self.row['id'],manifest_sha256='b'*64,
                     parent_id='folder',path=str(self.artifact))
        with self.assertRaises(ValueError):self.call(request)
        self.assertEqual(self.provider.reserves,0)
