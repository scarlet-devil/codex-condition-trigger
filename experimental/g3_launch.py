"""Supervised G3 launcher; no fake transport and no automatic rearm."""

import argparse
import copy
import json
import sqlite3
import sys
import threading
import time
import tkinter as tk
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import trigger as tr
from cwd_paths import cwd_matches
from desktop_ipc import rollout_state
from simple_catalog import verify_selection
from simple_controller import Controller, read_status
from simple_setup import App
from experimental.g3_trial import G3Budget, BoundedAdapter, preserve_primary


def save(path, obj):
    tr.atomic_write(
        Path(path), (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()
    )


def constrained_preview(result, contract, selection):
    c = copy.deepcopy(result["config"])
    if (
        c["thread_id"] != selection["id"]
        or not cwd_matches(c["expected_cwd"], selection["cwd"])
        or Path(c["rollout_path"]).resolve()
        != Path(selection["rollout_path"]).resolve()
        or Path(c["input_dir"]).resolve() != Path(contract["input_dir"]).resolve()
        or c["settle_seconds"] != 1
        or c["ready_file"] is not None
        or c["initial_files"] != "ignore"
    ):
        raise ValueError("trial form does not match approved binding")
    c.update(contract["rule_overrides"])
    for key, value in {
        "dispatch_mode": "notify",
        "initial_files": "ignore",
        "settle_seconds": 1,
        "owner_loading_enabled": False,
        "resume_unloaded": False,
        "native_result_collection": False,
    }.items():
        if c.get(key) != value:
            raise ValueError("trial safety option differs: " + key)
    c["trial_expires_at_utc"] = datetime.fromtimestamp(
        contract["expires_at_epoch"], timezone.utc
    ).isoformat()
    c["task_instruction"] = contract["instruction"]
    c = tr.validate_config(c)
    return dict(result, config=c)


class TrialController(Controller):
    def update(self, form):
        if form:
            form = dict(form, identity_reader=lambda p: self.budget.read_identity(p))
        super().update(form)

    def __init__(self, home, budget, selection, *, expected_saved=None):
        self.budget, self.selection = budget, selection
        self.expected_saved = copy.deepcopy(expected_saved)
        super().__init__(
            home,
            adapter_factory=lambda c, paused: BoundedAdapter(c, paused, budget),
            simulation=False,
        )

    def _event(self, event, **fields):
        if event == "preview":
            self.preview_result = constrained_preview(
                self.preview_result, self.budget.contract, self.selection
            )
        super()._event(event, **fields)

    def _start(self, initialize):
        self.budget.guard()
        c = self.config or (self.preview_result or {}).get("config")
        if not c:
            raise ValueError("preview required")
        if self.expected_saved is not None and (initialize or c != self.expected_saved):
            raise ValueError("second window must resume the same saved paused rule")
        constrained_preview({"config": c}, self.budget.contract, self.selection)
        for key, value in self.budget.contract["rule_overrides"].items():
            if c.get(key) != value:
                raise ValueError("saved rule trial options differ")
        if c.get("task_instruction") != self.budget.contract["instruction"]:
            raise ValueError("saved instruction differs")
        if tr.trial_deadline(c) != self.budget.contract["expires_at_epoch"]:
            raise ValueError("saved deadline differs")
        super()._start(initialize)


def rows(config):
    p = Path(config["state_dir"]) / "state.sqlite"
    with closing(sqlite3.connect(p.as_uri() + "?mode=ro", uri=True, timeout=1)) as db:
        db.row_factory = sqlite3.Row
        return [
            dict(r)
            for r in db.execute(
                "SELECT b.*,n.acceptance,n.terminal,n.released,n.release_evidence FROM batches b JOIN notifications n ON n.batch_id=b.id ORDER BY b.created,b.id"
            )
        ]


def fixture(label):
    offset = 0 if label == "A" else 100
    data = [dict(id=f"{label}{i:02}", value=offset + i) for i in range(1, 25)]
    data += [
        dict(id=f"{label}03", value=offset + 3),
        dict(id=f"{label}07", value=offset + 8),
        dict(id=f"{label}25"),
    ]
    return dict(label=label, records=data)


def close_window(controller, window, stopper, supervisor):
    """Drain only resources owned by this trial; never cancel the host's model turn."""
    if stopper:
        stopper.set()
    if controller:
        controller.close()
    until = time.monotonic() + 12
    if supervisor:
        supervisor.join(max(0, until - time.monotonic()))
    while controller and not controller.view()["closed"] and time.monotonic() < until:
        time.sleep(0.02)
    if window:
        try:
            if window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass  # App.poll may already have destroyed its own Tcl application.
    if (supervisor and supervisor.is_alive()) or (
        controller and not controller.view()["closed"]
    ):
        raise TimeoutError("trial_resource_cleanup_incomplete")


def validate_launch(contract):
    """Static preparation check; no deadline creation, IPC, model or GUI."""
    workflow = contract.get("workflow", "two_stage_form")
    if workflow not in ("two_stage_form", "batches_only"):
        raise ValueError("unknown trial workflow")
    rootdir = Path(contract["trial_root"]).resolve(strict=True)
    selection = json.loads(Path(contract["selection_path"]).read_bytes())
    if selection["id"] != contract["thread_id"]:
        raise ValueError("target changed")
    if workflow == "batches_only":
        if contract.get("min_start_remaining_seconds") != 180:
            raise ValueError("batches-only trial requires 180-second start reserve")
        if (
            contract["duration_seconds"] != 480
            or contract["limits"]["start_write_attempts"] != 2
        ):
            raise ValueError(
                "batches-only trial requires fixed 480-second/two-start scope"
            )
        if Path(contract["input_dir"]).resolve(strict=True) != rootdir / "inbox":
            raise ValueError("trial inbox binding differs")
        if {p.name for p in (rootdir / "inbox").iterdir()} != {"initial.json"}:
            raise ValueError("fresh isolated inbox with initial.json required")
        rules = rootdir / "rules"
        if rules.exists() and any(rules.iterdir()):
            raise ValueError(
                "fresh rules directory required; old batches cannot be resumed"
            )
        if not contract.get("expected_archive_sha256"):
            raise ValueError("installation pin required")
    return workflow, rootdir, selection


def start_batches(controller, budget, selection):
    """Use the real controller/enablement check; reuse already accepted GUI proof."""
    controller.update(
        dict(
            folder=budget.contract["input_dir"],
            condition="new_content_stable",
            selection=selection,
            settle_seconds=1,
            initial_files="ignore",
        )
    )
    controller.preview()
    while controller.view()["alive"] or controller.view()["command_busy"]:
        budget.guard()
        time.sleep(0.02)
    if controller.view()["error"]:
        raise ValueError("batch preview failed: " + str(controller.view()["error"]))
    budget.admit_start()
    controller.enable()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_bytes())
    workflow, rootdir, selection = validate_launch(contract)
    if args.check_only:
        print("launcher inputs checked; no activation, deadline, IPC or model")
        return 0
    if not contract.get("activation_allowed"):
        raise ValueError("trial not armed")
    budget = G3Budget(contract, rootdir / "private/budget.json")
    evidence = dict(
        phase=0,
        window_results=[],
        wrote_a=False,
        wrote_b=False,
        a_running_observed=False,
        b_waiting_while_a_running=False,
        two_released=False,
        closed=False,
        workflow=workflow,
        gui_evidence_reused=workflow == "batches_only",
    )
    (rootdir / "rules").mkdir(exist_ok=True)
    row_a = None
    expected_saved = None
    controller = window = supervisor = supervisor_stop = None
    try:
        verify_selection(selection, reader=budget.read_identity)
        for phase in (2,) if workflow == "batches_only" else (1, 2):
            budget.guard()
            evidence["phase"] = phase
            controller = TrialController(
                rootdir / "rules", budget, selection, expected_saved=expected_saved
            )
            if workflow == "two_stage_form":
                window = tk.Tk()
                App(
                    window,
                    controller,
                    Path(contract["catalog_path"]),
                    evidence_path=rootdir / "private" / f"ui-phase-{phase}.json",
                )
                window.title(f"条件触发器 · G3 单次试验 {phase}/2")
            else:
                start_batches(controller, budget, selection)

            def tick():
                nonlocal row_a
                try:
                    if (
                        budget.reason
                        or budget.wall() >= contract["expires_at_epoch"]
                        or budget.mono() >= budget.end
                    ):
                        controller.close()
                        if budget.reason is None:
                            budget.stop("trial_expired")
                    v = controller.view()
                    if v["closing"]:
                        return
                    if v["error"]:
                        budget.stop("controller_error")
                        controller.close()
                    c = v["config"]
                    if phase == 2 and c and v["worker_started"] and not budget.reason:
                        current = rows(c)
                        if not evidence["wrote_a"]:
                            budget.guard()
                            save(rootdir / "inbox/A.json", fixture("A"))
                            evidence["wrote_a"] = True
                            budget.event("fixture_written", label="A")
                        elif current:
                            row_a = current[0]
                            # This bounded read is counted together with adapter scans.
                            if row_a["acceptance"] and not evidence["wrote_b"]:
                                meta = json.loads(row_a["dispatch_meta"])
                                life = rollout_state(
                                    c["rollout_path"],
                                    c["thread_id"],
                                    c["expected_cwd"],
                                    baseline=meta["baseline"],
                                    reader=budget.read_rollout,
                                )
                                turn = life["turns"].get(row_a["turn_id"])
                                if turn and turn["state"] == "running":
                                    evidence["a_running_observed"] = True
                                    budget.guard()
                                    save(rootdir / "inbox/B.json", fixture("B"))
                                    evidence["wrote_b"] = True
                                    budget.event(
                                        "fixture_written", label="B", a_running=True
                                    )
                                elif turn and turn["state"] in ("ended", "failed"):
                                    budget.stop("a_finished_before_overlap_observed")
                            if (
                                len(current) == 2
                                and not evidence["b_waiting_while_a_running"]
                            ):
                                meta = json.loads(row_a["dispatch_meta"])
                                life = rollout_state(
                                    c["rollout_path"],
                                    c["thread_id"],
                                    c["expected_cwd"],
                                    baseline=meta["baseline"],
                                    reader=budget.read_rollout,
                                )
                                turn = life["turns"].get(row_a["turn_id"])
                                if (
                                    turn
                                    and turn["state"] == "running"
                                    and current[1]["state"] == "ready"
                                    and not current[1]["acceptance"]
                                ):
                                    evidence["b_waiting_while_a_running"] = True
                                    budget.event("b_waiting_while_a_running")
                                elif turn and turn["state"] in ("ended", "failed"):
                                    budget.stop("b_waiting_overlap_not_observed")
                            if len(current) == 2 and all(
                                r["released"] for r in current
                            ):
                                evidence["two_released"] = True
                                budget.stop("two_batches_released")
                                controller.close()
                    save(
                        rootdir / "private/supervisor.json",
                        dict(evidence, budget_reason=budget.reason),
                    )
                except BaseException as error:
                    evidence["supervisor_error"] = (
                        type(error).__name__ + ": " + str(error)
                    )
                    budget.stop_for_error("supervisor_error", error)
                    preserve_primary(
                        error, controller.close, "controller close failure"
                    )
                    evidence["supervisor_error_notes"] = getattr(error, "__notes__", [])

            supervisor_stop = threading.Event()

            def supervise():
                while not supervisor_stop.is_set() and not controller.view()["closed"]:
                    tick()
                    supervisor_stop.wait(0.25)

            supervisor = threading.Thread(
                target=supervise, name="g3-bounded-supervisor"
            )
            supervisor.start()
            try:
                if window is not None:
                    window.mainloop()
                else:
                    while not controller.view()["closed"]:
                        supervisor.join(0.25)
            finally:
                preserve_primary(
                    sys.exc_info()[1],
                    lambda: close_window(
                        controller, window, supervisor_stop, supervisor
                    ),
                    "window cleanup failure",
                )
            config = controller.config
            snap = (
                read_status(config)
                if config and (Path(config["state_dir"]) / "state.sqlite").exists()
                else None
            )
            evidence["window_results"].append(
                dict(
                    phase=phase,
                    controller_closed=controller.view()["closed"],
                    status=snap,
                )
            )
            if config:
                save(rootdir / "private/final-config.json", config)
                save(rootdir / "private/batches.json", rows(config))
            if budget.reason:
                break
            if (
                not config
                or not snap
                or snap["enabled"]
                or not snap["initialized"]
                or snap["batches"]
            ):
                budget.stop("first_window_not_cleanly_paused")
                break
            budget.event("gui_reopened_next", phase=phase)
            expected_saved = copy.deepcopy(config)
    except BaseException as error:
        evidence["error"] = type(error).__name__ + ": " + str(error)
        budget.stop_for_error("outer_failure", error)
        preserve_primary(
            error,
            lambda: close_window(controller, window, supervisor_stop, supervisor),
            "outer cleanup failure",
        )
        evidence["error_notes"] = getattr(error, "__notes__", [])
        raise
    finally:
        primary = sys.exc_info()[1]
        if not budget.reason:
            preserve_primary(
                primary,
                lambda: budget.stop("closed_without_completion"),
                "final stop failure",
            )
        evidence.update(
            closed=(controller is None or controller.view()["closed"])
            and (supervisor is None or not supervisor.is_alive()),
            budget_reason=budget.reason,
            ended_at=datetime.now(timezone.utc).isoformat(),
        )
        preserve_primary(
            primary,
            lambda: save(rootdir / "private/supervisor.json", evidence),
            "final report failure",
        )
    return (
        0
        if (
            evidence["two_released"]
            and evidence["closed"]
            and not evidence.get("supervisor_error")
            and not evidence.get("error")
            and budget.reason == "two_batches_released"
        )
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
