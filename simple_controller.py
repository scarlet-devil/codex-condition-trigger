"""Thin asynchronous form controller; existing G1 Store/run remain the scheduler."""

import copy
import json
import queue
import sqlite3
import threading
import time
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path

import notify_state as ns
import rule_service as rs
import trigger as tr
from execution_result import batch_status
from worker_health import read_health


def read_status(c):
    """Never call Store/status on a missing or malformed saved database."""
    p = Path(c["state_dir"])
    with closing(
        sqlite3.connect(
            (p / "state.sqlite").resolve(strict=True).as_uri() + "?mode=ro",
            uri=True,
            timeout=2,
        )
    ) as db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN")
        meta = dict(db.execute("SELECT k,v FROM meta"))
        expected = {k: c[k] for k in ("input_dir", "thread_id", "expected_cwd")}
        expected["notify"] = ns.binding(c)
        if (
            meta.get("binding") != tr.encode(expected)
            or meta.get("chat_adapter") != "desktop_ipc"
            or meta.get("trial_deadline", tr.encode(None))
            != tr.encode(tr.trial_deadline(c))
        ):
            raise ValueError("saved rule binding mismatch")
        rows = []
        for row in db.execute(
            "SELECT b.*,n.released,n.acceptance,n.terminal FROM batches b JOIN notifications n ON n.batch_id=b.id ORDER BY created DESC,id LIMIT 20"
        ):
            rows.append(
                dict(
                    batch_status(row),
                    notification_released=bool(row["released"]),
                    native_acceptance=bool(row["acceptance"]),
                    exact_terminal=bool(row["terminal"]),
                )
            )
        pending = db.execute(
            "SELECT count(*) FROM notifications WHERE released=0"
        ).fetchone()[0]
        size = 0
        for f in p.rglob("*"):
            try:
                if f.is_file():
                    size += f.stat().st_size
            except FileNotFoundError:
                pass  # transient progress tmp / SQLite journal
        resource = (
            "state_capacity"
            if size >= c["max_state_bytes"]
            else "batch_capacity"
            if pending >= c["max_pending_batches"]
            else None
        )
        return {
            "enabled": meta.get("notify_enabled") == "true",
            "initialized": meta.get("notify_initialized") == "true",
            "initial_files": int(meta["notify_initial_file_count"])
            if "notify_initial_file_count" in meta
            else None,
            "initial_bytes": int(meta["notify_initial_bytes"])
            if "notify_initial_bytes" in meta
            else None,
            "resource_reason": resource,
            "backlog": pending,
            "batches": rows,
            "rows_limit": 20,
            "watcher": read_health(p),
            "stop_present": (p / "STOP").exists(),
            "deadline": tr.trial_deadline(c),
        }


def save_rule(c, simulation):
    p = Path(c["state_dir"])
    raw = (tr.encode(c) + "\n").encode()
    tr.atomic_write(p / "rule.json", raw)
    tr.atomic_write(
        p / "simple-rule.json",
        (
            tr.encode(
                {"schema": 1, "simulation": simulation, "config_sha256": tr.digest(raw)}
            )
            + "\n"
        ).encode(),
    )


def load_rule(home, path, simulation):
    tr.safe_stat(Path(path))
    home = Path(home).resolve()
    p = Path(path).resolve(strict=True)
    if p.parent != home or p.is_symlink():
        raise ValueError("foreign rule directory")
    for name in ("simple-rule.json", "rule.json", "state.sqlite"):
        tr.safe_stat(p / name)
    marker = json.loads((p / "simple-rule.json").read_bytes())
    raw = (p / "rule.json").read_bytes()
    if marker != {
        "schema": 1,
        "simulation": simulation,
        "config_sha256": tr.digest(raw),
    }:
        raise ValueError("saved rule manifest mismatch")
    c = tr.validate_config(json.loads(raw))
    if c.get("dispatch_mode") != "notify" or Path(c["state_dir"]).resolve() != p:
        raise ValueError("foreign rule binding")
    return c, read_status(c)


def saved_rules(home):
    home = Path(home)
    return (
        [
            {"path": str(p), "label": p.name}
            for p in sorted(home.iterdir())
            if p.is_dir() and (p / "simple-rule.json").exists()
        ]
        if home.exists()
        else []
    )


class Controller:
    def __init__(
        self,
        home,
        *,
        adapter_factory,
        simulation=False,
        dispatch_interval=10,
        run_fn=None,
    ):
        if simulation and adapter_factory is None:
            raise ValueError("simulation requires explicit fake transport")
        if not simulation and dispatch_interval != 10:
            raise ValueError("short dispatch interval is simulation-only")
        self.home = Path(home).resolve()
        self.adapter_factory = adapter_factory
        self.simulation = simulation
        self.interval = dispatch_interval
        self.run_fn = run_fn or tr.run
        self.lock = threading.RLock()
        self.ownership_lock = threading.RLock()
        self.owns_worker = False
        self.events = queue.Queue()
        self.threads = []
        self.form = {}
        self.generation = 0
        self.preview_result = None
        self.config = None
        self.initialized = False
        self.command_busy = False
        self.refresh_busy = False
        self.worker_started = False
        self.worker = None
        self.run_id = None
        self.error = None
        self.status = {}
        self.closing = False
        self.cancel = threading.Event()
        self.stop = threading.Event()

    def _event(self, event, **data):
        self.events.put(dict(event=event, **data))

    def _spawn(self, fn, kind):
        # Status refreshes recur for the lifetime of the form. Keep only live
        # operations; completed Thread objects are not a second history log.
        self.threads = [thread for thread in self.threads if thread.is_alive()]

        def wrapped():
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 - report the worker or UI boundary error
                with self.lock:
                    self.error = f"{type(exc).__name__}: {exc}"
                self._event("error", operation=kind, reason=self.error)
            finally:
                with self.lock:
                    if kind == "refresh":
                        self.refresh_busy = False
                    elif kind in ("preview", "load"):
                        self.command_busy = False

        thread = threading.Thread(
            target=wrapped, name="simple-rule-" + kind, daemon=False
        )
        self.threads.append(thread)
        try:
            thread.start()
        except Exception:
            self.threads.remove(thread)
            self.command_busy = False
            self.refresh_busy = False
            raise
        return thread

    def view(self):
        with self.lock:
            alive = any(t.is_alive() for t in self.threads)
            worker_alive = self.worker is not None and self.worker.is_alive()
            status = copy.deepcopy(self.status)
            if status:
                h = status.get("watcher", {})
                try:
                    age = (
                        time.time()
                        - datetime.fromisoformat(h["progress_at_utc"]).timestamp()
                    )
                except (KeyError, TypeError, ValueError):
                    age = float("inf")
                current = (
                    worker_alive
                    and self.worker_started
                    and h.get("run_id") == self.run_id
                    and h.get("state") == "running"
                    and 0 <= age <= 30
                )
                status["monitoring"] = (
                    "failed"
                    if h.get("state") == "failed"
                    else "listening"
                    if current
                    and h.get("last_scan_at_utc")
                    and h.get("scan_result") == "ok"
                    else "starting"
                    if current and not h.get("last_scan_at_utc")
                    else "health_attention"
                    if worker_alive
                    else "enabled_no_worker"
                    if status.get("enabled")
                    else "stopped"
                )
            return {
                "alive": alive,
                "worker_alive": worker_alive,
                "worker_started": self.worker_started and worker_alive,
                "command_busy": self.command_busy,
                "refresh_busy": self.refresh_busy,
                "preview": copy.deepcopy(self.preview_result),
                "config": copy.deepcopy(self.config),
                "status": status,
                "pausing": self.cancel.is_set()
                and any(
                    t.is_alive()
                    and t.name in ("simple-rule-worker", "simple-rule-pause")
                    for t in self.threads
                ),
                "error": self.error,
                "closing": self.closing,
                "closed": self.closing and not alive,
                "generation": self.generation,
            }

    def update(self, form):
        with self.lock:
            if self.config is not None:
                raise ValueError("pause and create a new rule to change its inputs")
            self.form = copy.deepcopy(form)
            self.generation += 1
            self.preview_result = None

    def new(self):
        with self.lock:
            if self.view()["alive"]:
                raise ValueError("wait for the current rule to stop")
            if self.config is not None and self.status.get("enabled"):
                raise ValueError("pause the current rule first")
            self.config = None
            self.initialized = False
            self.preview_result = None
            self.status = {}
            self.error = None
            self.generation += 1

    def preview(self):
        with self.lock:
            if self.command_busy or self.config is not None or self.closing:
                raise ValueError("operation busy")
            form = copy.deepcopy(self.form)
            generation = self.generation
            self.command_busy = True
            self.error = None

            def work():
                result = rs.preview(**form, state_dir=str(self.home / uuid.uuid4().hex))
                with self.lock:
                    if generation == self.generation and not self.closing:
                        self.preview_result = result
                        self._event("preview", generation=generation)

            self._spawn(work, "preview")

    def _start(self, initialize):
        with self.lock:
            if self.view()["alive"] or self.command_busy or self.closing:
                raise ValueError("wait for previous operations to exit")
            if initialize:
                if self.initialized:
                    raise ValueError("already initialized; resume instead")
                if self.preview_result is None and self.config is None:
                    raise ValueError("preview required")
                c = copy.deepcopy(self.config or self.preview_result["config"])
            else:
                if self.config is None or not self.initialized:
                    raise ValueError("initialized saved rule required")
                c = copy.deepcopy(self.config)
            self.config = c
            self.cancel = threading.Event()
            self.stop = threading.Event()
            self.error = None
            self.worker_started = False
            self.command_busy = True
            self.run_id = uuid.uuid4().hex

            def work():
                store = None
                try:
                    if not initialize:
                        load_rule(self.home, c["state_dir"], self.simulation)
                    if self.cancel.is_set():
                        return
                    store = tr.Store(c)
                    with self.ownership_lock:
                        self.owns_worker = True
                    if initialize:
                        save_rule(c, self.simulation)
                        c2 = rs.enable(
                            c,
                            adapter_factory=self._factory,
                            cancelled=self.cancel.is_set,
                            _store=store,
                        )
                        store.c = c2
                        save_rule(c2, self.simulation)
                        with self.lock:
                            self.config = c2
                        self._event("baseline_committed")
                    else:
                        if self.cancel.is_set():
                            return
                        ns.set_active(store, True)
                    with self.lock:
                        self.initialized = True
                        self.command_busy = False
                    if self.cancel.is_set():
                        return
                    with self.lock:
                        self.worker_started = True
                    self._event("worker_started", run_id=self.run_id)
                    self.run_fn(
                        store,
                        live=True,
                        stop_event=self.stop,
                        adapter_factory=self._factory,
                        run_id=self.run_id,
                        dispatch_interval=self.interval,
                    )
                finally:
                    try:
                        if store is not None:
                            with self.ownership_lock:
                                try:
                                    ns.set_active(store, False)
                                finally:
                                    store.close()
                                    self.owns_worker = False
                    finally:
                        with self.lock:
                            self.worker_started = False
                            self.command_busy = False
                        self._event("worker_exited", run_id=self.run_id)

            self.worker = self._spawn(work, "worker")

    def _factory(self, c, paused):
        factory = self.adapter_factory or tr.make_adapter
        return factory(c, lambda: paused() or self.cancel.is_set())

    def enable(self):
        self._start(True)

    def resume(self):
        self._start(False)

    def pause(self):
        with self.lock:
            self.generation += 1
            self.preview_result = None
            self.cancel.set()
            c = copy.deepcopy(self.config)
            if any(
                t.is_alive() and t.name == "simple-rule-pause" for t in self.threads
            ):
                return

            def work():
                try:
                    if (
                        c is not None
                        and (Path(c["state_dir"]) / "state.sqlite").is_file()
                    ):
                        # Only the current controller's prepared/bound state; reloads
                        # are validated separately. Never instantiate a missing DB.
                        # A second form must never pause a worker owned elsewhere.
                        # Wait out our own startup without blocking the Tk thread.
                        while (
                            self.worker is not None
                            and self.worker.is_alive()
                            and not self.owns_worker
                        ):
                            time.sleep(0.01)
                        with self.ownership_lock:
                            read_status(c)
                            if self.owns_worker:
                                rs.pause(c)
                            else:
                                guard = tr.Store(c)  # same G1 worker/target locks
                                try:
                                    ns.set_active(guard, False)
                                finally:
                                    guard.close()
                finally:
                    self.stop.set()
                self._event("pause_persisted")

            self._spawn(work, "pause")

    def close(self):
        with self.lock:
            if self.closing:
                return
            self.closing = True
        self.pause()

    def load(self, path):
        with self.lock:
            if self.view()["alive"] or self.closing:
                raise ValueError("operation busy")
            self.command_busy = True
            self.error = None
            self.preview_result = None

            def work():
                c, s = load_rule(self.home, path, self.simulation)
                with self.lock:
                    self.config = c
                    self.initialized = s["initialized"]
                    self.status = s
                self._event("loaded_without_resume")

            self._spawn(work, "load")

    def refresh(self):
        with self.lock:
            if self.refresh_busy or self.closing or self.config is None:
                return
            self.refresh_busy = True
            c = copy.deepcopy(self.config)
            rid = self.run_id

            def work():
                try:
                    s = read_status(c)
                except (OSError, ValueError, sqlite3.Error) as exc:
                    raise ValueError("needs_review: " + str(exc)) from exc
                with self.lock:
                    h = s["watcher"]
                    alive = (
                        self.worker is not None
                        and self.worker.is_alive()
                        and self.worker_started
                    )
                    current = (
                        alive
                        and h.get("run_id") == rid
                        and h.get("state") == "running"
                        and h.get("freshness") == "recent"
                    )
                    s["monitoring"] = (
                        "failed"
                        if h.get("state") == "failed"
                        else "listening"
                        if current
                        and h.get("last_scan_at_utc")
                        and h.get("scan_result") == "ok"
                        else "starting"
                        if current and not h.get("last_scan_at_utc")
                        else "health_attention"
                        if alive
                        else "enabled_no_worker"
                        if s["enabled"]
                        else "stopped"
                    )
                    self.status = s
                self._event("status")

            self._spawn(work, "refresh")
