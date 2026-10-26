"""One-shot G3 transport budget. Importing never opens Desktop."""

import json
import math
import struct
import sys
import threading
import time
from pathlib import Path
import desktop_ipc as ipc
import trigger as tr

METHOD_KEYS = {
    "initialize": "initialize",
    "thread-owner-discovery": "owner_discovery",
    "thread-follower-load-complete-history": "history",
    "thread-follower-start-turn": "start_write_attempts",
}


class BudgetStopped(ValueError):
    """Latched failure; retain intent and never retry this trial."""


class StartWindowClosed(ipc.NotDispatched):
    """Admission refused before the first byte of a new model request."""


def preserve_primary(primary, operation, label):
    """Keep an active failure primary; a lone cleanup failure still raises."""
    try:
        return operation()
    except BaseException as secondary:
        if primary is None:
            raise
        note = f"{label}: {type(secondary).__name__}: {secondary}"
        primary.__notes__ = getattr(primary, "__notes__", []) + [note]


class G3Budget:
    def __init__(self, contract, receipt, *, wall=time.time, mono=time.monotonic):
        self.contract, self.receipt = contract, Path(receipt)
        self.wall, self.mono = wall, mono
        self.lock = threading.RLock()
        reserve = contract.get("min_start_remaining_seconds", 180)
        if (
            isinstance(reserve, bool)
            or not isinstance(reserve, (int, float))
            or not math.isfinite(reserve)
            or not 0 < reserve <= 480
        ):
            raise BudgetStopped("invalid start reserve")
        self.start_reserve = reserve
        if (
            not 0 < contract["duration_seconds"] <= 480
            or not wall() < contract["expires_at_epoch"] <= wall() + 480
        ):
            raise BudgetStopped("invalid fixed trial window")
        self.end = mono() + min(
            contract["duration_seconds"], contract["expires_at_epoch"] - wall()
        )
        self.reason, self.stop_mono = None, None
        self.started_clients = set()
        self.counts = {k: 0 for k in contract["limits"]}
        self.counts.update(
            rx_known_bytes=0,
            rx_upper_bytes=0,
            rollout_known_bytes=0,
            rollout_upper_bytes=0,
            tx_known_bytes=0,
            tx_upper_bytes=0,
            cleanup_frames=0,
        )
        self.events = []
        self.receipt.parent.mkdir(parents=True, exist_ok=True)
        with self.receipt.open("x", encoding="utf8") as f:
            f.write("{}\n")
        self._persist()

    def _persist(self):
        with self.lock:
            data = dict(
                schema=1,
                contract=self.contract,
                reason=self.reason,
                counts=self.counts,
                started_clients=sorted(self.started_clients),
                events=self.events,
                monotonic_deadline=self.end,
            )
            try:
                tr.atomic_write(self.receipt, (tr.encode(data) + "\n").encode())
            except BaseException as error:
                self.reason = self.reason or "evidence_write_failed"
                self.stop_mono = self.stop_mono or self.mono()
                raise BudgetStopped("evidence_write_failed") from error

    def stop(self, reason):
        with self.lock:
            if self.reason is None:
                self.reason, self.stop_mono = reason, self.mono()
                self.events.append(dict(event="stop", reason=reason, at=self.wall()))
                self._persist()

    def reject(self, reason):
        self.stop(reason)
        raise BudgetStopped(self.reason)

    def stop_for_error(self, reason, primary):
        preserve_primary(primary, lambda: self.stop(reason), "stop evidence failure")

    def guard(self):
        with self.lock:
            if self.reason:
                raise BudgetStopped(self.reason)
            if (
                self.contract.get("stop_path")
                and Path(self.contract["stop_path"]).exists()
            ):
                self.reject("operator_stop")
            if (
                self.wall() >= self.contract["expires_at_epoch"]
                or self.mono() >= self.end
            ):
                self.reject("trial_expired")

    def clipped(self, deadline):
        self.guard()
        return min(
            deadline,
            self.end,
            self.mono() + max(0, self.contract["expires_at_epoch"] - self.wall()),
        )

    def admit_start(self):
        """Reserve completion time; this is not a promise of model completion."""
        with self.lock:
            self.guard()
            remaining = min(
                self.end - self.mono(), self.contract["expires_at_epoch"] - self.wall()
            )
            if remaining < self.start_reserve:
                self.event(
                    "start_refused",
                    remaining_seconds=remaining,
                    required_seconds=self.start_reserve,
                    known_unsent=True,
                )
                self.stop("insufficient_start_time")
                raise StartWindowClosed("insufficient_start_time")

    def take(self, key, amount=1):
        with self.lock:
            self.guard()
            if self.counts[key] + amount > self.contract["limits"][key]:
                self.reject("limit_" + key)
            self.counts[key] += amount

    def reserve_frame(self, item):
        with self.lock:
            self.guard()
            self.take("non_cleanup_tx_frames")
            method, p = item.get("method"), item.get("params", {})
            if (
                method != "initialize"
                and p.get("conversationId") != self.contract["thread_id"]
            ):
                self.reject("target_conflict")
            if item.get("type") == "request":
                if method not in METHOD_KEYS:
                    self.reject("unexpected_rpc")
                self.take("total_requests")
                self.take(METHOD_KEYS[method])
                if method == "thread-follower-start-turn":
                    request = p.get("turnStart", {}).get("request", {})
                    client = request.get("clientUserMessageId")
                    if (
                        request.get("threadId") != self.contract["thread_id"]
                        or not client
                        or p.get("isSteering") is not False
                        or client in self.started_clients
                    ):
                        self.reject("duplicate_or_conflicting_start")
                    self.started_clients.add(client)
            elif not (
                item.get("type") == "broadcast"
                and method == "thread-stream-following-changed"
                and p.get("following") is True
            ):
                self.reject("unexpected_broadcast")
            self.events.append(
                dict(
                    event="tx_intent",
                    method=method,
                    request_id=item.get("requestId"),
                    at=self.wall(),
                )
            )
            self._persist()

    def transfer(self, kind, requested, operation):
        """Reserve worst case first; failed OS reads retain an unknown upper bound."""
        with self.lock:
            self.guard()
            upper, known = kind + "_upper_bytes", kind + "_known_bytes"
            limit = "total_rx_bytes" if kind == "rx" else "total_rollout_bytes"
            if self.counts[upper] + requested > self.contract["limits"][limit]:
                self.reject("limit_" + limit)
            self.counts[upper] += requested
            self._persist()
            try:
                result = operation()
            except BaseException as error:
                self.events.append(
                    dict(
                        event="read_unknown",
                        kind=kind,
                        reserved=requested,
                        error=type(error).__name__,
                        at=self.wall(),
                    )
                )
                self.stop_for_error("read_failed_" + type(error).__name__, error)
                raise
            actual = len(result)
            if actual > requested:
                self.reject("reader_contract_violation")
            self.counts[known] += actual
            self.counts[upper] -= requested - actual
            self._persist()
            self.guard()
            return result

    def read_rollout(self, path):
        with self.lock:
            self.take("rollout_reads")
            self._persist()
        size = Path(path).stat().st_size
        if size > ipc.MAX_ROLLOUT:
            self.reject("rollout_file_limit")
        with Path(path).open("rb") as f:
            data = self.transfer("rollout", size + 1, lambda: f.read(size + 1))
        if len(data) != size:
            self.reject("rollout_changed_while_reading")
        return data

    def read_identity(self, path):
        with self.lock:
            self.take("rollout_reads")
            self._persist()
        with Path(path).open("rb") as f:
            return self.transfer("rollout", 65537, lambda: f.readline(65537))

    def event(self, event, **fields):
        with self.lock:
            self.events.append(dict(event=event, at=self.wall(), **fields))
            self._persist()


class BudgetPipe:
    def __init__(self, inner, budget):
        self.inner, self.b = inner, budget
        self.header, self.payload_size, self.following = True, None, False

    def server_image(self):
        self.b.guard()
        return self.inner.server_image()

    def write(self, data, deadline, before_write=None):
        if len(data) < 5 or struct.unpack("<I", data[:4])[0] != len(data) - 4:
            self.b.reject("invalid_tx_frame")
        if len(data) - 4 > self.b.contract["limits"]["max_frame_bytes"]:
            self.b.reject("tx_frame_limit")
        item = json.loads(data[4:])
        cleanup = (
            item.get("type") == "broadcast"
            and item.get("method") == "thread-stream-following-changed"
            and item.get("params", {}).get("following") is False
        )
        if cleanup:
            if (
                not self.following
                or item["params"].get("conversationId") != self.b.contract["thread_id"]
            ):
                self.b.reject("unmatched_unsubscribe")
            with self.b.lock:
                self.following = False
                self.b.counts["cleanup_frames"] += 1
                deadline = min(
                    deadline,
                    self.b.mono() + 1,
                    (self.b.stop_mono or self.b.mono()) + 10,
                )
                self.b.event("cleanup_intent")
        else:
            if item.get("method") == "thread-follower-start-turn":
                self.b.admit_start()
            self.b.reserve_frame(item)
            deadline = self.b.clipped(deadline)
        offset = 0

        def guard():
            if not cleanup:
                self.b.guard()
                # Recheck after readonly RPCs, intent persistence and OS setup.
                # A partial write is already ambiguous: never classify it unsent.
                if offset == 0 and item.get("method") == "thread-follower-start-turn":
                    self.b.admit_start()
            return bool(before_write and before_write())

        try:
            while offset < len(data):
                pending = len(data) - offset
                with self.b.lock:
                    if not cleanup:
                        self.b.guard()
                    self.b.counts["tx_upper_bytes"] += pending
                    self.b._persist()
                try:
                    n = self.inner.io(data[offset:], deadline, True, guard)
                except StartWindowClosed:
                    # Only our first-byte callback can establish zero bytes sent.
                    with self.b.lock:
                        self.b.counts["tx_upper_bytes"] -= pending
                        self.b._persist()
                    raise
                if not 0 < n <= pending:
                    self.b.reject("invalid_tx_count")
                with self.b.lock:
                    self.b.counts["tx_known_bytes"] += n
                    self.b.counts["tx_upper_bytes"] -= pending - n
                    self.b._persist()
                offset += n
            if not cleanup and item.get("method") == "thread-stream-following-changed":
                self.following = True
        except BaseException as error:
            self.b.stop_for_error("write_failed_" + type(error).__name__, error)
            raise

    def read(self, size, deadline):
        self.b.guard()
        if self.header:
            if size != 4:
                self.b.reject("missing_frame_header")
            self.b.take("rx_frames")
            self.b._persist()
        elif size != self.payload_size:
            self.b.reject("payload_size_mismatch")
        deadline = self.b.clipped(deadline)
        data = bytearray()
        while len(data) < size:
            n = min(65536, size - len(data))
            part = self.b.transfer("rx", n, lambda: self.inner.io(n, deadline))
            if not part:
                self.b.reject("empty_read")
            data.extend(part)
        if self.header:
            (self.payload_size,) = struct.unpack("<I", data)
            if (
                not 0
                < self.payload_size
                <= self.b.contract["limits"]["max_frame_bytes"]
            ):
                self.b.reject("rx_frame_limit")
            if (
                self.b.counts["rx_upper_bytes"] + self.payload_size
                > self.b.contract["limits"]["total_rx_bytes"]
            ):
                self.b.reject("limit_total_rx_bytes")
        else:
            self.b.event("rx_frame", payload_bytes=size)
            item = json.loads(data)
            if (
                isinstance(item, dict)
                and item.get("method") == "thread-stream-state-changed"
            ):
                params = item.get("params", {})
                if (
                    isinstance(params, dict)
                    and params.get("conversationId") == self.b.contract["thread_id"]
                ):
                    change = params.get("change")
                    if isinstance(change, dict) and change.get("type") == "snapshot":
                        snap = change.get("conversationState")
                        self.b.event(
                            "target_snapshot_unverified",
                            snapshot_serialized_bytes=len(
                                json.dumps(snap, ensure_ascii=False).encode()
                            ),
                            revision=change.get("revision"),
                        )
        self.header = not self.header
        return bytes(data)

    def close(self):
        preserve_primary(sys.exc_info()[1], self.inner.close, "pipe close failure")


def make_client(
    budget, timeout, *, pipe_factory=ipc.WindowsPipe, verifier=ipc.verify_installation
):
    budget.guard()
    pipe = BudgetPipe(pipe_factory(), budget)

    def checked_verifier(p):
        budget.guard()
        began = budget.mono()
        result = verifier(p)
        budget.event(
            "installation",
            seconds=budget.mono() - began,
            archive_bytes=result.get("archive_bytes"),
            archive_sha256=result.get("archive_sha256"),
        )
        budget.guard()
        expected = budget.contract.get("expected_archive_sha256")
        if expected is not None and result.get("archive_sha256") != expected:
            budget.reject("installation_pin_mismatch")
        return result

    try:
        return ipc.IPCClient(timeout, pipe=pipe, verifier=checked_verifier)
    except BaseException as error:
        preserve_primary(error, pipe.close, "pipe close failure")
        budget.stop_for_error("client_failed_" + type(error).__name__, error)
        raise


class BoundedAdapter(ipc.DesktopAdapter):
    def __init__(self, c, paused, budget):
        self.budget = budget
        budget.guard()
        if c["thread_id"] != budget.contract["thread_id"]:
            budget.reject("config_target_conflict")
        super().__init__(
            c, paused, client_factory=lambda timeout: make_client(budget, timeout)
        )

    def scan(self, **kwargs):
        try:
            return ipc.rollout_state(
                self.c["rollout_path"],
                self.c["thread_id"],
                self.c["expected_cwd"],
                reader=self.budget.read_rollout,
                **kwargs,
            )
        except BaseException as error:
            self.budget.stop_for_error("rollout_failed_" + type(error).__name__, error)
            raise

    def observe(self, row):
        result = super().observe(row)
        if result and (
            result.get("uncertain")
            or result.get("execution_outcome") in ("failed", "interrupted")
        ):
            self.budget.stop("native_observation_not_successful")
        return result

    def inspect(self, row):
        self.budget.guard()
        try:
            result = super().inspect(row)
            if row.get("state", "ready") == "ready":
                if not result.get("can_send"):
                    self.budget.reject("target_not_ready_" + str(result.get("reason")))
                self.budget.event("fresh_state", **result["fresh_state"])
            return result
        except BaseException as error:
            self.budget.stop_for_error("inspect_failed_" + type(error).__name__, error)
            raise

    def send(self, row, text, metadata):
        self.budget.guard()
        try:
            result = super().send(row, text, metadata)
            self.budget.event(
                "native_acceptance",
                batch_id=row["id"],
                client_id=row["client_id"],
                turn_id=result["turn_id"],
                request_id=metadata["request_id"],
            )
            return result
        except BaseException as error:
            self.budget.stop_for_error("send_failed_" + type(error).__name__, error)
            raise

    def prepare(self, row):
        self.budget.admit_start()
        return super().prepare(row)
