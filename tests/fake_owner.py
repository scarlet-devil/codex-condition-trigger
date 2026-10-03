"""Protocol test double ONLY; never starts Codex or contacts a model."""
import json
from pathlib import Path
import sys
import time

p = Path(sys.argv[1])
state = json.loads(p.read_text())
for line in sys.stdin:
    message = json.loads(line)
    method = message["method"]
    args = message.get("params", {})
    if method == "initialized":
        continue
    if method == "initialize":
        state["initializations"] = state.get("initializations", 0) + 1
        result = {"userAgent": "fake-owner-for-tests"}
    elif method == "thread/read":
        if state.get("mode") == "wrong_id_flood":
            state["noise_started"] = True
            p.write_text(json.dumps(state))
            end = time.monotonic() + 8
            while time.monotonic() < end:
                print(json.dumps({"id": "unrelated", "result": {}}), flush=True)
            continue
        result = {"thread": {"id": state["thread_id"], "cwd": state["cwd"],
                             "status": {"type": "idle"}, "turns": []}}
    elif method == "thread/queue/list":
        result = {"data": state["queue"], "nextCursor": None}
    elif method == "thread/queue/add":
        item = {"id": "fake-submission", "clientUserMessageId": args["clientUserMessageId"], "input": args["input"]}
        state["queue"].append(item)
        result = {"queuedSubmission": item}
    else:
        raise RuntimeError(method)
    p.write_text(json.dumps(state))
    print(json.dumps({"id": message["id"], "result": result}), flush=True)
