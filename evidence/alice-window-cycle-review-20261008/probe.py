"""Alice's isolated pre-send owner-loss counterexample; no native IPC/UI/model.

Usage: python evidence/alice-window-cycle-review-20261008/probe.py --repo .
The unchanged candidate is expected to fail the recovery requirement.
Existing test fixtures provide only temporary files, SQLite and synthetic IPC.
"""
import argparse
import json
import sys
from pathlib import Path
from unittest import mock

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
args = parser.parse_args()
root = args.repo.resolve()
sys.path[:0] = [str(root), str(root / 'tests')]
from test_window_cycle import CycleTests

case = CycleTests('test_surviving_owner_reused_on_second_batch')
case.setUp()
trace = {}
try:
    original_owner = case.client.owner
    calls = 0
    def disappears(client, target):
        global calls
        calls += 1
        # The first preparation observes a real synthetic idle owner.
        # It disappears before dispatch's independent pre-send inspection.
        if calls >= 2:
            case.available = False
        return original_owner(client, target)
    with mock.patch.object(case.client, 'owner', disappears):
        first = case.tick()
    row = case.store.rows()[0]
    trace['first_tick'] = first
    trace['before_restart'] = {
        'batch_state': row['state'],
        'dispatch_text_is_none': row['dispatch_text'] is None,
        'dispatch_meta_is_none': row['dispatch_meta'] is None,
        'cycle_phase': case.manager().records()[0]['phase'],
        'lease_is_none': case.manager().records()[0]['lease'] is None,
        'open_calls': case.actions.count('open'),
        'send_calls': len(case.sent),
    }
    case.reopen()
    retry_at = case.store.rows()[0]['next_try']
    trace['retry_deadline_bypassed_by_seconds'] = 60
    # Advance the synthetic clock, so normal pre-send retry backoff has expired.
    with mock.patch('time.time', return_value=retry_at + 60):
        trace['ticks_after_restart'] = [case.tick() for _ in range(3)]
        case.ready(b'Alice synthetic second pending batch')
        trace['tick_after_new_file'] = case.tick()
    trace['pending_batches'] = len(case.store.rows())
    trace['final_open_calls'] = case.actions.count('open')
    trace['final_send_calls'] = len(case.sent)
    trace['final_cycle_phase'] = case.manager().records()[0]['phase']
    trace['requirement'] = (
        'Definite owner absence for a ready, never-dispatched, reused cycle '
        'with no lease or prior window action permits one durable open claim.'
    )
    trace['requirement_satisfied'] = case.actions.count('open') == 1 and len(case.sent) == 1
    trace['native_actions'] = 0
    trace['model_calls'] = 0
finally:
    case.tearDown()
    case.doCleanups()
print(json.dumps(trace, indent=2))
raise SystemExit(0 if trace['requirement_satisfied'] else 1)

