"""Pending research is durable, but does not monopolize future intake."""
import json
from unittest import mock

import trigger as tr
from test_window_cycle import CycleTests


class MaterialWaitTests(CycleTests):
    def defer_receipt(self, row=None):
        row = row or self.store.rows()[0]
        p = self.root / 'material-wait.json'
        p.write_text(json.dumps(dict(schema=1, batch_id=row['id'],
            turn_id=row['turn_id'], manifest_sha256=tr.digest(
                (self.store.path / 'batches' / (row['id'] + '.json')).read_bytes()),
            status='waiting_materials', reason='Author conclusions not available',
            delivery_verified=False)), encoding='utf-8')
        return p

    def defer(self, p):
        self.assertTrue(callable(getattr(self.store, 'defer_materials', None)),
                        'missing explicit durable waiting-materials transition')
        self.store.defer_materials(self.store.rows()[0]['id'], p)

    def test_later_files_resume_intake_without_faking_delivery(self):
        self.tick(); self.complete(ack=False)
        first = self.store.rows()[0]
        self.defer(self.defer_receipt())
        self.assertEqual(self.store.rows()[0]['state'], 'waiting_materials')
        self.assertEqual(self.tick(), 'cycle_deferred')
        self.reopen()
        self.assertEqual(self.tick(), 'quiet')
        self.ready(b'author conclusions arrived')
        self.assertEqual(self.tick(), 'accepted')
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(self.actions, [])
        prompt = self.store.rows()[1]['dispatch_text']
        self.assertIn(first['id'], prompt)
        self.assertIn('waiting_materials', prompt)
        refs, _ = json.JSONDecoder().raw_decode(prompt.split('References: ', 1)[1])
        self.assertEqual(refs[0]['manifest'], str(self.store.path / 'batches' / (first['id'] + '.json')))
        from pathlib import Path
        self.assertEqual(refs[0]['manifest_sha256'], tr.digest(Path(refs[0]['manifest']).read_bytes()))
        self.assertEqual(self.store.rows()[0]['state'], 'waiting_materials')

    def test_waiting_materials_is_not_replayed_without_new_bytes(self):
        self.tick(); self.complete(ack=False); self.defer(self.defer_receipt())
        self.tick()
        for _ in range(5): self.assertEqual(self.tick(), 'quiet')
        self.assertEqual(len(self.sent), 1)

    def test_completed_without_defer_still_blocks(self):
        self.tick(); self.complete(ack=False); self.ready(b'later')
        self.assertEqual(self.tick(), 'completed')
        self.assertEqual(len(self.sent), 1)

    def test_mismatched_receipt_cannot_release_batch(self):
        self.tick(); self.complete(ack=False)
        p = self.defer_receipt(); d = json.loads(p.read_text()); d['turn_id'] = 'wrong'
        p.write_text(json.dumps(d))
        with self.assertRaises(ValueError): self.defer(p)
        self.assertEqual(self.store.rows()[0]['state'], 'completed')

    def test_active_or_uncertain_turn_cannot_be_deferred(self):
        self.tick()
        for state in ('uncertain', 'sending', 'failed', 'ready'):
            self.store.update(self.store.rows()[0]['id'], state)
            with self.assertRaises(ValueError): self.defer(self.defer_receipt())

    def test_wait_request_during_turn_releases_only_after_correlated_completion(self):
        self.tick()
        self.defer(self.defer_receipt())
        self.assertEqual(self.store.rows()[0]['state'], 'accepted')
        self.ready(b'next')
        self.assertEqual(self.tick(), 'running')
        self.assertEqual(len(self.sent), 1)
        self.complete(ack=False)
        self.assertEqual(self.tick(), 'cycle_deferred')
        self.assertEqual(self.tick(), 'accepted')
        self.assertEqual(len(self.sent), 2)

    def test_owned_window_cannot_be_released_by_defer(self):
        self.available = False
        self.tick(); self.complete(ack=False)
        with self.assertRaises(ValueError): self.defer(self.defer_receipt())
        self.assertEqual(self.actions, ['open'])

    def test_changed_wait_receipt_blocks_next_cycle(self):
        self.tick(); self.complete(ack=False)
        p = self.defer_receipt(); self.defer(p); p.write_text('{}')
        self.ready(b'later')
        self.assertEqual(self.tick(), 'material_evidence_unconfirmed')
        self.assertEqual(len(self.sent), 1)

    def test_verified_delivery_can_ack_deferred_input(self):
        self.tick(); self.complete(ack=False); self.defer(self.defer_receipt()); self.tick()
        p = self.root / 'delivery'; p.write_text('caller verified business delivery')
        self.store.acknowledge(self.store.rows()[0]['id'], p)
        self.assertEqual(self.store.rows()[0]['state'], 'delivered')

    def test_stale_observation_cannot_erase_material_wait(self):
        self.tick(); self.complete(ack=False); self.defer(self.defer_receipt())
        row = self.store.rows()[0]
        self.assertFalse(self.store.update(row['id'], 'completed', detail='stale'))
        self.assertEqual(self.store.rows()[0]['detail'], row['detail'])

    def test_stop_rejects_new_defer(self):
        self.tick(); self.complete(ack=False)
        (self.store.path / 'STOP').touch()
        with self.assertRaises(ValueError): self.defer(self.defer_receipt())
