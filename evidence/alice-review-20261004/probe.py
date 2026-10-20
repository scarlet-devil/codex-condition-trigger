"""Alice's synthetic review probes for candidate 93d84fd; no Desktop/model calls.

Run: python evidence/alice-review-20261004/probe.py
These probes record candidate behavior, not a passing acceptance suite.
"""
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import desktop_ipc as ipc
from test_desktop_ipc import DesktopDispatchTests, WireTests


def event(kind, turn):
    return {"type": "event_msg", "payload": {"type": kind, "turn_id": turn}}


def interrupted_history():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "rollout.jsonl"
        rows = [
            {"type": "session_meta", "payload": {"id": "synthetic-target", "cwd": directory}},
            event("task_started", "a"), event("turn_interrupted", "a"),
        ]
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        first = ipc.rollout_state(path, "synthetic-target", directory)
        rows += [event("task_started", "b"), event("task_complete", "b")]
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        try:
            later = ipc.rollout_state(path, "synthetic-target", directory)
            result = {"status": later["status"]}
        except Exception as error:
            result = {"exception": type(error).__name__, "message": str(error)}
        return {"after_interruption": first["status"], "after_next_complete_turn": result,
                "source_boundary": "turn_interrupted appears in the pinned third-party reference; current Windows event shape not independently verified"}


def malformed_acceptance():
    case = DesktopDispatchTests(methodName="test_native_acceptance_completion_and_ack_are_distinct")
    case.setUp()
    try:
        case.ready()
        original = case.client.request
        def malformed(client, *args, **kwargs):
            original(client, *args, **kwargs)  # synthetic dispatch writes a correlated local turn
            return {"result": None}
        case.client.request = malformed
        try:
            value = case.dispatch()
            result = {"return": value}
        except Exception as error:
            result = {"exception": type(error).__name__, "message": str(error)}
        result["persisted_before_restart"] = case.store.rows()[0]["state"]
        case.reopen()
        result["persisted_after_restart"] = case.store.rows()[0]["state"]
        result["reconciliation_after_restart"] = case.dispatch()
        result["synthetic_requests"] = len(case.sent)
        return result
    finally:
        case.tearDown()


def malformed_frame():
    fixture = WireTests()
    client = fixture.client(lambda request: [None])
    try:
        return {"return": client.request("initialize", {})}
    except Exception as error:
        return {"exception": type(error).__name__, "message": str(error)}


print(json.dumps({
    "input_commit": "93d84fdd4be5d6ed7b9ea9317a3326489a12a41b",
    "actor": "Alice, cloud Linux",
    "real_ipc_or_model_calls": 0,
    "interrupted_lifecycle": interrupted_history(),
    "malformed_success_reply": malformed_acceptance(),
    "malformed_json_frame": malformed_frame(),
}, indent=2))
