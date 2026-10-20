from contextlib import closing
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


class LedgerCLI(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix=".ledger-test-", dir=PROJECT)
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "tasks.db"

    def cli(self, *arguments, database=None):
        return subprocess.run(
            [sys.executable, str(PROJECT / "tasks.py"), "--db",
             str(self.database if database is None else database), *arguments],
            capture_output=True, text=True, encoding="utf-8", timeout=15,
        )

    def success(self, *arguments, database=None):
        result = self.cli(*arguments, database=database)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def failure(self, *arguments, reason, database=None):
        result = self.cli(*arguments, database=database)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn(reason, result.stderr)

    def test_persistence_titles_json_and_markdown(self):
        titles = ["  中文 café 🐈  ", "don't trim\tthis\nline"]
        for task_id, title in enumerate(titles, 1):
            self.assertEqual(self.success("add", title), f"{task_id}\n")
        self.assertEqual(self.success("done", "2"), "")
        self.assertEqual(self.success("done", "2"), "")
        self.assertEqual(json.loads(self.success("list")), [
            {"id": 1, "title": titles[0], "done": False},
            {"id": 2, "title": titles[1], "done": True},
        ])
        self.assertEqual(
            self.success("export"), f"- [ ] {titles[0]}\n- [x] {titles[1]}\n"
        )

    def test_empty_database(self):
        self.assertEqual(self.success("list"), "[]\n")
        self.assertEqual(self.success("export"), "")

    def test_invalid_titles_and_missing_ids_do_not_change_records(self):
        self.assertEqual(self.success("add", "keep"), "1\n")
        for title in ("", " \t\n", "\u2003\u3000"):
            with self.subTest(title=title):
                self.failure("add", title, reason="title must not be blank")
        for task_id in ("0", "-1", "2"):
            with self.subTest(task_id=task_id):
                self.failure("done", task_id, reason=f"task ID {task_id} does not exist")
        self.assertEqual(json.loads(self.success("list")), [
            {"id": 1, "title": "keep", "done": False},
        ])

    def test_argument_failures(self):
        for arguments, reason in [
            ((), "required"), (("add",), "required"),
            (("done", "abc"), "invalid int value"), (("unknown",), "invalid choice"),
        ]:
            with self.subTest(arguments=arguments):
                self.failure(*arguments, reason=reason)

    def test_database_errors_preserve_the_cause_and_empty_stdout(self):
        self.failure("list", database=Path(self.directory.name),
                     reason="unable to open database file")
        self.database.write_bytes(b"not a SQLite database")
        self.failure("list", reason="file is not a database")

    def test_failed_write_rolls_back_and_preserves_sqlite_reason(self):
        self.success("list")
        with closing(sqlite3.connect(self.database)) as database, database:
            database.execute(
                "CREATE TRIGGER reject_task BEFORE INSERT ON tasks "
                "BEGIN SELECT RAISE(ABORT, 'specific write failure'); END"
            )
        self.failure("add", "rejected", reason="specific write failure")
        self.assertEqual(self.success("list"), "[]\n")

    def test_commit_failure_prints_no_success_and_rolls_back(self):
        self.success("list")
        with closing(sqlite3.connect(self.database)) as reader:
            reader.execute("BEGIN")
            reader.execute("SELECT * FROM tasks").fetchall()
            self.failure("add", "blocked", reason="database is locked")
            reader.rollback()
        self.assertEqual(self.success("list"), "[]\n")

    def test_existing_database_compatibility_on_copy(self):
        existing = PROJECT / "existing.db"
        original = hashlib.sha256(existing.read_bytes()).digest()
        with closing(sqlite3.connect(existing.as_uri() + "?mode=ro", uri=True)) as database:
            rows = database.execute("SELECT * FROM tasks ORDER BY id").fetchall()
            schema = database.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
            sequence = database.execute(
                "SELECT seq FROM sqlite_sequence WHERE name = 'tasks'"
            ).fetchone()
        next_id = max([sequence[0] if sequence else 0, *(row[0] for row in rows)]) + 1
        shutil.copyfile(existing, self.database)
        self.assertEqual(json.loads(self.success("list")), [
            {"id": task_id, "title": title, "done": bool(done)}
            for task_id, title, done in rows
        ])
        markdown = "\n".join(
            f"- [{'x' if done else ' '}] {title}" for _, title, done in rows
        )
        self.assertEqual(self.success("export"), markdown + "\n" if markdown else "")
        self.assertEqual(self.success("add", "new task"), f"{next_id}\n")
        completed_id = rows[0][0] if rows else next_id
        self.assertEqual(self.success("done", str(completed_id)), "")
        expected = [
            (task_id, title, 1 if task_id == completed_id else done)
            for task_id, title, done in [*rows, (next_id, "new task", 0)]
        ]
        with closing(sqlite3.connect(self.database)) as database:
            self.assertEqual(
                database.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall(),
                schema,
            )
            self.assertEqual(database.execute(
                "SELECT seq FROM sqlite_sequence WHERE name = 'tasks'"
            ).fetchone(), (next_id,))
            self.assertEqual(database.execute("SELECT * FROM tasks ORDER BY id").fetchall(),
                             expected)
        self.assertEqual(hashlib.sha256(existing.read_bytes()).digest(), original)


if __name__ == "__main__":
    unittest.main()
