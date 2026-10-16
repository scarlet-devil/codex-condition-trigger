"""Adapter boundary tests; all targets and receipts here are synthetic."""
import json
from pathlib import Path
import unittest

import trigger as tr
from test_trigger import Fixture


class AdapterConfigTests(Fixture):
    def test_custom_task_does_not_inject_business_ack_workflow(self):
        self.ready()
        self.config['task_instruction'] = 'Read only; return synthetic result. Caller records ACK.'
        prompt = tr.dispatch_prompt(self.store, self.store.rows()[0])
        self.assertIn(self.config['task_instruction'], prompt)
        self.assertNotIn('Record ack through', prompt)

    def check_invalid(self, **values):
        config = dict(self.config, **values)
        path = self.root / 'config.json'
        path.write_text(json.dumps(config))
        with self.assertRaises(ValueError):
            tr.load_config(path)

    def test_unknown_adapter_rejected(self):
        self.check_invalid(chat_adapter='typo')

    def test_ipc_needs_exact_absolute_rollout(self):
        self.check_invalid(chat_adapter='desktop_ipc', rollout_path='relative.jsonl')

    def test_ipc_cannot_force_resume(self):
        self.check_invalid(chat_adapter='desktop_ipc', rollout_path=str(self.root / 'rollout.jsonl'), resume_unloaded=True)

    def test_state_cannot_change_adapter(self):
        self.ready()
        self.store.close()
        try:
            with self.assertRaises(ValueError):
                other = tr.Store(dict(self.config, chat_adapter='desktop_ipc'))
                other.close()
        finally:
            self.store = tr.Store(self.config)


if __name__ == '__main__':
    unittest.main()
