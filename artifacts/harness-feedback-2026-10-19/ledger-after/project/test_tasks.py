from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parent


class TaskCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".ledger-test-", dir=PROJECT)
        self.addCleanup(self.temporary.cleanup)
        self.database = Path(self.temporary.name) / "tasks.db"

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(PROJECT / "tasks.py"),
             "--db", str(self.database), *arguments],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=15,
        )

    def success(self, *arguments):
        result = self.run_cli(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def failure(self, *arguments, reason):
        result = self.run_cli(*arguments)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn(reason, result.stderr)

    def test_persistent_round_trip_and_exact_outputs(self):
        titles = ["  中文 🐍 O'Reilly\t ", "line one\nline two"]
        self.assertEqual(self.success("add", titles[0]), "1\n")
        self.assertEqual(self.success("add", titles[1]), "2\n")
        expected = [
            {"id": 1, "title": titles[0], "done": False},
            {"id": 2, "title": titles[1], "done": False},
        ]
        self.assertEqual(self.success("list"), json.dumps(expected, ensure_ascii=False) + "\n")
        self.assertEqual(self.success("done", "2"), "")
        self.assertEqual(self.success("done", "2"), "")
        expected[1]["done"] = True
        self.assertEqual(json.loads(self.success("list")), expected)
        self.assertEqual(self.success("export"), f"- [ ] {titles[0]}\n- [x] {titles[1]}\n")

    def test_fresh_database_and_schema(self):
        self.assertEqual(self.success("export"), "")
        self.assertEqual(self.success("list"), "[]\n")
        with closing(sqlite3.connect(self.database)) as database:
            columns = database.execute("PRAGMA table_info(tasks)").fetchall()
            self.assertEqual([row[1:3] for row in columns],
                             [("id", "INTEGER"), ("title", "TEXT"), ("done", "INTEGER")])
            with self.assertRaises(sqlite3.IntegrityError):
                database.execute("INSERT INTO tasks(title, done) VALUES ('bad', 2)")

    def test_rename_preserves_titles_ids_and_completion_states(self):
        self.assertEqual(self.success("add", "pending"), "1\n")
        self.assertEqual(self.success("add", "finished"), "2\n")
        self.assertEqual(self.success("done", "2"), "")
        titles = ["  新标题 🐍 O'Reilly\t ", "已完成\n第二行"]
        for task_id, title in enumerate(titles, 1):
            self.assertEqual(self.success("rename", str(task_id), title), "")
            self.assertEqual(self.success("rename", str(task_id), title), "")
        expected = [
            {"id": 1, "title": titles[0], "done": False},
            {"id": 2, "title": titles[1], "done": True},
        ]
        self.assertEqual(json.loads(self.success("list")), expected)
        self.assertEqual(self.success("export"), f"- [ ] {titles[0]}\n- [x] {titles[1]}\n")
        for title in ("", " \t\n", "\u2003\u3000"):
            with self.subTest(title=title):
                self.failure("rename", "1", title, reason="title must not be blank")
        self.failure("rename", "99", "missing", reason="task ID 99 does not exist")
        self.failure("rename", "wrong", "title", reason="invalid int value")
        self.failure("rename", "1", reason="required")
        self.assertEqual(json.loads(self.success("list")), expected)
        self.assertEqual(self.success("add", "next"), "3\n")

    def test_invalid_operations_have_no_stdout(self):
        for title in ("", " \t\n", "\u2003\u3000"):
            with self.subTest(title=title):
                self.failure("add", title, reason="title must not be blank")
        self.failure("done", "99", reason="task ID 99 does not exist")
        self.failure("done", "wrong", reason="invalid int value")
        self.failure("add", reason="required")
        self.failure("unknown", reason="invalid choice")
        self.assertEqual(self.success("list"), "[]\n")

    def test_database_errors_retain_the_original_cause(self):
        self.database.write_bytes(b"this is not a SQLite database")
        self.failure("list", reason="file is not a database")
        self.database = self.database.parent / "missing-directory" / "tasks.db"
        self.failure("add", "task", reason="unable to open database file")

    def test_commit_failure_reports_no_success_and_rolls_back(self):
        self.assertEqual(self.success("add", "original"), "1\n")
        with closing(sqlite3.connect(self.database)) as reader:
            reader.execute("BEGIN")
            reader.execute("SELECT * FROM tasks").fetchall()
            # A reader permits INSERT but blocks its COMMIT in SQLite's default journal mode.
            self.failure("add", "must roll back", reason="database is locked")
            self.failure("rename", "1", "must roll back", reason="database is locked")
            reader.rollback()
        self.assertEqual(json.loads(self.success("list")),
                         [{"id": 1, "title": "original", "done": False}])
        self.assertEqual(self.success("add", "next"), "2\n")

    def test_existing_database_compatibility_without_changing_original(self):
        existing = PROJECT / "existing.db"
        original_hash = hashlib.sha256(existing.read_bytes()).digest()
        with closing(sqlite3.connect(existing.as_uri() + "?mode=ro", uri=True)) as database:
            rows = database.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()
            schema = database.execute("SELECT sql FROM sqlite_master WHERE name='tasks'").fetchone()
            sequence = database.execute("SELECT seq FROM sqlite_sequence WHERE name='tasks'").fetchone()[0]
            self.assertEqual(database.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
        shutil.copyfile(existing, self.database)
        expected = [{"id": task_id, "title": title, "done": bool(done)}
                    for task_id, title, done in rows]
        self.assertEqual(json.loads(self.success("list")), expected)
        markdown = "\n".join(f"- [{'x' if done else ' '}] {title}" for _, title, done in rows)
        self.assertEqual(self.success("export"), markdown + ("\n" if markdown else ""))
        self.assertEqual(self.success("add", "copy only"), f"{sequence + 1}\n")
        self.assertEqual(self.success("done", str(sequence + 1)), "")
        renamed_rows = []
        for task_id, title, done in rows:
            new_title = f"  改名 🐍 {title}\t "
            self.assertEqual(self.success("rename", str(task_id), new_title), "")
            renamed_rows.append((task_id, new_title, done))
        with closing(sqlite3.connect(self.database)) as database:
            self.assertEqual(database.execute("SELECT sql FROM sqlite_master WHERE name='tasks'").fetchone(), schema)
            self.assertEqual(database.execute("SELECT id,title,done FROM tasks ORDER BY id").fetchall(),
                             renamed_rows + [(sequence + 1, "copy only", 1)])
        self.assertEqual(hashlib.sha256(existing.read_bytes()).digest(), original_hash)


if __name__ == "__main__":
    unittest.main()
