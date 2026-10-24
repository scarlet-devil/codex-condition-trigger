import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


class CatalogSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state_5.sqlite"
        self.db = sqlite3.connect(self.path)
        self.addCleanup(self.db.close)
        self.db.execute(
            "CREATE TABLE threads(id TEXT PRIMARY KEY,name TEXT,title TEXT,cwd TEXT,rollout_path TEXT,updated_at INTEGER,source TEXT,thread_source TEXT,agent_path TEXT,archived INTEGER)"
        )
        self.db.execute(
            "CREATE TABLE thread_spawn_edges(parent_thread_id TEXT,child_thread_id TEXT,status TEXT)"
        )

    def insert(self, id="one", **kw):
        row = {
            "id": id,
            "name": "",
            "title": "same",
            "cwd": r"D:\project",
            "rollout_path": r"D:\session.jsonl",
            "updated_at": 1,
            "source": "vscode",
            "thread_source": "user",
            "agent_path": None,
            "archived": 0,
        }
        row.update(kw)
        self.db.execute(
            "INSERT INTO threads VALUES(" + ",".join("?" * 10) + ")",
            tuple(row.values()),
        )
        self.db.commit()

    def test_filters_names_projects_and_source_database_unchanged(self):
        from simple_catalog import read_catalog

        self.insert("one", name="renamed")
        self.insert("two", title="renamed", cwd=r"E:\project")
        self.insert("child")
        self.insert("archived", archived=1)
        self.db.execute(
            "INSERT INTO thread_spawn_edges VALUES ('one','child','completed')"
        )
        self.db.commit()
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        rows = read_catalog(self.path)
        self.assertEqual([r["id"] for r in rows], ["one", "two"])
        self.assertEqual([r["display_name"] for r in rows], ["renamed", "renamed"])
        self.assertNotEqual(rows[0]["display_label"], rows[1]["display_label"])
        self.assertEqual(read_catalog(self.path, search="E:\\")[0]["id"], "two")
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)

    def test_row_budget_and_filter_before_fetch(self):
        from simple_catalog import read_catalog

        for i in range(501):
            self.insert(str(i), title="findme" if i == 500 else "many")
        with self.assertRaisesRegex(ValueError, "catalog_record_limit"):
            read_catalog(self.path)
        self.assertEqual(len(read_catalog(self.path, search="findme")), 1)

    def test_metadata_budget_is_checked_before_materialization(self):
        from simple_catalog import read_catalog

        self.insert(title="x" * 1048576)
        with self.assertRaisesRegex(ValueError, "catalog_metadata_limit"):
            read_catalog(self.path)

    def test_unknown_schema_and_missing_database_are_not_created(self):
        from simple_catalog import read_catalog

        missing = self.path.parent / "missing.sqlite"
        with self.assertRaises((OSError, ValueError, sqlite3.Error)):
            read_catalog(missing)
        self.assertFalse(missing.exists())
        self.db.execute("DROP TABLE thread_spawn_edges")
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "catalog_schema_unavailable"):
            read_catalog(self.path)

    def test_metadata_boundary_error_is_not_silently_filtered(self):
        from simple_catalog import FIELDS, MAX_METADATA_BYTES, read_catalog

        self.insert(title="")
        fields = ",".join("'" + k + "'," + k for k in FIELDS)
        payload = self.db.execute(
            "SELECT json_object(" + fields + ") FROM threads"
        ).fetchone()[0]
        # Compact SQL JSON fits, but the reused selector's spaced encoding
        # exceeds its bound. It must report that limit, never return no rows.
        self.db.execute(
            "UPDATE threads SET title=?",
            ("x" * (MAX_METADATA_BYTES - len(payload.encode()) - 8),),
        )
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "catalog_metadata_limit"):
            read_catalog(self.path)

    def test_selected_rollout_reads_only_identity_line(self):
        from simple_catalog import verify_selection

        p = self.path.parent / "rollout.jsonl"
        cwd = str(p.parent)
        p.write_bytes(
            (
                json.dumps(
                    {"type": "session_meta", "payload": {"id": "one", "cwd": cwd}}
                )
                + "\nnot valid history"
            ).encode()
        )
        s = {"id": "one", "selection_key": "one", "cwd": cwd, "rollout_path": str(p)}
        self.assertIsNone(verify_selection(s))
        with self.assertRaises(ValueError):
            verify_selection(dict(s, id="two", selection_key="two"))
        with self.assertRaises(ValueError):
            verify_selection(dict(s, selection_key="two"))

    def test_extended_cwd_and_unsupported_source(self):
        from simple_catalog import read_catalog

        self.insert("one", cwd=r"\\?\D:\project")
        self.insert("two", source="unknown")
        self.insert("three", agent_path="/root/child")
        self.assertEqual([r["id"] for r in read_catalog(self.path)], ["one"])
