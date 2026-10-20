import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parent


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=PROJECT, prefix=".ledger-test-")
        self.addCleanup(self.temporary.cleanup)
        self.db = Path(self.temporary.name) / "tasks.db"

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(PROJECT / "tasks.py"), "--db", str(self.db), *arguments],
            capture_output=True, text=True, timeout=15,
        )

    def success(self, *arguments):
        result = self.run_cli(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def failure(self, *arguments, cause):
        result = self.run_cli(*arguments)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn(cause, result.stderr)

    def test_persistent_commands_preserve_titles_and_output(self):
        self.assertEqual(self.success("list"), "[]\n")
        self.assertEqual(self.success("export"), "")
        titles = ["  中文 café 📝  ", "quote ' and newline\nsecond line"]
        ids = [int(self.success("add", title)) for title in titles]
        self.assertEqual(ids, [1, 2])
        self.assertEqual(self.success("done", "2"), "")
        self.assertEqual(self.success("done", "2"), "")
        self.assertEqual(json.loads(self.success("list")), [
            {"id": 1, "title": titles[0], "done": False},
            {"id": 2, "title": titles[1], "done": True},
        ])
        self.assertEqual(self.success("export"),
                         f"- [ ] {titles[0]}\n- [x] {titles[1]}\n")
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall(),
                             [(1, titles[0], 0), (2, titles[1], 1)])

    def test_invalid_input_has_no_success_output_or_data_changes(self):
        self.failure("add", " \t\n\u2003", cause="title must not be blank")
        self.assertFalse(self.db.exists())
        self.success("add", "keep")
        self.failure("done", "999", cause="task ID 999 does not exist")
        self.failure("done", "invalid", cause="invalid int value")
        self.failure("done", str(2**100), cause="too large")
        self.assertEqual(json.loads(self.success("list")),
                         [{"id": 1, "title": "keep", "done": False}])

    def test_storage_failures_preserve_original_cause(self):
        self.db.write_bytes(b"not a sqlite database")
        self.failure("list", cause="file is not a database")
        self.db.unlink()
        self.db = self.db / "missing" / "tasks.db"
        self.failure("add", "title", cause="unable to open database file")

    def test_sql_failure_rolls_back_without_output(self):
        self.success("list")
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TRIGGER reject_insert BEFORE INSERT ON tasks "
                       "BEGIN SELECT RAISE(ABORT, 'original rejection'); END")
        self.failure("add", "rejected", cause="original rejection")
        self.assertEqual(self.success("list"), "[]\n")

    def test_commit_failure_does_not_print_id_or_persist_task(self):
        self.success("add", "keep")
        with sqlite3.connect(self.db) as reader:
            reader.execute("BEGIN")
            reader.execute("SELECT * FROM tasks").fetchall()
            self.failure("add", "cannot commit", cause="database is locked")
        self.assertEqual(json.loads(self.success("list")),
                         [{"id": 1, "title": "keep", "done": False}])

    def test_existing_database_compatibility_without_modifying_original(self):
        existing = PROJECT / "existing.db"
        before = hashlib.sha256(existing.read_bytes()).hexdigest()
        shutil.copyfile(existing, self.db)
        with sqlite3.connect(f"file:{existing}?mode=ro", uri=True) as original:
            rows = original.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()
            sequence = original.execute(
                "SELECT seq FROM sqlite_sequence WHERE name = 'tasks'"
            ).fetchone()[0]
            self.assertEqual(original.execute("PRAGMA integrity_check").fetchone(), ("ok",))
        self.assertEqual(json.loads(self.success("list")), [
            {"id": task_id, "title": title, "done": bool(done)}
            for task_id, title, done in rows
        ])
        self.assertEqual(self.success("add", "new task"), f"{sequence + 1}\n")
        self.assertEqual(self.success("done", str(rows[0][0])), "")
        self.assertEqual(hashlib.sha256(existing.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
