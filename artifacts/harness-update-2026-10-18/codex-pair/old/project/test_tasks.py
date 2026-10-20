import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("tasks.py")


class TaskLedgerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=SCRIPT.parent)
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "tasks.sqlite3"

    def run_cli(self, *arguments, success=True, db=None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--db", str(db or self.db), *arguments],
            capture_output=True,
            text=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(result.stderr.strip())
            self.assertEqual(result.stdout, "")
        return result

    def test_persistent_workflow_and_exact_output(self):
        self.assertEqual(self.run_cli("list").stdout, "[]\n")
        self.assertEqual(self.run_cli("export").stdout, "")
        titles = ["买牛奶 and bread", "  保留两侧空格  ", "引号 ' 与 SQL ; --"]
        ids = [int(self.run_cli("add", title).stdout) for title in titles]
        self.assertEqual(ids, sorted(set(ids)))
        self.assertEqual(self.run_cli("done", str(ids[1])).stdout, "")
        # Repeating completion is harmless; every invocation is a new process.
        self.run_cli("done", str(ids[1]))
        tasks = json.loads(self.run_cli("list").stdout)
        self.assertEqual(tasks, [
            {"id": task_id, "title": title, "done": index == 1}
            for index, (task_id, title) in enumerate(zip(ids, titles))
        ])
        for task in tasks:
            self.assertEqual(set(task), {"id", "title", "done"})
            self.assertIs(type(task["done"]), bool)
        self.assertEqual(
            self.run_cli("export").stdout,
            "".join(f"- [{'x' if i == 1 else ' '}] {title}\n"
                    for i, title in enumerate(titles)),
        )

    def test_invalid_operations_do_not_change_tasks(self):
        task_id = self.run_cli("add", "保留的任务").stdout.strip()
        before = self.run_cli("list").stdout
        for title in ("", " \t\n", "\u3000"):
            self.run_cli("add", title, success=False)
        for task in ("999", "-1", "not-an-integer", str(10 ** 100)):
            self.run_cli("done", task, success=False)
        self.run_cli("unknown", success=False)
        self.run_cli("add", success=False)
        self.assertEqual(self.run_cli("list").stdout, before)
        self.run_cli("done", task_id)

    def test_database_failures_have_no_success_output(self):
        self.run_cli("add", "任务", db=Path(self.directory.name), success=False)
        self.run_cli("add", "任务", db=self.db / "missing", success=False)
        self.db.write_text("not a sqlite database", encoding="utf-8")
        self.run_cli("list", success=False)
        self.run_cli("add", "任务", success=False)


if __name__ == "__main__":
    unittest.main()
