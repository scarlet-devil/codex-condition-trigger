"""Version-specific, read-only Desktop metadata source (no conversation history)."""

import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from cwd_paths import cwd_matches, normalize_windows_cwd
from experimental.conversation_catalog import (
    MAX_METADATA_BYTES,
    MAX_RECORDS,
    select_candidates,
)

FIELDS = (
    "id",
    "name",
    "title",
    "cwd",
    "rollout_path",
    "updated_at",
    "source",
    "thread_source",
    "agent_path",
    "archived",
)


def read_catalog(path, *, search=""):
    path = Path(path).resolve(strict=True)
    # mode=ro retains WAL semantics; immutable=1 would silently omit recent rows.
    with closing(
        sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
    ) as db:
        try:
            deadline = time.monotonic() + 2
            db.set_progress_handler(lambda: time.monotonic() > deadline, 1000)
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")
            cols = {r[1] for r in db.execute("PRAGMA table_info(threads)")}
            edges = {r[1] for r in db.execute("PRAGMA table_info(thread_spawn_edges)")}
            if (
                not set(FIELDS) <= cols
                or not {"parent_thread_id", "child_thread_id"} <= edges
            ):
                raise ValueError("catalog_schema_unavailable")
            # Budget before fetch, in one read transaction. The query projects only
            # these fields, never SELECT * or first_user_message/history columns.
            obj = ",".join("'" + k + "',t." + k for k in FIELDS)
            picked = (
                "WITH picked AS (SELECT json_object("
                + obj
                + ") AS payload FROM threads t "
                "WHERE archived=0 AND source IN ('vscode','cli') "
                "AND thread_source IN ('user','agent_created_thread') "
                "AND (agent_path IS NULL OR agent_path IN ('','/root')) "
                "AND NOT EXISTS (SELECT 1 FROM thread_spawn_edges e WHERE e.child_thread_id=t.id) "
                "AND (?='' OR instr(lower(coalesce(name,'')||' '||title||' '||cwd),lower(?))>0) "
                "ORDER BY updated_at DESC,id LIMIT 501) "
            )
            params = (search, search)
            count, size = db.execute(
                picked
                + "SELECT count(*),coalesce(sum(length(CAST(payload AS BLOB))),0)+count(*)+2 FROM picked",
                params,
            ).fetchone()
            if count > MAX_RECORDS:
                raise ValueError("catalog_record_limit: narrow search or project")
            if size > MAX_METADATA_BYTES:
                raise ValueError("catalog_metadata_limit: narrow search or project")
            rows = [
                json.loads(r[0])
                for r in db.execute(picked + "SELECT payload FROM picked", params)
            ]
        finally:
            db.rollback()
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("duplicate_catalog_id")
    result = []
    for row in rows:
        try:
            normalize_windows_cwd(row["cwd"])
        except ValueError:
            continue  # unsupported cwd representation, never selectable
        selected = select_candidates([row], row["cwd"])
        if selected:
            item = selected[0]
            length = 8
            while any(
                r["id"] != item["id"] and r["id"][-length:] == item["id"][-length:]
                for r in rows
            ):
                length += 4
            item["short_id"] = item["id"][-length:]
            item["display_label"] = (
                f"{item['display_name']} | {item['cwd']} | {item['updated_at']} | {item['short_id']}"
            )
            result.append(item)
    return result


def verify_selection(selection, *, reader=None):
    if selection.get("selection_key") != selection.get("id"):
        raise ValueError("selection_identity_changed")
    p = Path(selection["rollout_path"])
    if reader is None:
        with p.open("rb") as f:
            first = f.readline(65537)
    else:
        first = reader(p)
    if len(first) > 65536:
        raise ValueError("rollout_identity_limit")
    try:
        meta = json.loads(first)
        payload = meta["payload"]
        valid = (
            meta["type"] == "session_meta"
            and payload["id"] == selection["id"]
            and cwd_matches(payload["cwd"], selection["cwd"])
        )
    except (ValueError, KeyError, TypeError):
        valid = False
    if not valid:
        raise ValueError("rollout_identity_mismatch")
