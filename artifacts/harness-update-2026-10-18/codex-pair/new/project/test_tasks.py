import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent


class TaskCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "tasks.sqlite3"

    def cli(self, *arguments, db=None):
        return subprocess.run(
            [sys.executable, str(ROOT / "tasks.py"), "--db", str(db or self.db), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def success(self, *arguments):
        result = self.cli(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def assert_failure(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.strip())

    def test_persistent_workflow_and_exact_output(self):
        first = int(self.success("add", "学习 Python 标准库"))
        second = int(self.success("add", "buy milk"))
        self.assertLess(first, second)
        expected = [
            {"id": first, "title": "学习 Python 标准库", "done": False},
            {"id": second, "title": "buy milk", "done": False},
        ]
        tasks = json.loads(self.success("list"))
        self.assertEqual(tasks, expected)
        self.assertTrue(all(type(task["done"]) is bool for task in tasks))
        self.assertEqual(self.success("done", str(second)), "")
        self.assertEqual(self.success("done", str(second)), "")
        expected[1]["done"] = True
        self.assertEqual(json.loads(self.success("list")), expected)
        self.assertEqual(
            self.success("export"), "- [ ] 学习 Python 标准库\n- [x] buy milk\n"
        )

    def test_empty_ledger(self):
        self.assertEqual(self.success("list"), "[]\n")
        self.assertEqual(self.success("export"), "")

    def test_invalid_operations_leave_tasks_unchanged(self):
        self.success("add", "保留这个任务")
        before = self.success("list")
        for title in ("", " \t\n", "\u3000"):
            self.assert_failure(self.cli("add", title))
        for task_id in ("999", "-1", "not-an-integer"):
            self.assert_failure(self.cli("done", task_id))
        self.assert_failure(self.cli("add"))
        self.assertEqual(self.success("list"), before)

    def test_database_errors_have_no_success_output(self):
        missing_parent = Path(self.directory.name) / "missing" / "tasks.db"
        self.assert_failure(self.cli("add", "hello", db=missing_parent))
        self.db.write_text("not a sqlite database", encoding="utf-8")
        self.assert_failure(self.cli("list"))


if __name__ == "__main__":
    unittest.main()
